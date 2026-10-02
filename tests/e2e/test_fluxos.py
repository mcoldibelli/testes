"""Testes de sistema ponta a ponta (nível de sistema/interface).

Cada teste indica o caso manual (CT) e o requisito (RF) que automatiza.
"""
import uuid

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from conftest import BASE_URL, cpf_ficticio, entrar


def enviar(driver, id_botao):
    """Clica no botão e espera a página atual sair do DOM, ou seja, a resposta do POST carregar."""
    botao = driver.find_element(By.ID, id_botao)
    botao.click()
    # Durante a navegação o chromedriver às vezes devolve um erro genérico
    # ("Node with given id does not belong to the document") em vez de StaleElementReferenceException.
    # Por isso esta espera ignora WebDriverException e consulta de novo.
    WebDriverWait(driver, 5, ignored_exceptions=(WebDriverException,)).until(EC.staleness_of(botao))


def cadastrar_cliente(driver, espera, nome, cpf, email):
    driver.get(BASE_URL + "/clientes/novo")
    espera.until(EC.presence_of_element_located((By.ID, "nome"))).send_keys(nome)
    driver.find_element(By.ID, "cpf").send_keys(cpf)
    driver.find_element(By.ID, "email").send_keys(email)
    enviar(driver, "salvar")


def test_st01_login_valido_mostra_painel(driver, espera):
    """ST-01 | CT-01 | RF-01, RF-07"""
    entrar(driver, espera, "admin@teste.local", "Admin@123")
    usuario = espera.until(EC.visibility_of_element_located((By.ID, "usuario-logado")))
    assert usuario.text == "Administrador"
    assert driver.find_element(By.ID, "total").text.isdigit()


def test_st02_login_invalido_mostra_erro(driver, espera):
    """ST-02 | CT-02 | RF-01"""
    entrar(driver, espera, "admin@teste.local", "senha-errada")
    erro = espera.until(EC.visibility_of_element_located((By.ID, "erro")))
    assert erro.text == "e-mail ou senha inválidos"
    assert driver.current_url.endswith("/login")


def test_st03_cadastrar_cliente_e_buscar_por_cpf(logado, espera):
    """ST-03 | CT-06, CT-13 | RF-02, RF-03"""
    driver = logado
    cpf = cpf_ficticio()
    nome = "Cliente Selenium " + cpf[:4]
    cadastrar_cliente(driver, espera, nome, cpf, "selenium@teste.local")

    mensagem = espera.until(EC.visibility_of_element_located((By.ID, "mensagem")))
    assert mensagem.text == "Cliente cadastrado com sucesso."

    driver.find_element(By.ID, "busca").send_keys(cpf)
    enviar(driver, "buscar")
    linhas = espera.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#tabela-clientes tr[data-cpf]")))
    assert len(linhas) == 1
    assert linhas[0].get_attribute("data-cpf") == cpf
    assert nome in linhas[0].text


def test_st04_cpf_invalido_mostra_erro_e_mantem_dados(logado, espera):
    """ST-04 | CT-07 | RF-02"""
    driver = logado
    cadastrar_cliente(driver, espera, "Maria Teste", "529.982.247-24", "maria@teste.local")

    erro = espera.until(EC.visibility_of_element_located((By.ID, "erro-cpf")))
    assert erro.text == "CPF inválido"
    assert driver.find_element(By.ID, "nome").get_attribute("value") == "Maria Teste"


def test_st05_abrir_ordem_e_concluir(logado, espera):
    """ST-05 | CT-16, CT-22 | RF-04, RF-05, RF-06"""
    driver = logado
    cpf = cpf_ficticio()
    nome_cliente = "Cliente OS " + cpf[:6]
    cadastrar_cliente(driver, espera, nome_cliente, cpf, "os@teste.local")
    espera.until(EC.visibility_of_element_located((By.ID, "mensagem")))

    descricao = "Teste Selenium " + uuid.uuid4().hex[:8]
    driver.get(BASE_URL + "/ordens/nova")
    Select(espera.until(EC.presence_of_element_located((By.ID, "cliente_id")))).select_by_visible_text(nome_cliente)
    driver.find_element(By.ID, "descricao").send_keys(descricao)
    Select(driver.find_element(By.ID, "prioridade")).select_by_value("ALTA")
    driver.find_element(By.ID, "valor").send_keys("150,00")
    enviar(driver, "salvar")

    espera.until(EC.visibility_of_element_located((By.ID, "mensagem")))
    linha = driver.find_element(By.XPATH, f"//table[@id='tabela-ordens']//tr[td[text()='{descricao}']]")
    assert linha.find_element(By.CLASS_NAME, "status").text == "ABERTA"
    linha.find_element(By.TAG_NAME, "a").click()

    assert espera.until(EC.visibility_of_element_located((By.ID, "valor"))).text == "R$ 150,00"
    enviar(driver, "acao-EM_ANDAMENTO")
    assert driver.find_element(By.ID, "status-atual").text == "EM_ANDAMENTO"
    enviar(driver, "acao-CONCLUIDA")
    assert driver.find_element(By.ID, "status-atual").text == "CONCLUIDA"

    assert driver.find_element(By.ID, "concluida-em").text != ""
    assert driver.find_elements(By.CSS_SELECTOR, "[id^='acao-']") == []  # status final: sem ações


def test_st06_cancelar_sem_motivo_mostra_erro(logado, espera):
    """ST-06 | CT-24 | RF-05"""
    driver = logado
    driver.get(BASE_URL + "/ordens?status=ABERTA")
    espera.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tabela-ordens tr[data-id] a"))).click()

    espera.until(EC.element_to_be_clickable((By.ID, "acao-CANCELADA")))
    enviar(driver, "acao-CANCELADA")
    erro = espera.until(EC.visibility_of_element_located((By.ID, "erro")))
    assert "motivo" in erro.text
    assert driver.find_element(By.ID, "status-atual").text == "ABERTA"


def test_st07_erro_do_ultimo_campo_fica_acima_do_botao(logado, espera):
    """ST-07 | CT-11, CT-19 | RF-02, RF-04 | DEF-03"""
    driver = logado

    def assert_erro_acima_do_botao(id_erro):
        erro = espera.until(EC.visibility_of_element_located((By.ID, id_erro))).rect
        botao = driver.find_element(By.ID, "salvar").rect
        assert erro["y"] + erro["height"] <= botao["y"], f"{id_erro} {erro} na linha do botão {botao}"

    driver.get(BASE_URL + "/clientes/novo")
    espera.until(EC.presence_of_element_located((By.ID, "nome"))).send_keys("Ana Souza")
    driver.find_element(By.ID, "cpf").send_keys(cpf_ficticio())
    driver.find_element(By.ID, "email").send_keys("ana@teste.local")
    driver.find_element(By.ID, "telefone").send_keys("999994444")
    enviar(driver, "salvar")
    assert_erro_acima_do_botao("erro-telefone")

    driver.get(BASE_URL + "/ordens/nova")
    Select(espera.until(EC.presence_of_element_located((By.ID, "cliente_id")))).select_by_visible_text("Mercado Bom Preço")
    driver.find_element(By.ID, "descricao").send_keys("Teste de valor limite")
    Select(driver.find_element(By.ID, "prioridade")).select_by_value("BAIXA")
    driver.find_element(By.ID, "valor").send_keys("50000,01")
    enviar(driver, "salvar")
    assert_erro_acima_do_botao("erro-valor")


def test_st08_listas_sem_rolagem_horizontal_em_tela_estreita(logado):
    """ST-08 | NF-04 | RNF-02 | DEF-04"""
    driver = logado
    # O navegador pede 375 px, mas sem janela visível o Chrome e o Firefox usam no mínimo 500 px.
    # As tabelas têm cerca de 670 px, então a rolagem horizontal também aparece em 500 px.
    driver.set_window_size(375, 812)
    for caminho in ("/clientes", "/ordens"):
        driver.get(BASE_URL + caminho)
        pagina = driver.execute_script("return document.documentElement.scrollWidth")
        tela = driver.execute_script("return document.documentElement.clientWidth")
        assert pagina <= tela, f"{caminho}: página com {pagina} px em tela de {tela} px"
