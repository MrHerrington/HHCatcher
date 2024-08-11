import json
from contextlib import contextmanager
import logging
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - [%(levelname)s]: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

timeout = 10

with open('credentials.json') as file:
    creds = json.load(file)
    creds_login, creds_password = creds['credentials']['login'], creds['credentials']['password']

logger.info('Browser driver creation...')
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)
logger.info('Browser driver is created.')

logger.info('Authentication form opening...')
driver.get("https://hh.ru/account/login?backurl=%2F")
logger.info('Authentication form is open.')
driver.find_element(By.CSS_SELECTOR, 'button[data-qa="expand-login-by-password"]').click()
logger.info('Authentication form is switched.')
driver.find_element(By.CSS_SELECTOR, 'input[data-qa="login-input-username"]').send_keys(creds_login)
logger.info('Login input is filled.')
driver.find_element(By.CSS_SELECTOR, 'input[data-qa="login-input-password"]').send_keys(creds_password)
logger.info('Password input is filled.')
driver.find_element(By.CSS_SELECTOR, 'button[data-qa="account-login-submit"]').click()
logger.info('Authentication is complete.')


@contextmanager
def wait_for_page_load() -> None:
    old_page = driver.find_element(By.TAG_NAME, 'html')
    WebDriverWait(driver, timeout).until(
        EC.staleness_of(old_page)
    )
    yield


def find_vacancy(vacancy: str) -> None:
    logger.info('Loading main page...')
    with wait_for_page_load():
        driver.get(
            "https://hh.ru/search/vacancy?search_field=name&search_field=company_name&search_field=description&"
            f"text={'+'.join(vacancy.split(' '))}&enable_snippets=true&L_save_area=true"
        )
        logger.info('Page with vacancies is opened.')


find_vacancy('Data Engineer')

elements = driver.find_elements(By.XPATH, '//div[contains (@data-qa, "vacancy-serp__vacancy vacancy-serp__vacancy_standard")]')
for element in elements:
    soup = BeautifulSoup(element.get_attribute('innerHTML'), "lxml")
    print(soup)
    print('\n' * 5)
