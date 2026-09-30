DB ?= dados/ordens.db
export SONAR_TOKEN # vale também para "make sonar SONAR_TOKEN=..."
E2E_VENV = tests/e2e/.venv

.PHONY: run reset test-unit test-integracao cobertura test-api e2e-setup test-e2e sonar-up sonar entrega

run:             ## inicia o sistema em http://localhost:8080
	go run ./cmd/server -db $(DB)

reset:           ## apaga o banco, recria os dados fictícios e inicia o sistema
	go run ./cmd/server -reset -db $(DB)

test-unit:       ## testes unitários (regras de negócio)
	go test -count=1 -v ./internal/domain/...

test-integracao: ## testes de integração (HTTP + serviço + SQLite)
	go test -count=1 -v ./internal/web/...

cobertura:       ## gera coverage.out (usado pelo SonarQube) e mostra o total
	go test -count=1 -coverprofile=coverage.out ./...
	go tool cover -func=coverage.out | tail -1

test-api:        ## testes de API com Newman (o sistema precisa estar rodando)
	npx --yes newman@6 run tests/postman/ordens-servico.postman_collection.json \
		-e tests/postman/local.postman_environment.json

e2e-setup:       ## cria o ambiente Python dos testes Selenium
	python3 -m venv $(E2E_VENV)
	$(E2E_VENV)/bin/pip install -r tests/e2e/requirements.txt

test-e2e:        ## testes de sistema com Selenium (o sistema precisa estar rodando)
	cd tests/e2e && .venv/bin/pytest -v

sonar-up:        ## sobe o SonarQube local em http://localhost:9000
	docker run -d --name sonarqube -p 9000:9000 sonarqube:community

sonar: cobertura ## analisa o projeto no SonarQube local (exige SONAR_TOKEN no ambiente)
	@test -n "$$SONAR_TOKEN" || (echo "defina SONAR_TOKEN antes: export SONAR_TOKEN=<token>" && exit 1)
	# Scanner nativo via npm: a imagem Docker do scanner é só amd64 e, emulada no Mac Apple Silicon,
	# fica lenta demais para a análise de CSS/JS ("bridge server is unresponsive").
	# O token vem da variável de ambiente e não aparece na saída do make.
	npx --yes sonarqube-scanner@4 -Dsonar.host.url=http://localhost:9000

entrega:         ## cria a estrutura de pastas do Drive (seção 11.3) em ./entrega
	sh tools/montar_entrega.sh
