// Package domain contém as regras de negócio do sistema, sem dependência de banco ou HTTP.
package domain

import (
	"errors"
	"sort"
	"strings"
)

// ErrValidacao agrupa as mensagens de validação por nome de campo.
type ErrValidacao map[string]string

func (e ErrValidacao) Error() string {
	campos := make([]string, 0, len(e))
	for c := range e {
		campos = append(campos, c)
	}
	sort.Strings(campos)
	partes := make([]string, 0, len(e))
	for _, c := range campos {
		partes = append(partes, c+": "+e[c])
	}
	return "dados inválidos: " + strings.Join(partes, "; ")
}

var (
	ErrNaoEncontrado     = errors.New("registro não encontrado")
	ErrCPFDuplicado      = errors.New("CPF já cadastrado")
	ErrTransicaoInvalida = errors.New("transição de status não permitida")
)
