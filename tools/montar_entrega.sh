#!/bin/sh
# Cria a estrutura obrigatória de pastas do Drive (manual, seção 11.3) e copia os produtos.
# Uso: sh tools/montar_entrega.sh [pasta-destino]
# Copie antes o artefato do CI para resultados/ci-final (gh run download <run> -D resultados/ci-final).
set -eu
DESTINO="${1:-entrega}"
for p in 00_IDENTIFICACAO_E_README 01_SISTEMA_ALVO 02_REQUISITOS_ESCOPO_RISCOS 03_PLANO_DE_TESTES \
         04_CASOS_E_RASTREABILIDADE 05_EXECUCAO_MANUAL 06_DEFEITOS 07_AUTOMACAO_UNITARIA \
         08_INTEGRACAO_API 09_SISTEMA_INTERFACE 10_ACEITACAO_NAO_FUNCIONAIS 11_METRICAS_E_QUALIDADE \
         12_TDD_CICD_MELHORIA 13_RELATORIO_FINAL 14_APRESENTACAO_E_VIDEO_CONTINGENCIA \
         15_DIARIO_DE_PARTICIPACAO 16_BACKUP_ENTREGA; do
  mkdir -p "$DESTINO/$p"
done
P="docs/P2_TQS_planilha.xlsx"
CI="resultados/ci-final"
ART=$(find "$CI" -type d -name 'resultados-*' 2>/dev/null | head -1)
cp README.md "$DESTINO/00_IDENTIFICACAO_E_README/"
cp docs/P01-ficha-do-sistema.md "$DESTINO/00_IDENTIFICACAO_E_README/"
git archive --format=zip -o "$DESTINO/01_SISTEMA_ALVO/ordens-servico-codigo-fonte.zip" HEAD
cp docs/P02-requisitos-escopo-riscos.md "$P" "$DESTINO/02_REQUISITOS_ESCOPO_RISCOS/"
cp docs/P03-plano-de-testes.md "$DESTINO/03_PLANO_DE_TESTES/"
cp "$P" "$DESTINO/04_CASOS_E_RASTREABILIDADE/"
cp "$P" "$DESTINO/05_EXECUCAO_MANUAL/"
cp -R docs/evidencias/execucao "$DESTINO/05_EXECUCAO_MANUAL/evidencias"
cp docs/P07-defeitos.csv docs/defeitos/*.md "$DESTINO/06_DEFEITOS/"
cp tests/postman/*.json "$DESTINO/08_INTEGRACAO_API/"
cp "$P" "$DESTINO/10_ACEITACAO_NAO_FUNCIONAIS/"
cp -R docs/evidencias/nao-funcionais "$DESTINO/10_ACEITACAO_NAO_FUNCIONAIS/evidencias"
cp "$P" docs/evidencias/SONAR_LINHA-DE-BASE_2026-09-29.png docs/evidencias/sonar/* "$DESTINO/11_METRICAS_E_QUALIDADE/"
cp docs/graficos/*.png "$DESTINO/11_METRICAS_E_QUALIDADE/"
cp docs/P11-roteiro-tdd-cicd-qualidade.md docs/evidencias/tdd/* docs/evidencias/cicd/* "$DESTINO/12_TDD_CICD_MELHORIA/"
cp docs/P12-relatorio-final.docx docs/P12-relatorio-final.pdf "$DESTINO/13_RELATORIO_FINAL/"
cp docs/P13-apresentacao.pptx docs/P13-apresentacao.pdf docs/P13-roteiro-de-demonstracao.md "$DESTINO/14_APRESENTACAO_E_VIDEO_CONTINGENCIA/"
cp "$P" "$DESTINO/15_DIARIO_DE_PARTICIPACAO/"
if [ -n "$ART" ]; then
  cp -R "$ART" "$DESTINO/12_TDD_CICD_MELHORIA/artefato-ci"
  cp "$ART/resultados/go-test.txt" "$ART/resultados/cobertura.txt" "$DESTINO/07_AUTOMACAO_UNITARIA/"
  cp "$ART/resultados/newman.xml" "$DESTINO/08_INTEGRACAO_API/"
  cp "$ART/resultados/e2e.xml" "$DESTINO/09_SISTEMA_INTERFACE/"
  cp -R "$ART/tests/e2e/evidencias" "$DESTINO/09_SISTEMA_INTERFACE/capturas"
else
  echo "Aviso: $CI não existe; as pastas 07 a 09 ficam sem resultados do CI." >&2
fi
cp tests/e2e/test_fluxos.py tests/e2e/conftest.py tests/e2e/requirements.txt "$DESTINO/09_SISTEMA_INTERFACE/"
cp internal/domain/*_test.go "$DESTINO/07_AUTOMACAO_UNITARIA/"
find "$DESTINO" -name .DS_Store -delete
(cd "$DESTINO" && rm -f 16_BACKUP_ENTREGA/backup.zip && zip -qr 16_BACKUP_ENTREGA/backup.zip . -x '16_BACKUP_ENTREGA/*')
echo "Estrutura criada em $DESTINO/"
