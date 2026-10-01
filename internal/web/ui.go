package web

import (
	"errors"
	"net/http"
	"strconv"
	"strings"

	"ordens-servico/internal/app"
	"ordens-servico/internal/domain"
	"ordens-servico/internal/store"
)

func (s *Server) renderizar(w http.ResponseWriter, r *http.Request, status int, pagina string, dados map[string]any) {
	dados["Usuario"] = usuarioDe(r.Context())
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.WriteHeader(status)
	if err := s.paginas[pagina].Execute(w, dados); err != nil {
		s.log.Error("renderizar página", "pagina", pagina, "erro", err)
	}
}

// errosDeFormulario separa erros de validação (mostrados no formulário) de erros inesperados.
func errosDeFormulario(err error) (domain.ErrValidacao, int, bool) {
	var ev domain.ErrValidacao
	switch {
	case errors.As(err, &ev):
		return ev, http.StatusBadRequest, true
	case errors.Is(err, domain.ErrCPFDuplicado):
		return domain.ErrValidacao{"cpf": "CPF já cadastrado"}, http.StatusConflict, true
	}
	return nil, 0, false
}

func (s *Server) erroInterno(w http.ResponseWriter, r *http.Request, err error) {
	s.log.Error("erro interno", "caminho", r.URL.Path, "erro", err)
	http.Error(w, "erro interno", http.StatusInternalServerError)
}

func (s *Server) uiLoginForm(w http.ResponseWriter, r *http.Request) {
	s.renderizar(w, r, http.StatusOK, "login", map[string]any{})
}

func (s *Server) uiLogin(w http.ResponseWriter, r *http.Request) {
	email := r.FormValue("email")
	token, err := s.svc.Login(r.Context(), email, r.FormValue("senha"))
	switch {
	case errors.Is(err, app.ErrCredenciais):
		s.renderizar(w, r, http.StatusUnauthorized, "login", map[string]any{"Erro": err.Error(), "Email": email})
		return
	case errors.Is(err, app.ErrBloqueado):
		s.renderizar(w, r, http.StatusLocked, "login", map[string]any{"Erro": err.Error(), "Email": email})
		return
	case err != nil:
		s.erroInterno(w, r, err)
		return
	}
	http.SetCookie(w, &http.Cookie{
		Name: nomeCookie, Value: token, Path: "/",
		HttpOnly: true, SameSite: http.SameSiteLaxMode, MaxAge: 8 * 60 * 60,
	})
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func (s *Server) uiLogout(w http.ResponseWriter, r *http.Request) {
	if c, err := r.Cookie(nomeCookie); err == nil {
		s.svc.Logout(c.Value)
	}
	http.SetCookie(w, &http.Cookie{Name: nomeCookie, Value: "", Path: "/", MaxAge: -1})
	http.Redirect(w, r, "/login", http.StatusSeeOther)
}

func (s *Server) uiPainel(w http.ResponseWriter, r *http.Request) {
	resumo, err := s.svc.Resumo(r.Context())
	if err != nil {
		s.erroInterno(w, r, err)
		return
	}
	ordens, err := s.svc.ListarOrdens(r.Context(), store.FiltroOrdens{})
	if err != nil {
		s.erroInterno(w, r, err)
		return
	}
	var atrasadas []domain.Ordem
	for _, o := range ordens {
		if o.Atrasada {
			atrasadas = append(atrasadas, o)
		}
	}
	s.renderizar(w, r, http.StatusOK, "painel", map[string]any{
		"Resumo": resumo, "Status": domain.TodosStatus, "Atrasadas": atrasadas,
	})
}

func (s *Server) uiClientes(w http.ResponseWriter, r *http.Request) {
	busca := r.URL.Query().Get("busca")
	clientes, err := s.svc.ListarClientes(r.Context(), busca)
	if err != nil {
		s.erroInterno(w, r, err)
		return
	}
	dados := map[string]any{"Clientes": clientes, "Busca": busca}
	if r.URL.Query().Has("criado") {
		dados["Mensagem"] = "Cliente cadastrado com sucesso."
	}
	s.renderizar(w, r, http.StatusOK, "clientes", dados)
}

func (s *Server) uiClienteForm(w http.ResponseWriter, r *http.Request) {
	s.renderizar(w, r, http.StatusOK, "cliente_form", map[string]any{"Form": map[string]string{}})
}

func (s *Server) uiCriarCliente(w http.ResponseWriter, r *http.Request) {
	form := map[string]string{
		"nome": r.FormValue("nome"), "cpf": r.FormValue("cpf"),
		"email": r.FormValue("email"), "telefone": r.FormValue("telefone"),
	}
	_, err := s.svc.CriarCliente(r.Context(), form["nome"], form["cpf"], form["email"], form["telefone"])
	if err != nil {
		ev, status, ok := errosDeFormulario(err)
		if !ok {
			s.erroInterno(w, r, err)
			return
		}
		s.renderizar(w, r, status, "cliente_form", map[string]any{"Form": form, "Erros": ev})
		return
	}
	http.Redirect(w, r, "/clientes?criado=1", http.StatusSeeOther)
}

// nomesDosClientes monta o mapa id -> nome para as telas de ordens.
func (s *Server) nomesDosClientes(r *http.Request) ([]domain.Cliente, map[int64]string, error) {
	clientes, err := s.svc.ListarClientes(r.Context(), "")
	if err != nil {
		return nil, nil, err
	}
	nomes := make(map[int64]string, len(clientes))
	for _, c := range clientes {
		nomes[c.ID] = c.Nome
	}
	return clientes, nomes, nil
}

func (s *Server) uiOrdens(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	filtro := store.FiltroOrdens{Status: domain.Status(q.Get("status")), Prioridade: domain.Prioridade(q.Get("prioridade"))}
	dados := map[string]any{
		"Filtro": filtro, "Status": domain.TodosStatus,
		"Prioridades": []domain.Prioridade{domain.PrioridadeBaixa, domain.PrioridadeMedia, domain.PrioridadeAlta, domain.PrioridadeCritica},
	}
	if q.Has("criada") {
		dados["Mensagem"] = "Ordem de serviço aberta com sucesso."
	}

	ordens, err := s.svc.ListarOrdens(r.Context(), filtro)
	if ev, _, ok := errosDeFormulario(err); ok {
		dados["Erros"] = ev
		s.renderizar(w, r, http.StatusBadRequest, "ordens", dados)
		return
	} else if err != nil {
		s.erroInterno(w, r, err)
		return
	}
	_, nomes, err := s.nomesDosClientes(r)
	if err != nil {
		s.erroInterno(w, r, err)
		return
	}
	dados["Ordens"], dados["Nomes"] = ordens, nomes
	s.renderizar(w, r, http.StatusOK, "ordens", dados)
}

func (s *Server) dadosFormOrdem(r *http.Request, form map[string]string) (map[string]any, error) {
	clientes, _, err := s.nomesDosClientes(r)
	if err != nil {
		return nil, err
	}
	return map[string]any{
		"Form": form, "Clientes": clientes,
		"Prioridades": []domain.Prioridade{domain.PrioridadeBaixa, domain.PrioridadeMedia, domain.PrioridadeAlta, domain.PrioridadeCritica},
	}, nil
}

func (s *Server) uiOrdemForm(w http.ResponseWriter, r *http.Request) {
	dados, err := s.dadosFormOrdem(r, map[string]string{"cliente_id": r.URL.Query().Get("cliente_id")})
	if err != nil {
		s.erroInterno(w, r, err)
		return
	}
	s.renderizar(w, r, http.StatusOK, "ordem_form", dados)
}

func (s *Server) uiAbrirOrdem(w http.ResponseWriter, r *http.Request) {
	form := map[string]string{
		"cliente_id": r.FormValue("cliente_id"), "descricao": r.FormValue("descricao"),
		"prioridade": r.FormValue("prioridade"), "valor": r.FormValue("valor"),
	}
	clienteID, _ := strconv.ParseInt(form["cliente_id"], 10, 64) // texto inválido vira 0 e cai na RN de cliente obrigatório
	valor, errValor := domain.ParseValor(form["valor"])

	var err error
	if errValor == nil { // valor inválido não grava a OS (DEF-02)
		_, err = s.svc.AbrirOrdem(r.Context(), clienteID, form["descricao"], domain.Prioridade(form["prioridade"]), valor)
	}
	if err == nil && errValor == nil {
		http.Redirect(w, r, "/ordens?criada=1", http.StatusSeeOther)
		return
	}

	ev := domain.ErrValidacao{}
	if err != nil {
		var e domain.ErrValidacao
		if !errors.As(err, &e) {
			s.erroInterno(w, r, err)
			return
		}
		ev = e
	}
	if errValor != nil {
		ev["valor"] = errValor.(domain.ErrValidacao)["valor"]
	}
	dados, err := s.dadosFormOrdem(r, form)
	if err != nil {
		s.erroInterno(w, r, err)
		return
	}
	dados["Erros"] = ev
	s.renderizar(w, r, http.StatusBadRequest, "ordem_form", dados)
}

func (s *Server) dadosDetalhe(r *http.Request, o domain.Ordem) (map[string]any, error) {
	c, err := s.svc.BuscarCliente(r.Context(), o.ClienteID)
	if err != nil {
		return nil, err
	}
	var acoes []domain.Status
	for _, st := range domain.TodosStatus {
		if domain.PodeTransitar(o.Status, st) {
			acoes = append(acoes, st)
		}
	}
	return map[string]any{"Ordem": o, "Cliente": c, "Acoes": acoes}, nil
}

func (s *Server) uiOrdemDetalhe(w http.ResponseWriter, r *http.Request) {
	id, ok := idDoCaminho(r)
	if !ok {
		http.NotFound(w, r)
		return
	}
	o, err := s.svc.BuscarOrdem(r.Context(), id)
	if errors.Is(err, domain.ErrNaoEncontrado) {
		http.NotFound(w, r)
		return
	} else if err != nil {
		s.erroInterno(w, r, err)
		return
	}
	dados, err := s.dadosDetalhe(r, o)
	if err != nil {
		s.erroInterno(w, r, err)
		return
	}
	if r.URL.Query().Has("alterada") {
		dados["Mensagem"] = "Status alterado para " + string(o.Status) + "."
	}
	s.renderizar(w, r, http.StatusOK, "ordem_detalhe", dados)
}

func (s *Server) uiAlterarStatus(w http.ResponseWriter, r *http.Request) {
	id, ok := idDoCaminho(r)
	if !ok {
		http.NotFound(w, r)
		return
	}
	_, err := s.svc.AlterarStatus(r.Context(), id, domain.Status(r.FormValue("status")), r.FormValue("motivo"))
	if err == nil {
		http.Redirect(w, r, "/ordens/"+strconv.FormatInt(id, 10)+"?alterada=1", http.StatusSeeOther)
		return
	}
	if errors.Is(err, domain.ErrNaoEncontrado) {
		http.NotFound(w, r)
		return
	}

	status := http.StatusBadRequest
	var mensagens []string
	var ev domain.ErrValidacao
	switch {
	case errors.As(err, &ev):
		for _, m := range ev {
			mensagens = append(mensagens, m)
		}
	case errors.Is(err, domain.ErrTransicaoInvalida):
		status = http.StatusConflict
		mensagens = append(mensagens, err.Error())
	default:
		s.erroInterno(w, r, err)
		return
	}

	o, errBusca := s.svc.BuscarOrdem(r.Context(), id)
	if errBusca != nil {
		s.erroInterno(w, r, errBusca)
		return
	}
	dados, errDados := s.dadosDetalhe(r, o)
	if errDados != nil {
		s.erroInterno(w, r, errDados)
		return
	}
	dados["Erro"] = strings.Join(mensagens, " ")
	s.renderizar(w, r, status, "ordem_detalhe", dados)
}
