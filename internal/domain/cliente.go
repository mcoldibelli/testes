package domain

import (
	"fmt"
	"net/mail"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"
)

// Limites da RN-01 (nome do cliente).
const (
	NomeMin = 3
	NomeMax = 100
)

var (
	formatoCPF      = regexp.MustCompile(`^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$`)
	formatoTelefone = regexp.MustCompile(`^[\d\s()-]+$`)
)

type Cliente struct {
	ID       int64     `json:"id"`
	Nome     string    `json:"nome"`
	CPF      string    `json:"cpf"` // somente dígitos
	Email    string    `json:"email"`
	Telefone string    `json:"telefone,omitempty"` // somente dígitos
	CriadoEm time.Time `json:"criado_em"`
}

// NovoCliente normaliza e valida os dados de um cliente (RN-01 a RN-04).
func NovoCliente(nome, cpf, email, telefone string, agora time.Time) (Cliente, error) {
	c := Cliente{
		Nome:     strings.TrimSpace(nome),
		CPF:      SomenteDigitos(cpf),
		Email:    strings.ToLower(strings.TrimSpace(email)),
		Telefone: SomenteDigitos(telefone),
		CriadoEm: agora,
	}

	erros := ErrValidacao{}
	if n := utf8.RuneCountInString(c.Nome); n < NomeMin || n > NomeMax {
		erros["nome"] = fmt.Sprintf("deve ter entre %d e %d caracteres", NomeMin, NomeMax)
	}
	if !CPFValido(cpf) {
		erros["cpf"] = "CPF inválido"
	}
	if !emailValido(c.Email) {
		erros["email"] = "e-mail inválido"
	}
	if tel := strings.TrimSpace(telefone); tel != "" && !telefoneValido(tel) {
		erros["telefone"] = "deve ter 10 ou 11 dígitos"
	}
	if len(erros) > 0 {
		return Cliente{}, erros
	}
	return c, nil
}

// CPFValido aceita "00000000000" ou "000.000.000-00" e confere os dígitos verificadores (RN-02).
func CPFValido(cpf string) bool {
	if !formatoCPF.MatchString(strings.TrimSpace(cpf)) {
		return false
	}
	d := SomenteDigitos(cpf)
	if strings.Count(d, d[:1]) == len(d) {
		return false
	}
	return digitoVerificador(d[:9]) == int(d[9]-'0') &&
		digitoVerificador(d[:10]) == int(d[10]-'0')
}

func digitoVerificador(base string) int {
	soma := 0
	peso := len(base) + 1
	for i, r := range base {
		soma += int(r-'0') * (peso - i)
	}
	resto := soma % 11
	if resto < 2 {
		return 0
	}
	return 11 - resto
}

func SomenteDigitos(s string) string {
	var b strings.Builder
	for _, r := range s {
		if r >= '0' && r <= '9' {
			b.WriteRune(r)
		}
	}
	return b.String()
}

func emailValido(email string) bool {
	endereco, err := mail.ParseAddress(email)
	if err != nil || endereco.Address != email {
		return false
	}
	_, dominio, _ := strings.Cut(email, "@")
	return strings.Contains(dominio, ".")
}

func telefoneValido(tel string) bool {
	n := len(SomenteDigitos(tel))
	return formatoTelefone.MatchString(tel) && (n == 10 || n == 11)
}
