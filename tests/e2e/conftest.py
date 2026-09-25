"""Configuração dos testes de sistema com Selenium.

Variáveis de ambiente:
  BASE_URL  endereço do sistema (padrão http://localhost:8080)
  HEADLESS  "0" abre o navegador visível (padrão "1", sem janela)
  BROWSER   "chrome" (padrão) ou "firefox"
"""
import os
import random
from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
NAVEGADOR = os.environ.get("BROWSER", "chrome")
PASTA_EVIDENCIAS = Path(__file__).parent / "evidencias"


@pytest.fixture
def driver():
    # O Selenium Manager baixa o driver certo (chromedriver ou geckodriver).
    headless = os.environ.get("HEADLESS", "1") == "1"
    if NAVEGADOR == "firefox":
        opcoes = webdriver.FirefoxOptions()
        if headless:
            opcoes.add_argument("-headless")
        d = webdriver.Firefox(options=opcoes)
        d.set_window_size(1280, 900)
    else:
        opcoes = webdriver.ChromeOptions()
        if headless:
            opcoes.add_argument("--headless=new")
        opcoes.add_argument("--window-size=1280,900")
        opcoes.add_argument("--no-sandbox")  # necessário no runner Linux do GitHub Actions
        d = webdriver.Chrome(options=opcoes)
    yield d
    d.quit()


@pytest.fixture
def espera(driver):
    return WebDriverWait(driver, timeout=5)


@pytest.fixture
def logado(driver, espera):
    entrar(driver, espera, "admin@teste.local", "Admin@123")
    espera.until(EC.presence_of_element_located((By.ID, "usuario-logado")))
    return driver


def entrar(driver, espera, email, senha):
    driver.get(BASE_URL + "/login")
    espera.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(email)
    driver.find_element(By.ID, "senha").send_keys(senha)
    driver.find_element(By.ID, "entrar").click()


def cpf_ficticio():
    """Gera um CPF válido e aleatório para o teste poder ser repetido sem duplicar dados."""
    def dv(base):
        soma = sum(int(d) * (len(base) + 1 - i) for i, d in enumerate(base))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    base = "".join(str(random.randint(0, 9)) for _ in range(9))
    if len(set(base)) == 1:
        base = "123456780"
    base += dv(base)
    return base + dv(base)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Salva captura de tela ao fim de cada teste (aprovado ou reprovado) como evidência."""
    resultado = yield
    relatorio = resultado.get_result()
    if relatorio.when != "call" or "driver" not in item.funcargs:
        return
    PASTA_EVIDENCIAS.mkdir(exist_ok=True)
    situacao = "APROVADO" if relatorio.passed else "REPROVADO"
    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
    nome = f"{item.name}_{NAVEGADOR}_{situacao}_{carimbo}"
    driver = item.funcargs["driver"]
    driver.save_screenshot(str(PASTA_EVIDENCIAS / f"{nome}.png"))
    if relatorio.failed:
        (PASTA_EVIDENCIAS / f"{nome}.html").write_text(driver.page_source, encoding="utf-8")
        (PASTA_EVIDENCIAS / f"{nome}.txt").write_text(relatorio.longreprtext, encoding="utf-8")
