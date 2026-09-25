package domain

type Usuario struct {
	ID        int64
	Nome      string
	Email     string
	SenhaHash []byte
	Salt      []byte
}
