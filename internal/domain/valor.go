package domain

import (
	"regexp"
	"strconv"
	"strings"
)

var (
	formatoDecimal = regexp.MustCompile(`^\d{1,9}([.,]\d{1,2})?$`)
	// O ponto só é separador de milhar com vírgula decimal e grupos de 3 dígitos.
	formatoMilhar = regexp.MustCompile(`^\d{1,3}(\.\d{3})+,\d{1,2}$`)
)

// ParseValor converte "1500", "1500,5", "1500.50" ou "1.500,00" em centavos. Texto vazio vale zero.
func ParseValor(s string) (int64, error) {
	s = strings.TrimSpace(s)
	if s == "" {
		return 0, nil
	}
	if formatoMilhar.MatchString(s) {
		s = strings.ReplaceAll(s, ".", "")
	}
	if !formatoDecimal.MatchString(s) {
		return 0, ErrValidacao{"valor": "use o formato 1234,56"}
	}
	inteiro, frac, _ := strings.Cut(strings.ReplaceAll(s, ",", "."), ".")
	frac = (frac + "00")[:2]
	centavos, err := strconv.ParseInt(inteiro+frac, 10, 64)
	if err != nil {
		return 0, ErrValidacao{"valor": "use o formato 1234,56"}
	}
	return centavos, nil
}

// FormatarValor devolve centavos no formato "R$ 1.234,56".
func FormatarValor(centavos int64) string {
	inteiro := strconv.FormatInt(centavos/100, 10)
	var b strings.Builder
	for i, r := range inteiro {
		if i > 0 && (len(inteiro)-i)%3 == 0 {
			b.WriteByte('.')
		}
		b.WriteRune(r)
	}
	return "R$ " + b.String() + "," + strconv.FormatInt(centavos%100+100, 10)[1:]
}
