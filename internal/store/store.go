// Package store grava e lê os dados no SQLite.
package store

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"time"

	"modernc.org/sqlite"
	sqlite3 "modernc.org/sqlite/lib"

	"ordens-servico/internal/domain"
)

const esquema = `
CREATE TABLE IF NOT EXISTS usuarios (
	id         INTEGER PRIMARY KEY,
	nome       TEXT NOT NULL,
	email      TEXT NOT NULL UNIQUE,
	senha_hash BLOB NOT NULL,
	salt       BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS clientes (
	id        INTEGER PRIMARY KEY,
	nome      TEXT NOT NULL,
	cpf       TEXT NOT NULL UNIQUE,
	email     TEXT NOT NULL,
	telefone  TEXT NOT NULL DEFAULT '',
	criado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ordens (
	id                  INTEGER PRIMARY KEY,
	cliente_id          INTEGER NOT NULL REFERENCES clientes(id),
	descricao           TEXT NOT NULL,
	prioridade          TEXT NOT NULL,
	status              TEXT NOT NULL,
	valor_centavos      INTEGER NOT NULL,
	aberta_em           TEXT NOT NULL,
	prazo               TEXT NOT NULL,
	concluida_em        TEXT,
	motivo_cancelamento TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_ordens_status ON ordens(status);
`

type Store struct {
	db *sql.DB
}

// Abrir abre (ou cria) o arquivo do banco e aplica o esquema.
func Abrir(ctx context.Context, caminho string) (*Store, error) {
	db, err := sql.Open("sqlite", "file:"+caminho+"?_pragma=foreign_keys(1)&_pragma=busy_timeout(5000)")
	if err != nil {
		return nil, fmt.Errorf("abrir banco %s: %w", caminho, err)
	}
	// O SQLite aceita um escritor por vez. Uma conexão evita SQLITE_BUSY sob concorrência.
	db.SetMaxOpenConns(1)
	if _, err := db.ExecContext(ctx, esquema); err != nil {
		db.Close()
		return nil, fmt.Errorf("aplicar esquema: %w", err)
	}
	return &Store{db: db}, nil
}

func (s *Store) Close() error { return s.db.Close() }

func (s *Store) ContarUsuarios(ctx context.Context) (int, error) {
	var n int
	if err := s.db.QueryRowContext(ctx, `SELECT COUNT(*) FROM usuarios`).Scan(&n); err != nil {
		return 0, fmt.Errorf("contar usuários: %w", err)
	}
	return n, nil
}

func (s *Store) InserirUsuario(ctx context.Context, u *domain.Usuario) error {
	res, err := s.db.ExecContext(ctx,
		`INSERT INTO usuarios (nome, email, senha_hash, salt) VALUES (?, ?, ?, ?)`,
		u.Nome, u.Email, u.SenhaHash, u.Salt)
	if err != nil {
		return fmt.Errorf("inserir usuário %s: %w", u.Email, err)
	}
	u.ID, err = res.LastInsertId()
	return err
}

func (s *Store) BuscarUsuarioPorEmail(ctx context.Context, email string) (domain.Usuario, error) {
	var u domain.Usuario
	err := s.db.QueryRowContext(ctx,
		`SELECT id, nome, email, senha_hash, salt FROM usuarios WHERE email = ?`, email).
		Scan(&u.ID, &u.Nome, &u.Email, &u.SenhaHash, &u.Salt)
	if errors.Is(err, sql.ErrNoRows) {
		return u, domain.ErrNaoEncontrado
	}
	if err != nil {
		return u, fmt.Errorf("buscar usuário: %w", err)
	}
	return u, nil
}

func (s *Store) InserirCliente(ctx context.Context, c *domain.Cliente) error {
	res, err := s.db.ExecContext(ctx,
		`INSERT INTO clientes (nome, cpf, email, telefone, criado_em) VALUES (?, ?, ?, ?, ?)`,
		c.Nome, c.CPF, c.Email, c.Telefone, formatar(c.CriadoEm))
	var se *sqlite.Error
	if errors.As(err, &se) && se.Code() == sqlite3.SQLITE_CONSTRAINT_UNIQUE {
		return domain.ErrCPFDuplicado
	}
	if err != nil {
		return fmt.Errorf("inserir cliente: %w", err)
	}
	c.ID, err = res.LastInsertId()
	return err
}

const colunasCliente = `id, nome, cpf, email, telefone, criado_em`

func (s *Store) BuscarCliente(ctx context.Context, id int64) (domain.Cliente, error) {
	row := s.db.QueryRowContext(ctx, `SELECT `+colunasCliente+` FROM clientes WHERE id = ?`, id)
	c, err := lerCliente(row)
	if errors.Is(err, sql.ErrNoRows) {
		return c, domain.ErrNaoEncontrado
	}
	if err != nil {
		return c, fmt.Errorf("buscar cliente %d: %w", id, err)
	}
	return c, nil
}

// ListarClientes filtra por parte do nome ou do CPF. Devolve no máximo 200 registros.
func (s *Store) ListarClientes(ctx context.Context, busca string) ([]domain.Cliente, error) {
	termo := strings.TrimSpace(busca)
	termoCPF := termo
	if d := domain.SomenteDigitos(termo); d != "" && strings.Trim(termo, "0123456789.-") == "" {
		termoCPF = d // CPF com máscara: o banco guarda só os dígitos (DEF-01)
	}
	rows, err := s.db.QueryContext(ctx,
		`SELECT `+colunasCliente+` FROM clientes WHERE nome LIKE ? OR cpf LIKE ? ORDER BY nome LIMIT 200`,
		"%"+termo+"%", "%"+termoCPF+"%")
	if err != nil {
		return nil, fmt.Errorf("listar clientes: %w", err)
	}
	defer rows.Close()

	clientes := []domain.Cliente{}
	for rows.Next() {
		c, err := lerCliente(rows)
		if err != nil {
			return nil, fmt.Errorf("ler cliente: %w", err)
		}
		clientes = append(clientes, c)
	}
	return clientes, rows.Err()
}

func (s *Store) InserirOrdem(ctx context.Context, o *domain.Ordem) error {
	res, err := s.db.ExecContext(ctx,
		`INSERT INTO ordens (cliente_id, descricao, prioridade, status, valor_centavos, aberta_em, prazo)
		 VALUES (?, ?, ?, ?, ?, ?, ?)`,
		o.ClienteID, o.Descricao, o.Prioridade, o.Status, o.ValorCentavos, formatar(o.AbertaEm), formatar(o.Prazo))
	if err != nil {
		return fmt.Errorf("inserir ordem: %w", err)
	}
	o.ID, err = res.LastInsertId()
	return err
}

// AtualizarStatus grava o novo status somente se o status no banco ainda for statusAnterior.
// Se outra requisição mudou a ordem antes, devolve domain.ErrTransicaoInvalida.
func (s *Store) AtualizarStatus(ctx context.Context, o domain.Ordem, statusAnterior domain.Status) error {
	var concluidaEm any
	if o.ConcluidaEm != nil {
		concluidaEm = formatar(*o.ConcluidaEm)
	}
	res, err := s.db.ExecContext(ctx,
		`UPDATE ordens SET status = ?, concluida_em = ?, motivo_cancelamento = ? WHERE id = ? AND status = ?`,
		o.Status, concluidaEm, o.MotivoCancelamento, o.ID, statusAnterior)
	if err != nil {
		return fmt.Errorf("atualizar ordem %d: %w", o.ID, err)
	}
	n, err := res.RowsAffected()
	if err != nil {
		return fmt.Errorf("atualizar ordem %d: %w", o.ID, err)
	}
	if n == 0 {
		return fmt.Errorf("%w: a ordem %d mudou de status durante a operação", domain.ErrTransicaoInvalida, o.ID)
	}
	return nil
}

const colunasOrdem = `id, cliente_id, descricao, prioridade, status, valor_centavos, aberta_em, prazo, concluida_em, motivo_cancelamento`

func (s *Store) BuscarOrdem(ctx context.Context, id int64) (domain.Ordem, error) {
	row := s.db.QueryRowContext(ctx, `SELECT `+colunasOrdem+` FROM ordens WHERE id = ?`, id)
	o, err := lerOrdem(row)
	if errors.Is(err, sql.ErrNoRows) {
		return o, domain.ErrNaoEncontrado
	}
	if err != nil {
		return o, fmt.Errorf("buscar ordem %d: %w", id, err)
	}
	return o, nil
}

// FiltroOrdens: campo vazio significa "sem filtro".
type FiltroOrdens struct {
	Status     domain.Status
	Prioridade domain.Prioridade
}

func (s *Store) ListarOrdens(ctx context.Context, f FiltroOrdens) ([]domain.Ordem, error) {
	rows, err := s.db.QueryContext(ctx,
		`SELECT `+colunasOrdem+` FROM ordens
		 WHERE (? = '' OR status = ?) AND (? = '' OR prioridade = ?)
		 ORDER BY prazo`,
		f.Status, f.Status, f.Prioridade, f.Prioridade)
	if err != nil {
		return nil, fmt.Errorf("listar ordens: %w", err)
	}
	defer rows.Close()

	ordens := []domain.Ordem{}
	for rows.Next() {
		o, err := lerOrdem(rows)
		if err != nil {
			return nil, fmt.Errorf("ler ordem: %w", err)
		}
		ordens = append(ordens, o)
	}
	return ordens, rows.Err()
}

type scanner interface{ Scan(dest ...any) error }

func lerCliente(r scanner) (domain.Cliente, error) {
	var c domain.Cliente
	var criadoEm string
	if err := r.Scan(&c.ID, &c.Nome, &c.CPF, &c.Email, &c.Telefone, &criadoEm); err != nil {
		return c, err
	}
	var err error
	c.CriadoEm, err = interpretar(criadoEm)
	return c, err
}

func lerOrdem(r scanner) (domain.Ordem, error) {
	var o domain.Ordem
	var abertaEm, prazo string
	var concluidaEm sql.NullString
	err := r.Scan(&o.ID, &o.ClienteID, &o.Descricao, &o.Prioridade, &o.Status, &o.ValorCentavos,
		&abertaEm, &prazo, &concluidaEm, &o.MotivoCancelamento)
	if err != nil {
		return o, err
	}
	if o.AbertaEm, err = interpretar(abertaEm); err != nil {
		return o, err
	}
	if o.Prazo, err = interpretar(prazo); err != nil {
		return o, err
	}
	if concluidaEm.Valid {
		t, err := interpretar(concluidaEm.String)
		if err != nil {
			return o, err
		}
		o.ConcluidaEm = &t
	}
	return o, nil
}

// As datas são gravadas como texto RFC 3339 em UTC com largura fixa.
// Assim a ordem do texto é igual à ordem cronológica (ORDER BY prazo).
const formatoData = "2006-01-02T15:04:05.000000000Z07:00"

func formatar(t time.Time) string { return t.UTC().Format(formatoData) }

func interpretar(s string) (time.Time, error) {
	t, err := time.Parse(time.RFC3339Nano, s)
	if err != nil {
		return t, fmt.Errorf("data inválida no banco %q: %w", s, err)
	}
	return t, nil
}
