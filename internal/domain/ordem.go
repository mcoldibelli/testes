package domain

import (
	"fmt"
	"slices"
	"strings"
	"time"
	"unicode/utf8"
)

type Prioridade string

const (
	PrioridadeBaixa   Prioridade = "BAIXA"
	PrioridadeMedia   Prioridade = "MEDIA"
	PrioridadeAlta    Prioridade = "ALTA"
	PrioridadeCritica Prioridade = "CRITICA"
)

// slaPorPrioridade define o prazo de atendimento de cada prioridade (RN-06).
var slaPorPrioridade = map[Prioridade]time.Duration{
	PrioridadeBaixa:   72 * time.Hour,
	PrioridadeMedia:   48 * time.Hour,
	PrioridadeAlta:    24 * time.Hour,
	PrioridadeCritica: 4 * time.Hour,
}

func (p Prioridade) Valida() bool {
	_, ok := slaPorPrioridade[p]
	return ok
}

type Status string

const (
	StatusAberta      Status = "ABERTA"
	StatusEmAndamento Status = "EM_ANDAMENTO"
	StatusConcluida   Status = "CONCLUIDA"
	StatusCancelada   Status = "CANCELADA"
)

var TodosStatus = []Status{StatusAberta, StatusEmAndamento, StatusConcluida, StatusCancelada}

// transicoes lista os destinos permitidos para cada status (RN-08).
// CONCLUIDA e CANCELADA são finais.
var transicoes = map[Status][]Status{
	StatusAberta:      {StatusEmAndamento, StatusCancelada},
	StatusEmAndamento: {StatusConcluida, StatusCancelada},
}

func (s Status) Valido() bool { return slices.Contains(TodosStatus, s) }

func PodeTransitar(de, para Status) bool { return slices.Contains(transicoes[de], para) }

// Limites da RN-05 (descrição), RN-07 (valor) e RN-08 (motivo de cancelamento).
const (
	DescricaoMin     = 10
	DescricaoMax     = 500
	ValorMaxCentavos = 5_000_000 // R$ 50.000,00
	MotivoMin        = 10
)

type Ordem struct {
	ID                 int64      `json:"id"`
	ClienteID          int64      `json:"cliente_id"`
	Descricao          string     `json:"descricao"`
	Prioridade         Prioridade `json:"prioridade"`
	Status             Status     `json:"status"`
	ValorCentavos      int64      `json:"valor_centavos"`
	AbertaEm           time.Time  `json:"aberta_em"`
	Prazo              time.Time  `json:"prazo"`
	ConcluidaEm        *time.Time `json:"concluida_em,omitempty"`
	MotivoCancelamento string     `json:"motivo_cancelamento,omitempty"`
	// Atrasada é calculada na leitura e não é gravada no banco.
	Atrasada bool `json:"atrasada"`
}

// NovaOrdem valida os dados e calcula o prazo pelo SLA da prioridade (RN-05 a RN-07).
func NovaOrdem(clienteID int64, descricao string, p Prioridade, valorCentavos int64, agora time.Time) (Ordem, error) {
	descricao = strings.TrimSpace(descricao)

	erros := ErrValidacao{}
	if clienteID <= 0 {
		erros["cliente_id"] = "cliente obrigatório"
	}
	if n := utf8.RuneCountInString(descricao); n < DescricaoMin || n > DescricaoMax {
		erros["descricao"] = fmt.Sprintf("deve ter entre %d e %d caracteres", DescricaoMin, DescricaoMax)
	}
	if !p.Valida() {
		erros["prioridade"] = "use BAIXA, MEDIA, ALTA ou CRITICA"
	}
	if valorCentavos < 0 || valorCentavos > ValorMaxCentavos {
		erros["valor"] = "deve estar entre R$ 0,00 e R$ 50.000,00"
	}
	if len(erros) > 0 {
		return Ordem{}, erros
	}

	return Ordem{
		ClienteID:     clienteID,
		Descricao:     descricao,
		Prioridade:    p,
		Status:        StatusAberta,
		ValorCentavos: valorCentavos,
		AbertaEm:      agora,
		Prazo:         agora.Add(slaPorPrioridade[p]),
	}, nil
}

// AlterarStatus aplica a RN-08. O cancelamento exige motivo.
func (o *Ordem) AlterarStatus(novo Status, motivo string, agora time.Time) error {
	if !novo.Valido() {
		return ErrValidacao{"status": "status desconhecido"}
	}
	if !PodeTransitar(o.Status, novo) {
		return fmt.Errorf("%w: de %s para %s", ErrTransicaoInvalida, o.Status, novo)
	}
	motivo = strings.TrimSpace(motivo)
	if novo == StatusCancelada && utf8.RuneCountInString(motivo) < MotivoMin {
		return ErrValidacao{"motivo": fmt.Sprintf("o cancelamento exige motivo com pelo menos %d caracteres", MotivoMin)}
	}

	o.Status = novo
	switch novo {
	case StatusConcluida:
		o.ConcluidaEm = &agora
	case StatusCancelada:
		o.MotivoCancelamento = motivo
	}
	return nil
}

// EstaAtrasada é verdadeiro quando a ordem ainda está ativa depois do prazo (RN-09).
func (o Ordem) EstaAtrasada(agora time.Time) bool {
	ativa := o.Status == StatusAberta || o.Status == StatusEmAndamento
	return ativa && agora.After(o.Prazo)
}
