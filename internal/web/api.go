package web

import (
	"encoding/json"
	"errors"
	"net/http"

	"ordens-servico/internal/app"
	"ordens-servico/internal/domain"
	"ordens-servico/internal/store"
)

const tamanhoMaxCorpo = 1 << 20 // 1 MiB

func escreverJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v) // falha aqui significa conexão fechada pelo cliente
}

// lerJSON rejeita campos desconhecidos e corpo maior que 1 MiB.
func lerJSON(w http.ResponseWriter, r *http.Request, destino any) bool {
	dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, tamanhoMaxCorpo))
	dec.DisallowUnknownFields()
	if err := dec.Decode(destino); err != nil {
		escreverJSON(w, http.StatusBadRequest, map[string]string{"erro": "JSON inválido: " + err.Error()})
		return false
	}
	return true
}

// responderErro traduz os erros do domínio em códigos HTTP.
func (s *Server) responderErro(w http.ResponseWriter, r *http.Request, err error) {
	var ev domain.ErrValidacao
	switch {
	case errors.As(err, &ev):
		escreverJSON(w, http.StatusBadRequest, map[string]any{"erro": "dados inválidos", "campos": ev})
	case errors.Is(err, domain.ErrNaoEncontrado):
		escreverJSON(w, http.StatusNotFound, map[string]string{"erro": err.Error()})
	case errors.Is(err, domain.ErrCPFDuplicado), errors.Is(err, domain.ErrTransicaoInvalida):
		escreverJSON(w, http.StatusConflict, map[string]string{"erro": err.Error()})
	case errors.Is(err, app.ErrCredenciais):
		escreverJSON(w, http.StatusUnauthorized, map[string]string{"erro": err.Error()})
	case errors.Is(err, app.ErrBloqueado):
		escreverJSON(w, http.StatusLocked, map[string]string{"erro": err.Error()})
	default:
		s.log.Error("erro interno", "caminho", r.URL.Path, "erro", err)
		escreverJSON(w, http.StatusInternalServerError, map[string]string{"erro": "erro interno"})
	}
}

func (s *Server) apiLogin(w http.ResponseWriter, r *http.Request) {
	var in struct {
		Email string `json:"email"`
		Senha string `json:"senha"`
	}
	if !lerJSON(w, r, &in) {
		return
	}
	token, err := s.svc.Login(r.Context(), in.Email, in.Senha)
	if err != nil {
		s.responderErro(w, r, err)
		return
	}
	escreverJSON(w, http.StatusOK, map[string]string{"token": token})
}

func (s *Server) apiListarClientes(w http.ResponseWriter, r *http.Request) {
	clientes, err := s.svc.ListarClientes(r.Context(), r.URL.Query().Get("busca"))
	if err != nil {
		s.responderErro(w, r, err)
		return
	}
	escreverJSON(w, http.StatusOK, clientes)
}

func (s *Server) apiCriarCliente(w http.ResponseWriter, r *http.Request) {
	var in struct {
		Nome     string `json:"nome"`
		CPF      string `json:"cpf"`
		Email    string `json:"email"`
		Telefone string `json:"telefone"`
	}
	if !lerJSON(w, r, &in) {
		return
	}
	c, err := s.svc.CriarCliente(r.Context(), in.Nome, in.CPF, in.Email, in.Telefone)
	if err != nil {
		s.responderErro(w, r, err)
		return
	}
	escreverJSON(w, http.StatusCreated, c)
}

func (s *Server) apiBuscarCliente(w http.ResponseWriter, r *http.Request) {
	id, ok := idDoCaminho(r)
	if !ok {
		s.responderErro(w, r, domain.ErrNaoEncontrado)
		return
	}
	c, err := s.svc.BuscarCliente(r.Context(), id)
	if err != nil {
		s.responderErro(w, r, err)
		return
	}
	escreverJSON(w, http.StatusOK, c)
}

func (s *Server) apiListarOrdens(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	ordens, err := s.svc.ListarOrdens(r.Context(), store.FiltroOrdens{
		Status:     domain.Status(q.Get("status")),
		Prioridade: domain.Prioridade(q.Get("prioridade")),
	})
	if err != nil {
		s.responderErro(w, r, err)
		return
	}
	escreverJSON(w, http.StatusOK, ordens)
}

func (s *Server) apiAbrirOrdem(w http.ResponseWriter, r *http.Request) {
	var in struct {
		ClienteID     int64             `json:"cliente_id"`
		Descricao     string            `json:"descricao"`
		Prioridade    domain.Prioridade `json:"prioridade"`
		ValorCentavos int64             `json:"valor_centavos"`
	}
	if !lerJSON(w, r, &in) {
		return
	}
	o, err := s.svc.AbrirOrdem(r.Context(), in.ClienteID, in.Descricao, in.Prioridade, in.ValorCentavos)
	if err != nil {
		s.responderErro(w, r, err)
		return
	}
	escreverJSON(w, http.StatusCreated, o)
}

func (s *Server) apiBuscarOrdem(w http.ResponseWriter, r *http.Request) {
	id, ok := idDoCaminho(r)
	if !ok {
		s.responderErro(w, r, domain.ErrNaoEncontrado)
		return
	}
	o, err := s.svc.BuscarOrdem(r.Context(), id)
	if err != nil {
		s.responderErro(w, r, err)
		return
	}
	escreverJSON(w, http.StatusOK, o)
}

func (s *Server) apiAlterarStatus(w http.ResponseWriter, r *http.Request) {
	id, ok := idDoCaminho(r)
	if !ok {
		s.responderErro(w, r, domain.ErrNaoEncontrado)
		return
	}
	var in struct {
		Status domain.Status `json:"status"`
		Motivo string        `json:"motivo"`
	}
	if !lerJSON(w, r, &in) {
		return
	}
	o, err := s.svc.AlterarStatus(r.Context(), id, in.Status, in.Motivo)
	if err != nil {
		s.responderErro(w, r, err)
		return
	}
	escreverJSON(w, http.StatusOK, o)
}

func (s *Server) apiResumo(w http.ResponseWriter, r *http.Request) {
	res, err := s.svc.Resumo(r.Context())
	if err != nil {
		s.responderErro(w, r, err)
		return
	}
	escreverJSON(w, http.StatusOK, res)
}
