# O que falta para a entrega

Estes itens dependem de você, de outra pessoa ou do professor. Nenhum resultado deles foi registrado sem execução.

## 1. Revisar e confirmar

- [ ] Ler e compreender o relatório, a apresentação e o código do TDD. O manual exige que você explique tudo (seções 14.1 e 15).
- [ ] Confirmar se o texto sobre uso de IA, na folha de identificação do relatório, está correto e se segue a orientação do professor.
- [ ] Revisar no Diario as 4 linhas de 05/11/2026 e os tempos informados. Retirar "revisão do aluno pendente" depois de revisar.
- [ ] Registrar no Diario a entrega e a aprovação do P01, com a data real.
- [ ] Escrever em `docs/P01-ficha-do-sistema.md` a data da aprovação, no lugar de `_informar_`.
- [ ] Confirmar que a aprovação do professor cobre o trabalho individual (seção 4.1) e o uso do pacote `testing` do Go (seção 8.3).

## 2. Executar com uma pessoa que não fez os testes

1. Inicie o sistema com `make reset`.
2. Peça que a pessoa execute AC-01 a AC-04 (aba Aceitacao), sem ajuda. Preencha participante, observações, dificuldades e decisão. Apague o texto "Não executado".
3. Para o NF-07, peça: "cadastre o cliente X e abra uma OS ALTA para ele". Meça tempo, erros e satisfação (1 a 5). Preencha Resultado obtido, Conclusão e Evidências na aba NaoFuncionais.
4. Guarde as capturas em `docs/evidencias`, abra a planilha no Excel e salve.
5. Gere de novo os documentos: `tools/.venv/bin/python tools/gerar_relatorio.py` e `tools/.venv/bin/python tools/gerar_apresentacao.py`.
6. Revise as interpretações das métricas e da seção 12 do relatório: elas citam a situação em 05/11/2026.

## 3. Gravar

- [ ] Vídeo de contingência de 3 a 5 minutos (`docs/P13-roteiro-de-demonstracao.md`, seção 4). Salve em `entrega/14_APRESENTACAO_E_VIDEO_CONTINGENCIA`.

## 4. Entregar

1. Mesclar o PR da branch `entrega-final` no `main`, se o pipeline estiver aprovado.
2. Dar acesso ao professor no GitHub: Settings > Collaborators (o repositório é privado).
3. `gh run download <run final> -D resultados/ci-final` e `make entrega`.
4. Preencher, assinar digitalmente e exportar em PDF o `docs/COMPROVANTE_DE_ENTREGA-modelo.docx`. Guardar como `COMPROVANTE_DE_ENTREGA.pdf`, na pasta 00.
5. Enviar `entrega/` para a pasta do Drive indicada pelo professor, com o nome `P2_TQS_2026_TURMA_GRUPOXX_ORDENS-DE-SERVICO` (confirme turma e número do grupo).
6. Testar links em janela anônima: repositório, issues, pipeline, vídeo e Drive.
