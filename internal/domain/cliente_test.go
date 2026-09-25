package domain

import (
	"errors"
	"strings"
	"testing"
	"time"
)

var agoraFixo = time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC)

// UT-01 | RF-02, RN-02 | Particionamento de equivalência e valor limite no CPF.
func TestCPFValido(t *testing.T) {
	casos := []struct {
		nome string
		cpf  string
		quer bool
	}{
		{"válido só dígitos", "52998224725", true},
		{"válido com máscara", "529.982.247-25", true},
		{"dígito verificador errado", "52998224724", false},
		{"todos os dígitos iguais", "11111111111", false},
		{"10 dígitos (limite inferior - 1)", "5299822472", false},
		{"12 dígitos (limite superior + 1)", "529982247250", false},
		{"letras no meio", "529a8224725", false},
		{"vazio", "", false},
	}
	for _, c := range casos {
		t.Run(c.nome, func(t *testing.T) {
			if got := CPFValido(c.cpf); got != c.quer {
				t.Errorf("CPFValido(%q) = %v, quer %v", c.cpf, got, c.quer)
			}
		})
	}
}

// UT-02 | RF-02, RN-01 | Valor limite no tamanho do nome (3 a 100 caracteres).
func TestNovoCliente_LimitesDoNome(t *testing.T) {
	casos := []struct {
		tamanho int
		valido  bool
	}{
		{2, false}, {3, true}, {100, true}, {101, false},
	}
	for _, c := range casos {
		nome := strings.Repeat("á", c.tamanho) // rune com 2 bytes: conta caracteres, não bytes
		_, err := NovoCliente(nome, "52998224725", "a@teste.local", "", agoraFixo)
		if (err == nil) != c.valido {
			t.Errorf("nome com %d caracteres: err = %v, quer válido = %v", c.tamanho, err, c.valido)
		}
	}
}

// UT-03 | RF-02, RN-03, RN-04 | Particionamento de equivalência em e-mail e telefone.
func TestNovoCliente_EmailETelefone(t *testing.T) {
	casos := []struct {
		nome, email, telefone string
		campoComErro          string // vazio = cadastro válido
	}{
		{"dados válidos, telefone vazio", "ana@teste.local", "", ""},
		{"telefone com 10 dígitos", "ana@teste.local", "(14) 3333-4444", ""},
		{"telefone com 11 dígitos", "ana@teste.local", "(14) 99999-4444", ""},
		{"telefone com 9 dígitos", "ana@teste.local", "999994444", "telefone"},
		{"telefone com letras", "ana@teste.local", "14 9999A4444", "telefone"},
		{"e-mail sem arroba", "ana.teste.local", "", "email"},
		{"e-mail sem ponto no domínio", "ana@teste", "", "email"},
	}
	for _, c := range casos {
		t.Run(c.nome, func(t *testing.T) {
			_, err := NovoCliente("Ana Souza", "52998224725", c.email, c.telefone, agoraFixo)
			if c.campoComErro == "" {
				if err != nil {
					t.Fatalf("erro inesperado: %v", err)
				}
				return
			}
			var ev ErrValidacao
			if !errors.As(err, &ev) || ev[c.campoComErro] == "" {
				t.Fatalf("quer erro no campo %q, obteve %v", c.campoComErro, err)
			}
		})
	}
}

// UT-04 | RF-02 | Normalização: CPF e telefone gravados só com dígitos, e-mail em minúsculas.
func TestNovoCliente_Normaliza(t *testing.T) {
	c, err := NovoCliente("  Ana Souza  ", "529.982.247-25", " Ana@Teste.Local ", "(14) 3333-4444", agoraFixo)
	if err != nil {
		t.Fatalf("erro inesperado: %v", err)
	}
	if c.Nome != "Ana Souza" || c.CPF != "52998224725" || c.Email != "ana@teste.local" || c.Telefone != "1433334444" {
		t.Errorf("normalização incorreta: %+v", c)
	}
}
