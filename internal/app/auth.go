package app

import (
	"context"
	"crypto/pbkdf2"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"errors"
	"fmt"
	"strings"
	"sync"
	"time"

	"ordens-servico/internal/domain"
)

// Parâmetros de senha e sessão (RF-01, RN-10, RNF-03).
const (
	iteracoesHash   = 600_000 // recomendação OWASP para PBKDF2-HMAC-SHA256
	tamanhoHash     = 32
	duracaoSessao   = 8 * time.Hour
	maxFalhasLogin  = 5
	duracaoBloqueio = 15 * time.Minute
)

var (
	ErrCredenciais = errors.New("e-mail ou senha inválidos")
	ErrBloqueado   = errors.New("usuário bloqueado por excesso de tentativas; tente novamente em 15 minutos")
)

func gerarHash(senha string, salt []byte) ([]byte, error) {
	h, err := pbkdf2.Key(sha256.New, senha, salt, iteracoesHash, tamanhoHash)
	if err != nil {
		return nil, fmt.Errorf("gerar hash da senha: %w", err)
	}
	return h, nil
}

// NovoUsuario gera salt aleatório e hash da senha. A senha em texto não é guardada.
func NovoUsuario(nome, email, senha string) (domain.Usuario, error) {
	salt := make([]byte, 16)
	if _, err := rand.Read(salt); err != nil {
		return domain.Usuario{}, fmt.Errorf("gerar salt: %w", err)
	}
	h, err := gerarHash(senha, salt)
	if err != nil {
		return domain.Usuario{}, err
	}
	return domain.Usuario{Nome: nome, Email: strings.ToLower(email), SenhaHash: h, Salt: salt}, nil
}

type sessao struct {
	usuario domain.Usuario
	expira  time.Time
}

type falhas struct {
	quantidade   int
	bloqueadoAte time.Time
}

// sessoes guarda as sessões e as falhas de login em memória.
// Ao reiniciar o servidor, todos os usuários precisam entrar de novo.
type sessoes struct {
	mu       sync.Mutex
	porToken map[string]sessao
	porEmail map[string]falhas
}

func novasSessoes() *sessoes {
	return &sessoes{porToken: map[string]sessao{}, porEmail: map[string]falhas{}}
}

// Login confere a senha e devolve um token de sessão.
// Depois de 5 falhas seguidas, o e-mail fica bloqueado por 15 minutos (RN-10).
func (s *Service) Login(ctx context.Context, email, senha string) (string, error) {
	email = strings.ToLower(strings.TrimSpace(email))
	agora := s.agora()

	s.sessoes.mu.Lock()
	bloqueado := agora.Before(s.sessoes.porEmail[email].bloqueadoAte)
	s.sessoes.mu.Unlock()
	if bloqueado {
		return "", ErrBloqueado
	}

	ok, u, err := s.conferirSenha(ctx, email, senha)
	if err != nil {
		return "", err
	}

	s.sessoes.mu.Lock()
	defer s.sessoes.mu.Unlock()
	if !ok {
		f := s.sessoes.porEmail[email]
		f.quantidade++
		if f.quantidade >= maxFalhasLogin {
			f = falhas{bloqueadoAte: agora.Add(duracaoBloqueio)}
		}
		s.sessoes.porEmail[email] = f
		return "", ErrCredenciais
	}
	delete(s.sessoes.porEmail, email)
	token := rand.Text()
	s.sessoes.porToken[token] = sessao{usuario: u, expira: agora.Add(duracaoSessao)}
	return token, nil
}

func (s *Service) conferirSenha(ctx context.Context, email, senha string) (bool, domain.Usuario, error) {
	u, err := s.store.BuscarUsuarioPorEmail(ctx, email)
	if errors.Is(err, domain.ErrNaoEncontrado) {
		return false, u, nil
	}
	if err != nil {
		return false, u, err
	}
	h, err := gerarHash(senha, u.Salt)
	if err != nil {
		return false, u, err
	}
	return subtle.ConstantTimeCompare(h, u.SenhaHash) == 1, u, nil
}

// UsuarioDaSessao devolve o usuário do token. Remove o token se ele expirou.
func (s *Service) UsuarioDaSessao(token string) (domain.Usuario, bool) {
	s.sessoes.mu.Lock()
	defer s.sessoes.mu.Unlock()
	se, ok := s.sessoes.porToken[token]
	if !ok {
		return domain.Usuario{}, false
	}
	if s.agora().After(se.expira) {
		delete(s.sessoes.porToken, token)
		return domain.Usuario{}, false
	}
	return se.usuario, true
}

func (s *Service) Logout(token string) {
	s.sessoes.mu.Lock()
	defer s.sessoes.mu.Unlock()
	delete(s.sessoes.porToken, token)
}
