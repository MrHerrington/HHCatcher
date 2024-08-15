# -*- coding: utf-8 -*-


import json
import logging
import sys
import typing as ty
from contextlib import contextmanager
from pathlib import Path
from time import sleep

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait


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
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
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
            By.CSS_SELECTOR,
            'button[data-qa="expand-login-by-password"]'
        ))
    ).click()
    logger.info('Authentication form is switched.')

    WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            'input[data-qa="login-input-username"]'
        ))
    ).send_keys(creds.LOGIN)  # noqa
    logger.info('Login input is filled.')

    WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            'input[data-qa="login-input-password"]'
        ))
    ).send_keys(creds.PASSWORD)  # noqa
    logger.info('Password input is filled.')

    WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            'button[data-qa="account-login-submit"]'
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
def parse_from_page():
    def find_or_default(soup: BeautifulSoup,
                        selector: str,
                        value: str = None,
                        dafault: ty.Any = None) -> ty.Any:
        try:
            return soup.find(attrs={selector: value})
        except AttributeError:
            return dafault

    elements = driver.find_elements(
        By.XPATH,
        '//div[contains(@data-qa, "vacancy-serp__vacancy vacancy-serp__vacancy_standard") '
        'and .//*[contains(@data-qa, "vacancy-serp__vacancy_contacts")]]'
    )
    for element in elements:
        # vacancy main card info
        vacancy_soup = BeautifulSoup(element.get_attribute('innerHTML'), "lxml")

        vacancy_address = find_or_default(
            vacancy_soup, 'data-qa', 'vacancy-serp__vacancy-address', None
        ).text
        vacancy_employer = find_or_default(
            vacancy_soup, 'data-qa', 'vacancy-serp__vacancy-employer', None
        ).text
        vacancy_name = find_or_default(
            vacancy_soup, 'data-qa', 'serp-item__title', None
        ).text
        vacancy_work_experience = find_or_default(
            vacancy_soup, 'data-qa', 'vacancy-serp__vacancy-work-experience', None
        ).text
        vacancy_page_link = find_or_default(
            vacancy_soup, 'data-qa', 'bloko-header-2', None
        ).a['href']

        # vacancy contacts
        show_contacts_button = WebDriverWait(element, driver.TIMEOUT).until(  # noqa
            EC.element_to_be_clickable((
                By.CSS_SELECTOR, 'button[data-qa="vacancy-serp__vacancy_contacts"]'
            ))
        )
        show_contacts_button.location_once_scrolled_into_view  # noqa
        show_contacts_button.click()
        # waiting for loading contacts form
        contacts_form = WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 'div[data-qa="drop-base"], div[data-qa="bloko-drop-down"]'
            ))
        )
        contacts_soup = BeautifulSoup(contacts_form.get_attribute('innerHTML'), "lxml")

        vacancy_hr_fio = find_or_default(
            contacts_soup, 'data-qa', 'vacancy-contacts__fio', None
        ).text
        vacancy_hr_tel = ''.join(
            find_or_default(
                contacts_soup, 'class', 'vacancy-contacts-call-tracking__phone-number', None
            ).text.split()
        )
        vacancy_hr_email = find_or_default(
            contacts_soup, 'data-qa', 'vacancy-contacts__email', None
        ).text
        print(vacancy_address)
        print(vacancy_name)
        print(vacancy_employer)
        print(vacancy_work_experience)
        print(vacancy_page_link)
        print(vacancy_hr_fio)
        print(vacancy_hr_tel)
        print(vacancy_hr_email)
        print('\n'*3)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - [%(levelname)s]: %(message)s",
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)

    driver = create_driver(headless=True)
    log_in('credentials.json')
    find_vacancies('Data Engineer')
    parse_from_page()
