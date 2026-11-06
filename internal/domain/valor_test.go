package domain

import "testing"

// UT-12 | RF-04, RN-07 | Particionamento de equivalência no formato do valor digitado.
func TestParseValor(t *testing.T) {
	casos := []struct {
		entrada  string
		centavos int64
		valido   bool
	}{
		{"", 0, true},
		{"1500", 150000, true},
		{"1500,5", 150050, true},
		{"1500.50", 150050, true},
		{"0,01", 1, true},
		{"1500,505", 0, false},
		{"-10", 0, false},
		{"1.500,00", 150000, true},
		{"12.345,6", 1234560, true},
		{"1.50,00", 0, false},
		{"abc", 0, false},
	}
	for _, c := range casos {
		got, err := ParseValor(c.entrada)
		if (err == nil) != c.valido || got != c.centavos {
			t.Errorf("ParseValor(%q) = %d, %v; quer %d, válido = %v", c.entrada, got, err, c.centavos, c.valido)
		}
	}
}

func TestFormatarValor(t *testing.T) {
	casos := map[int64]string{
		0:       "R$ 0,00",
		5:       "R$ 0,05",
		150050:  "R$ 1.500,50",
		5000000: "R$ 50.000,00",
	}
	for centavos, quer := range casos {
		if got := FormatarValor(centavos); got != quer {
			t.Errorf("FormatarValor(%d) = %q, quer %q", centavos, got, quer)
		}
	}
}
