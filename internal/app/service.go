// Package app contém os casos de uso. A API JSON e a interface HTML usam o mesmo Service.
package app

import (
	"context"
	"errors"
	"fmt"
	"time"

	"ordens-servico/internal/domain"
	"ordens-servico/internal/store"
)

type Service struct {
	store   *store.Store
	agora   func() time.Time
	sessoes *sessoes
}

// NovoService recebe o relógio como função para os testes controlarem o tempo.
func NovoService(st *store.Store, agora func() time.Time) *Service {
	return &Service{store: st, agora: agora, sessoes: novasSessoes()}
}

func (s *Service) CriarCliente(ctx context.Context, nome, cpf, email, telefone string) (domain.Cliente, error) {
	c, err := domain.NovoCliente(nome, cpf, email, telefone, s.agora())
	if err != nil {
		return c, err
	}
	if err := s.store.InserirCliente(ctx, &c); err != nil {
		return c, err
	}
	return c, nil
}

func (s *Service) BuscarCliente(ctx context.Context, id int64) (domain.Cliente, error) {
	return s.store.BuscarCliente(ctx, id)
}

func (s *Service) ListarClientes(ctx context.Context, busca string) ([]domain.Cliente, error) {
	return s.store.ListarClientes(ctx, busca)
}

// AbrirOrdem valida os dados e confere se o cliente existe (RN-11).
func (s *Service) AbrirOrdem(ctx context.Context, clienteID int64, descricao string, p domain.Prioridade, valorCentavos int64) (domain.Ordem, error) {
	o, err := domain.NovaOrdem(clienteID, descricao, p, valorCentavos, s.agora())
	if err != nil {
		return o, err
	}
	if _, err := s.store.BuscarCliente(ctx, clienteID); errors.Is(err, domain.ErrNaoEncontrado) {
		return o, domain.ErrValidacao{"cliente_id": "cliente não encontrado"}
	} else if err != nil {
		return o, err
	}
	if err := s.store.InserirOrdem(ctx, &o); err != nil {
		return o, err
	}
	return o, nil
}

func (s *Service) BuscarOrdem(ctx context.Context, id int64) (domain.Ordem, error) {
	o, err := s.store.BuscarOrdem(ctx, id)
	o.Atrasada = o.EstaAtrasada(s.agora())
	return o, err
}

func (s *Service) ListarOrdens(ctx context.Context, f store.FiltroOrdens) ([]domain.Ordem, error) {
	if f.Status != "" && !f.Status.Valido() {
		return nil, domain.ErrValidacao{"status": "status desconhecido"}
	}
	if f.Prioridade != "" && !f.Prioridade.Valida() {
		return nil, domain.ErrValidacao{"prioridade": "prioridade desconhecida"}
	}
	ordens, err := s.store.ListarOrdens(ctx, f)
	agora := s.agora()
	for i := range ordens {
		ordens[i].Atrasada = ordens[i].EstaAtrasada(agora)
	}
	return ordens, err
}

func (s *Service) AlterarStatus(ctx context.Context, id int64, novo domain.Status, motivo string) (domain.Ordem, error) {
	o, err := s.store.BuscarOrdem(ctx, id)
	if err != nil {
		return o, err
	}
	anterior := o.Status
	agora := s.agora()
	if err := o.AlterarStatus(novo, motivo, agora); err != nil {
		return o, err
	}
	if err := s.store.AtualizarStatus(ctx, o, anterior); err != nil {
		return o, err
	}
	o.Atrasada = o.EstaAtrasada(agora)
	return o, nil
}

type Resumo struct {
	Total     int                   `json:"total"`
	PorStatus map[domain.Status]int `json:"por_status"`
	Atrasadas int                   `json:"atrasadas"`
}

// Resumo alimenta o painel (RF-07).
func (s *Service) Resumo(ctx context.Context) (Resumo, error) {
	ordens, err := s.ListarOrdens(ctx, store.FiltroOrdens{})
	if err != nil {
		return Resumo{}, err
	}
	r := Resumo{Total: len(ordens), PorStatus: map[domain.Status]int{}}
	for _, st := range domain.TodosStatus {
		r.PorStatus[st] = 0
	}
	for _, o := range ordens {
		r.PorStatus[o.Status]++
		if o.Atrasada {
			r.Atrasadas++
		}
	}
	return r, nil
}

// Semear cria usuários e dados fictícios quando o banco está vazio.
func (s *Service) Semear(ctx context.Context) error {
	n, err := s.store.ContarUsuarios(ctx)
	if err != nil {
		return err
	}
	if n > 0 {
		return nil
	}

	usuarios := []struct{ nome, email, senha string }{
		{"Administrador", "admin@teste.local", "Admin@123"},
		{"Técnico de Campo", "tecnico@teste.local", "Tecnico@123"},
	}
	for _, d := range usuarios {
		u, err := NovoUsuario(d.nome, d.email, d.senha)
		if err != nil {
			return err
		}
		if err := s.store.InserirUsuario(ctx, &u); err != nil {
			return err
		}
	}

	clientes := [][4]string{
		{"Condomínio Jardim das Flores", "123.456.789-09", "portaria@jardim.teste.local", "(14) 3333-1000"},
		{"Mercado Bom Preço", "111.444.777-35", "gerencia@bompreco.teste.local", ""},
		{"Clínica Vida Plena", "390.533.447-05", "adm@vidaplena.teste.local", "(14) 99888-2000"},
	}
	for i, d := range clientes {
		c, err := s.CriarCliente(ctx, d[0], d[1], d[2], d[3])
		if err != nil {
			return fmt.Errorf("semear cliente %d: %w", i, err)
		}
		descricoes := []struct {
			texto string
			p     domain.Prioridade
			valor int64
		}{
			{"Sensor da porta dos fundos não comunica com a central", domain.PrioridadeAlta, 18000},
			{"Revisão preventiva das câmeras do estacionamento", domain.PrioridadeBaixa, 45000},
		}
		for _, o := range descricoes {
			if _, err := s.AbrirOrdem(ctx, c.ID, o.texto, o.p, o.valor); err != nil {
				return fmt.Errorf("semear ordem: %w", err)
			}
		}
	}
	return nil
}
