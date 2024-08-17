# -*- coding: utf-8 -*-


import json
import logging
import sys
import typing as ty
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait

from hh_parser.tools import retry_connect


###################
# Driver  section #
###################
def create_driver(headless: bool = True) -> webdriver.Chrome:
    def get_options() -> webdriver.ChromeOptions:
        options = webdriver.ChromeOptions()

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/"
            "537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        )
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")

        if headless:
            options.add_argument("--headless")

        return options

    logger.info('Browser driver creation...')
    chrome_options = get_options()
    driver_ = webdriver.Chrome(options=chrome_options)
    driver_.TIMEOUT = 10
    driver_.DEFAULT_PAGE_LOAD_TIMEOUT = driver_.timeouts.page_load
    logger.info('Browser driver is created.')

    return driver_


@contextmanager
def wait_for_page_load() -> None:
    old_page = driver.find_element(By.TAG_NAME, 'html')
    WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
        EC.staleness_of(old_page)
    )
    yield


##########################
# Authentication section #
##########################
@retry_connect(3, 'Unsuccessful authorization 3 times')
def log_in(creds_path: ty.Union[Path, str]) -> None:
    def get_creds() -> ty.Callable:
        with open(creds_path) as file:
            creds_ = json.load(file)
            get_creds.LOGIN = creds_['credentials']['login']
            get_creds.PASSWORD = creds_['credentials']['password']

        return get_creds

    creds = get_creds()

    logger.info('Authentication form opening...')
    driver.set_page_load_timeout(3)
    try:
        driver.get("https://hh.ru/account/login?backurl=%2F")
    except TimeoutException:
        driver.execute_script("window.stop();")
    driver.set_page_load_timeout(driver.DEFAULT_PAGE_LOAD_TIMEOUT)  # noqa
    logger.info('Authentication form is open.')

    WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
        EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'button[data-qa="expand-login-by-password"]'
        ))
    ).click()
    logger.info('Authentication form is switched.')

    WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
        EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'input[data-qa="login-input-username"]'
        ))
    ).send_keys(creds.LOGIN)  # noqa
    logger.info('Login input is filled.')

    WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
        EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'input[data-qa="login-input-password"]'
        ))
    ).send_keys(creds.PASSWORD)  # noqa
    logger.info('Password input is filled.')

    WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
        EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'button[data-qa="account-login-submit"]'
        ))
    ).click()
    logger.info('Authentication is complete.')


def find_vacancies(vacancy: str) -> None:
    logger.info('Loading main page...')
    with wait_for_page_load():
        driver.get(
            # Only Russia, remote job format
            "https://hh.ru/search/vacancy?hhtmFrom=main&hhtmFromLabel=vacancy_search_line&search_field=name&"
            "search_field=company_name&search_field=description&enable_snippets=true&L_save_area=true&area=113&"
            f"schedule=remote&text={'+'.join(vacancy.split(' '))}"

            # All vacancies, any job format
            # "https://hh.ru/search/vacancy?search_field=name&search_field=company_name&search_field=description&"
            # f"text={'+'.join(vacancy.split(' '))}&enable_snippets=true&L_save_area=true"
        )
    logger.info('Page with vacancies is opened.')


###################
# Parsing section #
###################
@retry_connect(5, 'Unsuccessful page parsing 5 times')
def parse_page():
    elements = driver.find_elements(
        By.XPATH,
        '//div[contains(@data-qa, "vacancy-serp__vacancy vacancy-serp__vacancy_standard") '
        'and .//*[contains(@data-qa, "vacancy-serp__vacancy_contacts")]]'
    )
    for element in elements:
        # vacancy main card info
        vacancy_soup = BeautifulSoup(element.get_attribute('innerHTML'), "lxml")

        try:
            vacancy_address = vacancy_soup.find(attrs={
                'data-qa': 'vacancy-serp__vacancy-address'
            }).text
        except (Exception,):
            vacancy_address = None

        try:
            vacancy_employer = vacancy_soup.find(attrs={
                'data-qa': 'vacancy-serp__vacancy-employer'
            }).text
        except (Exception,):
            vacancy_employer = None

        try:
            vacancy_name = vacancy_soup.find(attrs={
                'data-qa': 'serp-item__title'
            }).text
        except (Exception,):
            vacancy_name = None

        try:
            vacancy_work_experience = vacancy_soup.find(attrs={
                'data-qa': 'vacancy-serp__vacancy-work-experience'
            }).text
        except (Exception,):
            vacancy_work_experience = None

        try:
            vacancy_page_link = vacancy_soup.find(attrs={
                'data-qa': 'bloko-header-2'
            }).a['href']
        except (Exception,):
            vacancy_page_link = None

        # vacancy contacts
        show_contacts_button = WebDriverWait(element, driver.TIMEOUT).until(  # noqa
            EC.element_to_be_clickable((
                By.CSS_SELECTOR, 'button[data-qa="vacancy-serp__vacancy_contacts"]'
            ))
        )
        driver.execute_script("arguments[0].click();", show_contacts_button)
        # waiting for loading contacts form
        contacts_form = WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 'div[data-qa="drop-base"], div[data-qa="bloko-drop-down"]'
            ))
        )
        contacts_soup = BeautifulSoup(contacts_form.get_attribute('innerHTML'), "lxml")

        try:
            vacancy_hr_fio = contacts_soup.find(attrs={
                'data-qa': 'vacancy-contacts__fio'
            }).text
        except (Exception,):
            vacancy_hr_fio = None

        try:
            vacancy_hr_tel = ''.join(contacts_soup.find(attrs={
                'class': 'vacancy-contacts-call-tracking__phone-number'
            }).text.split())
        except (Exception,):
            vacancy_hr_tel = None

        try:
            vacancy_hr_email = contacts_soup.find(attrs={
                'data-qa': 'vacancy-contacts__email'
            }).text
        except (Exception,):
            vacancy_hr_email = None

        driver.execute_script("arguments[0].click();", show_contacts_button)

        print(vacancy_address)
        print(vacancy_name)
        print(vacancy_employer)
        print(vacancy_work_experience)
        print(vacancy_page_link)
        print(vacancy_hr_fio)
        print(vacancy_hr_tel)
        print(vacancy_hr_email)
        print('\n'*3)

        parse_page.vacancies += 1  # noqa


def parse_source():
    parse_page.vacancies = 0
    parse_source.pages = 0

    while True:
        parse_page()
        parse_source.pages += 1

        try:
            next_page = driver.find_element(By.CSS_SELECTOR, 'a[data-qa="pager-next"]')
            driver.execute_script("arguments[0].click();", next_page)
            WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
                EC.url_changes(driver.current_url)
            )

        except NoSuchElementException:
            break


if __name__ == '__main__':
    start_time = perf_counter()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - [%(levelname)s]: %(message)s",
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)

    driver = create_driver(headless=False)
    log_in('../credentials.json')
    find_vacancies('Data Engineer')

    # parse_source()

    # logger.info(f'Parsed {parse_page.vacancies} relevant vacancies '  # noqa
    #             f'from {parse_source.pages} pages.')  # noqa
    # logger.info(f'Completed for total time: {perf_counter() - start_time} seconds.')
