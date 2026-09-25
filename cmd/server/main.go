// Comando server inicia o sistema de ordens de serviço.
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"ordens-servico/internal/app"
	"ordens-servico/internal/store"
	"ordens-servico/internal/web"
)

func main() {
	if err := executar(); err != nil {
		fmt.Fprintln(os.Stderr, "erro:", err)
		os.Exit(1)
	}
}

func executar() error {
	endereco := flag.String("addr", ":8080", "endereço HTTP")
	caminhoBanco := flag.String("db", "dados/ordens.db", "arquivo do banco SQLite")
	reset := flag.Bool("reset", false, "apaga o banco e recria os dados fictícios")
	flag.Parse()

	log := slog.New(slog.NewTextHandler(os.Stdout, nil))

	// O contexto é cancelado por Ctrl+C ou SIGTERM e inicia o encerramento.
	ctx, parar := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer parar()

	if *reset {
		if err := os.Remove(*caminhoBanco); err != nil && !errors.Is(err, os.ErrNotExist) {
			return fmt.Errorf("apagar banco: %w", err)
		}
	}
	if err := os.MkdirAll(filepath.Dir(*caminhoBanco), 0o755); err != nil {
		return fmt.Errorf("criar pasta do banco: %w", err)
	}

	st, err := store.Abrir(ctx, *caminhoBanco)
	if err != nil {
		return err
	}
	defer st.Close()

	svc := app.NovoService(st, time.Now)
	if err := svc.Semear(ctx); err != nil {
		return fmt.Errorf("semear dados: %w", err)
	}

	srv := &http.Server{
		Addr:              *endereco,
		Handler:           web.NovoServer(svc, log).Handler(),
		ReadHeaderTimeout: 5 * time.Second,
	}

	erros := make(chan error, 1)
	go func() {
		log.Info("servidor iniciado", "endereco", *endereco, "banco", *caminhoBanco)
		erros <- srv.ListenAndServe()
	}()

	select {
	case err := <-erros:
		return fmt.Errorf("servidor HTTP: %w", err)
	case <-ctx.Done():
	}

	log.Info("encerrando servidor")
	ctxFim, cancelar := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancelar()
	if err := srv.Shutdown(ctxFim); err != nil {
		return fmt.Errorf("encerrar servidor: %w", err)
	}
	return nil
}
