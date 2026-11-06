package domain

import (
	"errors"
	"strings"
	"testing"
	"time"
)

// UT-05 | RF-04, RN-05 | Valor limite na descrição (10 a 500 caracteres).
func TestNovaOrdem_LimitesDaDescricao(t *testing.T) {
	casos := []struct {
		tamanho int
		valido  bool
	}{
		{9, false}, {10, true}, {500, true}, {501, false},
	}
	for _, c := range casos {
		_, err := NovaOrdem(1, strings.Repeat("x", c.tamanho), PrioridadeMedia, 0, agoraFixo)
		if (err == nil) != c.valido {
			t.Errorf("descrição com %d caracteres: err = %v, quer válido = %v", c.tamanho, err, c.valido)
		}
	}
}

// UT-06 | RF-04, RN-07 | Valor limite no valor estimado (R$ 0,00 a R$ 50.000,00).
func TestNovaOrdem_LimitesDoValor(t *testing.T) {
	casos := []struct {
		centavos int64
		valido   bool
	}{
		{-1, false}, {0, true}, {ValorMaxCentavos, true}, {ValorMaxCentavos + 1, false},
	}
	for _, c := range casos {
		_, err := NovaOrdem(1, "Troca de sensor da porta", PrioridadeMedia, c.centavos, agoraFixo)
		if (err == nil) != c.valido {
			t.Errorf("valor %d centavos: err = %v, quer válido = %v", c.centavos, err, c.valido)
		}
	}
}

// UT-07 | RF-04, RN-06 | O prazo é a data de abertura mais o SLA da prioridade.
func TestNovaOrdem_PrazoPorPrioridade(t *testing.T) {
	casos := map[Prioridade]time.Duration{
		PrioridadeBaixa:   72 * time.Hour,
		PrioridadeMedia:   48 * time.Hour,
		PrioridadeAlta:    24 * time.Hour,
		PrioridadeCritica: 5 * time.Hour,
	}
	for p, sla := range casos {
		o, err := NovaOrdem(1, "Troca de sensor da porta", p, 0, agoraFixo)
		if err != nil {
			t.Fatalf("%s: erro inesperado: %v", p, err)
		}
		if want := agoraFixo.Add(sla); !o.Prazo.Equal(want) {
			t.Errorf("%s: prazo = %v, quer %v", p, o.Prazo, want)
		}
		if o.Status != StatusAberta {
			t.Errorf("%s: status inicial = %s, quer ABERTA", p, o.Status)
		}
	}

	if _, err := NovaOrdem(1, "Troca de sensor da porta", "URGENTE", 0, agoraFixo); err == nil {
		t.Error("prioridade desconhecida foi aceita")
	}
}

// UT-08 | RF-05, RN-08 | Tabela de decisão com as 16 combinações de status de origem e destino.
func TestAlterarStatus_TabelaDeTransicoes(t *testing.T) {
	permitidas := map[[2]Status]bool{
		{StatusAberta, StatusEmAndamento}:    true,
		{StatusAberta, StatusCancelada}:      true,
		{StatusEmAndamento, StatusConcluida}: true,
		{StatusEmAndamento, StatusCancelada}: true,
	}
	for _, de := range TodosStatus {
		for _, para := range TodosStatus {
			o := Ordem{Status: de}
			err := o.AlterarStatus(para, "Cliente desistiu do serviço", agoraFixo)
			if permitidas[[2]Status{de, para}] {
				if err != nil {
					t.Errorf("%s -> %s: erro inesperado: %v", de, para, err)
				}
				continue
			}
			if !errors.Is(err, ErrTransicaoInvalida) {
				t.Errorf("%s -> %s: quer ErrTransicaoInvalida, obteve %v", de, para, err)
			}
		}
	}
}

// UT-09 | RF-05, RN-08 | Cancelamento exige motivo com 10 caracteres ou mais (valor limite).
func TestAlterarStatus_CancelamentoExigeMotivo(t *testing.T) {
	casos := []struct {
		motivo string
		valido bool
	}{
		{"", false}, {"123456789", false}, {"          ", false}, {"1234567890", true},
	}
	for _, c := range casos {
		o := Ordem{Status: StatusAberta}
		err := o.AlterarStatus(StatusCancelada, c.motivo, agoraFixo)
		if (err == nil) != c.valido {
			t.Errorf("motivo %q: err = %v, quer válido = %v", c.motivo, err, c.valido)
		}
		if c.valido && o.MotivoCancelamento != c.motivo {
			t.Errorf("motivo gravado = %q, quer %q", o.MotivoCancelamento, c.motivo)
		}
	}
}

// UT-10 | RF-05 | Concluir grava a data de conclusão.
func TestAlterarStatus_ConcluirGravaData(t *testing.T) {
	o := Ordem{Status: StatusEmAndamento}
	if err := o.AlterarStatus(StatusConcluida, "", agoraFixo); err != nil {
		t.Fatalf("erro inesperado: %v", err)
	}
	if o.ConcluidaEm == nil || !o.ConcluidaEm.Equal(agoraFixo) {
		t.Errorf("ConcluidaEm = %v, quer %v", o.ConcluidaEm, agoraFixo)
	}
}

// UT-11 | RF-07, RN-09 | Valor limite no prazo: no instante do prazo a ordem ainda não está atrasada.
func TestOrdem_EstaAtrasada(t *testing.T) {
	prazo := agoraFixo
	casos := []struct {
		nome   string
		status Status
		agora  time.Time
		quer   bool
	}{
		{"1 segundo antes do prazo", StatusAberta, prazo.Add(-time.Second), false},
		{"no prazo exato", StatusAberta, prazo, false},
		{"1 segundo depois do prazo", StatusAberta, prazo.Add(time.Second), true},
		{"em andamento depois do prazo", StatusEmAndamento, prazo.Add(time.Hour), true},
		{"concluída depois do prazo", StatusConcluida, prazo.Add(time.Hour), false},
		{"cancelada depois do prazo", StatusCancelada, prazo.Add(time.Hour), false},
	}
	for _, c := range casos {
		t.Run(c.nome, func(t *testing.T) {
			o := Ordem{Status: c.status, Prazo: prazo}
			if got := o.EstaAtrasada(c.agora); got != c.quer {
				t.Errorf("EstaAtrasada = %v, quer %v", got, c.quer)
			}
		})
	}
}
