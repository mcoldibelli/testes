// Package web expõe a API JSON (/api/...) e as páginas HTML.
package web

import (
	"context"
	"embed"
	"html/template"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"time"

	"ordens-servico/internal/app"
	"ordens-servico/internal/domain"
)

//go:embed templates/*.html
var arquivosTemplates embed.FS

type Server struct {
	svc     *app.Service
	log     *slog.Logger
	paginas map[string]*template.Template
}

func NovoServer(svc *app.Service, log *slog.Logger) *Server {
	funcs := template.FuncMap{
		"valor": domain.FormatarValor,
		"data":  func(t time.Time) string { return t.Local().Format("02/01/2006 15:04") },
	}
	paginas := map[string]*template.Template{}
	for _, nome := range []string{"login", "painel", "clientes", "cliente_form", "ordens", "ordem_form", "ordem_detalhe"} {
		paginas[nome] = template.Must(template.New("base.html").Funcs(funcs).
			ParseFS(arquivosTemplates, "templates/base.html", "templates/"+nome+".html"))
	}
	return &Server{svc: svc, log: log, paginas: paginas}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		escreverJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})

	// API JSON. Autenticação por "Authorization: Bearer <token>".
	mux.HandleFunc("POST /api/login", s.apiLogin)
	mux.Handle("GET /api/clientes", s.exigirToken(s.apiListarClientes))
	mux.Handle("POST /api/clientes", s.exigirToken(s.apiCriarCliente))
	mux.Handle("GET /api/clientes/{id}", s.exigirToken(s.apiBuscarCliente))
	mux.Handle("GET /api/ordens", s.exigirToken(s.apiListarOrdens))
	mux.Handle("POST /api/ordens", s.exigirToken(s.apiAbrirOrdem))
	mux.Handle("GET /api/ordens/{id}", s.exigirToken(s.apiBuscarOrdem))
	mux.Handle("PATCH /api/ordens/{id}/status", s.exigirToken(s.apiAlterarStatus))
	mux.Handle("GET /api/resumo", s.exigirToken(s.apiResumo))

	// Páginas HTML. Autenticação pelo cookie "sessao".
	mux.HandleFunc("GET /login", s.uiLoginForm)
	mux.HandleFunc("POST /login", s.uiLogin)
	mux.HandleFunc("POST /logout", s.uiLogout)
	mux.Handle("GET /{$}", s.exigirCookie(s.uiPainel))
	mux.Handle("GET /clientes", s.exigirCookie(s.uiClientes))
	mux.Handle("GET /clientes/novo", s.exigirCookie(s.uiClienteForm))
	mux.Handle("POST /clientes", s.exigirCookie(s.uiCriarCliente))
	mux.Handle("GET /ordens", s.exigirCookie(s.uiOrdens))
	mux.Handle("GET /ordens/nova", s.exigirCookie(s.uiOrdemForm))
	mux.Handle("POST /ordens", s.exigirCookie(s.uiAbrirOrdem))
	mux.Handle("GET /ordens/{id}", s.exigirCookie(s.uiOrdemDetalhe))
	mux.Handle("POST /ordens/{id}/status", s.exigirCookie(s.uiAlterarStatus))

	return s.registrarRequisicao(mux)
}

type chaveUsuario struct{}

func usuarioDe(ctx context.Context) domain.Usuario {
	u, _ := ctx.Value(chaveUsuario{}).(domain.Usuario)
	return u
}

func (s *Server) exigirToken(next http.HandlerFunc) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token, ok := strings.CutPrefix(r.Header.Get("Authorization"), "Bearer ")
		u, valido := s.svc.UsuarioDaSessao(token)
		if !ok || !valido {
			escreverJSON(w, http.StatusUnauthorized, map[string]string{"erro": "token ausente ou inválido"})
			return
		}
		next(w, r.WithContext(context.WithValue(r.Context(), chaveUsuario{}, u)))
	})
}

const nomeCookie = "sessao"

func (s *Server) exigirCookie(next http.HandlerFunc) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		c, err := r.Cookie(nomeCookie)
		if err != nil {
			http.Redirect(w, r, "/login", http.StatusSeeOther)
			return
		}
		u, ok := s.svc.UsuarioDaSessao(c.Value)
		if !ok {
			http.Redirect(w, r, "/login", http.StatusSeeOther)
			return
		}
		next(w, r.WithContext(context.WithValue(r.Context(), chaveUsuario{}, u)))
	})
}

type gravadorStatus struct {
	http.ResponseWriter
	status int
}

func (g *gravadorStatus) WriteHeader(status int) {
	g.status = status
	g.ResponseWriter.WriteHeader(status)
}

// registrarRequisicao grava método, caminho, status e duração de cada requisição.
// A duração no log serve de fonte para as medições de desempenho (RNF-01).
func (s *Server) registrarRequisicao(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		inicio := time.Now()
		g := &gravadorStatus{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(g, r)
		s.log.Info("requisicao",
			"metodo", r.Method, "caminho", r.URL.Path, "status", g.status,
			"duracao_ms", float64(time.Since(inicio).Microseconds())/1000)
	})
}

// idDoCaminho devolve false quando o {id} não é um inteiro positivo.
func idDoCaminho(r *http.Request) (int64, bool) {
	id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
	return id, err == nil && id > 0
}
