package web_test

// Testes de integração: HTTP -> web -> app -> store -> SQLite real (arquivo temporário).
// Cada teste cria um banco novo, então os testes não dependem uns dos outros.

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"net/url"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"ordens-servico/internal/app"
	"ordens-servico/internal/store"
	"ordens-servico/internal/web"
)

type relogio struct {
	mu sync.Mutex
	t  time.Time
}

func (r *relogio) agora() time.Time {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.t
}

func (r *relogio) avancar(d time.Duration) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.t = r.t.Add(d)
}

type ambiente struct {
	url     string
	relogio *relogio
}

func novoAmbiente(t *testing.T) *ambiente {
	t.Helper()
	ctx := context.Background()
	st, err := store.Abrir(ctx, filepath.Join(t.TempDir(), "teste.db"))
	if err != nil {
		t.Fatalf("abrir banco: %v", err)
	}
	t.Cleanup(func() { st.Close() })

	rel := &relogio{t: time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC)}
	svc := app.NovoService(st, rel.agora)
	if err := svc.Semear(ctx); err != nil {
		t.Fatalf("semear: %v", err)
	}
	srv := httptest.NewServer(web.NovoServer(svc, slog.New(slog.DiscardHandler)).Handler())
	t.Cleanup(srv.Close)
	return &ambiente{url: srv.URL, relogio: rel}
}

// chamar envia JSON e devolve o status e o corpo decodificado.
func (a *ambiente) chamar(t *testing.T, metodo, caminho, token string, corpo any) (int, map[string]any) {
	t.Helper()
	var leitor io.Reader
	if corpo != nil {
		b, err := json.Marshal(corpo)
		if err != nil {
			t.Fatalf("codificar corpo: %v", err)
		}
		leitor = bytes.NewReader(b)
	}
	req, err := http.NewRequest(metodo, a.url+caminho, leitor)
	if err != nil {
		t.Fatalf("montar requisição: %v", err)
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("%s %s: %v", metodo, caminho, err)
	}
	defer resp.Body.Close()

	var saida map[string]any
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("ler resposta: %v", err)
	}
	if len(b) > 0 && b[0] == '{' {
		if err := json.Unmarshal(b, &saida); err != nil {
			t.Fatalf("decodificar resposta %s: %v", b, err)
		}
	}
	return resp.StatusCode, saida
}

func (a *ambiente) login(t *testing.T) string {
	t.Helper()
	status, corpo := a.chamar(t, "POST", "/api/login", "", map[string]string{"email": "admin@teste.local", "senha": "Admin@123"})
	if status != http.StatusOK {
		t.Fatalf("login: status %d, corpo %v", status, corpo)
	}
	return corpo["token"].(string)
}

func (a *ambiente) criarCliente(t *testing.T, token, cpf string) float64 {
	t.Helper()
	status, corpo := a.chamar(t, "POST", "/api/clientes", token, map[string]string{
		"nome": "Cliente de Teste", "cpf": cpf, "email": "cliente@teste.local",
	})
	if status != http.StatusCreated {
		t.Fatalf("criar cliente: status %d, corpo %v", status, corpo)
	}
	return corpo["id"].(float64)
}

func (a *ambiente) abrirOrdem(t *testing.T, token string, clienteID float64, prioridade string) float64 {
	t.Helper()
	status, corpo := a.chamar(t, "POST", "/api/ordens", token, map[string]any{
		"cliente_id": clienteID, "descricao": "Troca da bateria da central", "prioridade": prioridade, "valor_centavos": 25000,
	})
	if status != http.StatusCreated {
		t.Fatalf("abrir ordem: status %d, corpo %v", status, corpo)
	}
	return corpo["id"].(float64)
}

// O JSON decodifica números como float64. Os IDs são inteiros, então 'f' com -1 não mostra casas decimais.
func texto(id float64) string { return strconv.FormatFloat(id, 'f', -1, 64) }

func caminhoOrdem(id float64, sufixo string) string { return "/api/ordens/" + texto(id) + sufixo }

// IT-01 | RF-01 | Login válido devolve token; senha errada devolve 401.
func TestLogin(t *testing.T) {
	a := novoAmbiente(t)
	if a.login(t) == "" {
		t.Fatal("token vazio")
	}
	status, _ := a.chamar(t, "POST", "/api/login", "", map[string]string{"email": "admin@teste.local", "senha": "errada"})
	if status != http.StatusUnauthorized {
		t.Errorf("senha errada: status %d, quer 401", status)
	}
}

// IT-02 | RF-01, RN-10 | Cinco falhas bloqueiam o login por 15 minutos, mesmo com a senha certa.
func TestLogin_BloqueioAposCincoFalhas(t *testing.T) {
	a := novoAmbiente(t)
	senhaErrada := map[string]string{"email": "tecnico@teste.local", "senha": "errada"}
	senhaCerta := map[string]string{"email": "tecnico@teste.local", "senha": "Tecnico@123"}

	for i := 1; i <= 5; i++ {
		if status, _ := a.chamar(t, "POST", "/api/login", "", senhaErrada); status != http.StatusUnauthorized {
			t.Fatalf("falha %d: status %d, quer 401", i, status)
		}
	}
	if status, _ := a.chamar(t, "POST", "/api/login", "", senhaCerta); status != http.StatusLocked {
		t.Fatalf("depois de 5 falhas: status %d, quer 423", status)
	}

	a.relogio.avancar(15*time.Minute + time.Second)
	if status, _ := a.chamar(t, "POST", "/api/login", "", senhaCerta); status != http.StatusOK {
		t.Fatalf("depois do bloqueio: status %d, quer 200", status)
	}
}

// IT-03 | RNF-03 | Endpoints protegidos rejeitam requisição sem token ou com token inválido.
func TestAPI_ExigeToken(t *testing.T) {
	a := novoAmbiente(t)
	for _, token := range []string{"", "token-inventado"} {
		if status, _ := a.chamar(t, "GET", "/api/clientes", token, nil); status != http.StatusUnauthorized {
			t.Errorf("token %q: status %d, quer 401", token, status)
		}
	}
}

// IT-04 | RF-02, RF-03, RN-02 | Cliente criado é gravado; o mesmo CPF com máscara é recusado.
func TestCliente_CriarBuscarEDuplicado(t *testing.T) {
	a := novoAmbiente(t)
	token := a.login(t)
	id := a.criarCliente(t, token, "52998224725")

	status, corpo := a.chamar(t, "GET", "/api/clientes/"+texto(id), token, nil)
	if status != http.StatusOK || corpo["cpf"] != "52998224725" {
		t.Fatalf("buscar cliente: status %d, corpo %v", status, corpo)
	}

	status, _ = a.chamar(t, "POST", "/api/clientes", token, map[string]string{
		"nome": "Outro Nome", "cpf": "529.982.247-25", "email": "outro@teste.local",
	})
	if status != http.StatusConflict {
		t.Errorf("CPF duplicado: status %d, quer 409", status)
	}
}

// IT-05 | RF-04, RN-11 | Ordem para cliente inexistente é recusada com erro no campo cliente_id.
func TestOrdem_ClienteInexistente(t *testing.T) {
	a := novoAmbiente(t)
	token := a.login(t)
	status, corpo := a.chamar(t, "POST", "/api/ordens", token, map[string]any{
		"cliente_id": 9999, "descricao": "Troca da bateria da central", "prioridade": "ALTA",
	})
	campos, _ := corpo["campos"].(map[string]any)
	if status != http.StatusBadRequest || campos["cliente_id"] == nil {
		t.Errorf("status %d, corpo %v; quer 400 com erro em cliente_id", status, corpo)
	}
}

// IT-06 | RF-05, RN-08 | Ciclo de vida completo gravado no banco; ordem concluída não pode ser cancelada.
func TestOrdem_CicloDeVida(t *testing.T) {
	a := novoAmbiente(t)
	token := a.login(t)
	id := a.abrirOrdem(t, token, a.criarCliente(t, token, "52998224725"), "MEDIA")

	for _, st := range []string{"EM_ANDAMENTO", "CONCLUIDA"} {
		if status, corpo := a.chamar(t, "PATCH", caminhoOrdem(id, "/status"), token, map[string]string{"status": st}); status != http.StatusOK {
			t.Fatalf("mudar para %s: status %d, corpo %v", st, status, corpo)
		}
	}
	_, corpo := a.chamar(t, "GET", caminhoOrdem(id, ""), token, nil)
	if corpo["status"] != "CONCLUIDA" || corpo["concluida_em"] == nil {
		t.Errorf("ordem gravada = %v; quer CONCLUIDA com concluida_em", corpo)
	}

	status, _ := a.chamar(t, "PATCH", caminhoOrdem(id, "/status"), token, map[string]string{"status": "CANCELADA", "motivo": "Cliente desistiu do serviço"})
	if status != http.StatusConflict {
		t.Errorf("cancelar concluída: status %d, quer 409", status)
	}
}

// IT-07 | RF-07, RN-09 | O painel conta a ordem CRITICA como atrasada 4 h e 1 s depois da abertura.
func TestResumo_ContaAtrasadas(t *testing.T) {
	a := novoAmbiente(t)
	token := a.login(t)
	id := a.abrirOrdem(t, token, a.criarCliente(t, token, "52998224725"), "CRITICA")

	_, antes := a.chamar(t, "GET", "/api/resumo", token, nil)
	a.relogio.avancar(4*time.Hour + time.Second)
	_, depois := a.chamar(t, "GET", "/api/resumo", token, nil)

	if antes["atrasadas"] != float64(0) || depois["atrasadas"] != float64(1) {
		t.Errorf("atrasadas antes = %v, depois = %v; quer 0 e 1", antes["atrasadas"], depois["atrasadas"])
	}
	if _, o := a.chamar(t, "GET", caminhoOrdem(id, ""), token, nil); o["atrasada"] != true {
		t.Errorf("ordem %v deveria estar atrasada", o)
	}
}

// IT-08 | RF-06 | Filtro por status devolve só ordens daquele status; status desconhecido devolve 400.
func TestOrdens_Filtro(t *testing.T) {
	a := novoAmbiente(t)
	token := a.login(t)
	id := a.abrirOrdem(t, token, a.criarCliente(t, token, "52998224725"), "BAIXA")
	a.chamar(t, "PATCH", caminhoOrdem(id, "/status"), token, map[string]string{"status": "EM_ANDAMENTO"})

	req, _ := http.NewRequest("GET", a.url+"/api/ordens?status=EM_ANDAMENTO", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	var ordens []map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&ordens); err != nil {
		t.Fatal(err)
	}
	if len(ordens) != 1 || ordens[0]["status"] != "EM_ANDAMENTO" {
		t.Errorf("filtro devolveu %v; quer 1 ordem EM_ANDAMENTO", ordens)
	}

	if status, _ := a.chamar(t, "GET", "/api/ordens?status=PAUSADA", token, nil); status != http.StatusBadRequest {
		t.Errorf("status desconhecido: %d, quer 400", status)
	}
}

// IT-09 | RNF-03 | JSON com campo desconhecido é recusado.
func TestAPI_RecusaCampoDesconhecido(t *testing.T) {
	a := novoAmbiente(t)
	status, _ := a.chamar(t, "POST", "/api/login", "", map[string]string{"email": "admin@teste.local", "senha": "Admin@123", "admin": "true"})
	if status != http.StatusBadRequest {
		t.Errorf("status %d, quer 400", status)
	}
}

// IT-10 | RF-01, RF-02, RNF-03 | Interface: sem sessão redireciona; cookie é HttpOnly; formulário mostra erro de CPF.
func TestUI_SessaoEFormulario(t *testing.T) {
	a := novoAmbiente(t)
	cliente := &http.Client{CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}

	resp, err := cliente.Get(a.url + "/clientes")
	if err != nil {
		t.Fatal(err)
	}
	resp.Body.Close()
	if resp.StatusCode != http.StatusSeeOther || resp.Header.Get("Location") != "/login" {
		t.Fatalf("sem sessão: status %d, Location %q", resp.StatusCode, resp.Header.Get("Location"))
	}

	resp, err = cliente.PostForm(a.url+"/login", url.Values{"email": {"admin@teste.local"}, "senha": {"Admin@123"}})
	if err != nil {
		t.Fatal(err)
	}
	resp.Body.Close()
	var sessao *http.Cookie
	for _, c := range resp.Cookies() {
		if c.Name == "sessao" {
			sessao = c
		}
	}
	if sessao == nil || !sessao.HttpOnly {
		t.Fatalf("cookie de sessão ausente ou sem HttpOnly: %+v", sessao)
	}

	req, _ := http.NewRequest("POST", a.url+"/clientes", strings.NewReader(url.Values{
		"nome": {"Ana Souza"}, "cpf": {"111.111.111-11"}, "email": {"ana@teste.local"},
	}.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.AddCookie(sessao)
	resp, err = cliente.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	corpo, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusBadRequest || !strings.Contains(string(corpo), `id="erro-cpf"`) {
		t.Errorf("CPF inválido no formulário: status %d; quer 400 com erro-cpf", resp.StatusCode)
	}
}

// IT-11 | RF-04 | DEF-02: valor em formato inválido no formulário mostra o erro e não grava a OS.
func TestUI_ValorInvalidoNaoGravaOrdem(t *testing.T) {
	a := novoAmbiente(t)
	token := a.login(t)
	clienteID := a.criarCliente(t, token, "52998224725")
	cliente := &http.Client{CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}

	resp, err := cliente.PostForm(a.url+"/login", url.Values{"email": {"admin@teste.local"}, "senha": {"Admin@123"}})
	if err != nil {
		t.Fatal(err)
	}
	resp.Body.Close()
	var sessao *http.Cookie
	for _, c := range resp.Cookies() {
		if c.Name == "sessao" {
			sessao = c
		}
	}
	if sessao == nil {
		t.Fatal("cookie de sessão ausente")
	}

	contarOrdens := func() int {
		t.Helper()
		req, _ := http.NewRequest("GET", a.url+"/api/ordens", nil)
		req.Header.Set("Authorization", "Bearer "+token)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			t.Fatal(err)
		}
		defer resp.Body.Close()
		var ordens []map[string]any
		if err := json.NewDecoder(resp.Body).Decode(&ordens); err != nil {
			t.Fatal(err)
		}
		return len(ordens)
	}

	for _, valor := range []string{"abc", "10,555"} {
		antes := contarOrdens()
		req, _ := http.NewRequest("POST", a.url+"/ordens", strings.NewReader(url.Values{
			"cliente_id": {texto(clienteID)}, "descricao": {"Teste de valor limite"},
			"prioridade": {"BAIXA"}, "valor": {valor},
		}.Encode()))
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		req.AddCookie(sessao)
		resp, err := cliente.Do(req)
		if err != nil {
			t.Fatal(err)
		}
		corpo, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		if resp.StatusCode != http.StatusBadRequest || !strings.Contains(string(corpo), `id="erro-valor"`) {
			t.Errorf("valor %q: status %d; quer 400 com erro-valor", valor, resp.StatusCode)
		}
		if depois := contarOrdens(); depois != antes {
			t.Errorf("valor %q: %d ordens antes e %d depois; a OS não pode ser gravada", valor, antes, depois)
		}
	}
}
