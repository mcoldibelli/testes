DB ?= dados/ordens.db
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

sonar: cobertura ## analisa o projeto (exige SONAR_TOKEN gerado no SonarQube)
	docker run --rm -e SONAR_HOST_URL=http://host.docker.internal:9000 -e SONAR_TOKEN=$(SONAR_TOKEN) \
		-v "$(CURDIR):/usr/src" sonarsource/sonar-scanner-cli

entrega:         ## cria a estrutura de pastas do Drive (seção 11.3) em ./entrega
	sh tools/montar_entrega.sh
