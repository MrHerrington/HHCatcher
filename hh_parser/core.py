# -*- coding: utf-8 -*-
"""
The module contains main web tools for web scraping source.

Functions:
    - create_driver: The function for creating browser driver with required options.
    - wait_for_page_load: The context manager for waiting for page load and execution script.
    - log_in: The function for authorization into source ecosystem.
    - find_vacancies: The function for finding vacancies on the main page and waiting for page load.
    - parse_page: The function for parsing relevant vacancies from current page.
    - parse_source: The function for parsing all pages in source.

"""


import csv
import logging
import os
import re
import typing as ty
from contextlib import contextmanager
from pathlib import Path
from time import sleep

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait

from hh_parser.tools import retry_connect, EmptyPageException


#############
# Constants #
#############

JOBS_CSV_FILE = Path('../jobs_info.csv')


###################
# Driver  section #
###################
def create_driver(logger: logging.Logger, headless: bool = True) -> webdriver.Chrome:
    """
    The function for creating browser driver with required options.

    Args:
        logger (logging.Logger): Logger object for logging system.
        headless (bool, optional): Enable or disable headless mode. Defaults to True.

    Returns:
        webdriver.Chrome: Browser driver object.

    """
    def __get_options() -> webdriver.ChromeOptions:
        """
        The service function for creating browser driver options.

        Returns:
            webdriver.ChromeOptions: Options for browser driver.

        """
        options = webdriver.ChromeOptions()

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/"
            "537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        )
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        if headless:
            options.add_argument("--headless")

        return options

    logger.info('Browser driver creation...')
    chrome_options = __get_options()
    driver = webdriver.Chrome(options=chrome_options)
    driver.TIMEOUT = 10
    driver.DEFAULT_PAGE_LOAD_TIMEOUT = driver.timeouts.page_load
    logger.info('Browser driver is created.')

    return driver


@contextmanager
def wait_for_page_load(driver: webdriver.Chrome) -> None:
    """
    The context manager for waiting for page load and execution script.

    Args:
        driver (webdriver.Chrome): Browser driver object.

    """
    old_page = driver.find_element(By.TAG_NAME, 'html')
    WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
        EC.staleness_of(old_page)
    )
    yield


def wait_less_timeout(driver: webdriver.Chrome, url: str) -> None:
    driver.set_page_load_timeout(3)

    try:
        driver.get(url)
    except TimeoutException:
        driver.execute_script("window.stop();")

    driver.set_page_load_timeout(driver.DEFAULT_PAGE_LOAD_TIMEOUT)  # noqa


##########################
# Authentication section #
##########################
@retry_connect(3, 'Unsuccessful authorization 3 times')
def log_in(driver: webdriver.Chrome,
           login_path: ty.Union[Path, str],
           pass_path: ty.Union[Path, str],
           logger: logging.Logger) -> None:
    """
    The function for authorization into source ecosystem.

    If an exception occurs, the function will throw an error after exhausting the set retries.

    Args:
        driver (webdriver.Chrome): Browser driver object.
        login_path (ty.Union[Path, str]): Path to file with login.
        pass_path (ty.Union[Path, str]): Path to file with password.
        logger (logging.Logger): Logger object for logging system.

    Raises:
        MaxRetriesException: If the number of retries is exceeded.

    """
    def __get_creds() -> ty.Callable:
        """
        The service function for getting credentials from JSON file.

        Returns:
            ty.Callable: Login and password as creds properties.

        """
        try:
            with open(login_path) as file:
                creds_ = file.readline().strip()
                __get_creds.LOGIN = creds_
            with open(pass_path) as file:
                creds_ = file.readline().strip()
                __get_creds.PASSWORD = creds_

        except FileNotFoundError:
            try:
                with open(os.environ['HH_LOGIN_FILE']) as file:
                    __get_creds.LOGIN = file.readline().strip()
                with open(os.environ['HH_PASSWORD_FILE']) as file:
                    __get_creds.PASSWORD = file.readline().strip()

            except KeyError:
                raise KeyError('Empty login-password secrets!')

        return __get_creds

    creds = __get_creds()

    logger.info('Authentication form opening...')
    wait_less_timeout(driver, "https://hh.ru/account/login?backurl=%2F")
    logger.info('Authentication form is open.')

    try:
        WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
            EC.element_to_be_clickable((
                By.CSS_SELECTOR, 'button[data-qa="expand-login-by-password"]'
            ))
        ).click()
    except (Exception,):
        WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
            EC.element_to_be_clickable((
                By.XPATH, '//*[contains(text(), "Войти с\u00A0паролем")]'
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


def find_vacancies(driver: webdriver.Chrome, logger: logging.Logger, vacancy: str) -> None:
    """
    The function for finding vacancies on the main page and waiting for page load.

    Args:
        driver (webdriver.Chrome): Browser driver object.
        logger (logging.Logger): Logger object for logging system.
        vacancy (str): Search query.

    """
    logger.info('Loading main page...')
    with wait_for_page_load(driver):
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
def parse_page(driver: webdriver.Chrome) -> None:
    """
    The function for parsing relevant vacancies from current page.

    If an exception occurs, the function will throw an error after exhausting the set retries.

    Args:
        driver (webdriver.Chrome): Browser driver object.

    Raises:
        MaxRetriesException: If the number of retries is exceeded.

    """
    elements = driver.find_elements(
        By.XPATH,
        '//div[contains(@data-qa, "vacancy-serp__vacancy vacancy-serp__vacancy_standard") '
        'and .//*[contains(@data-qa, "vacancy-serp__vacancy_contacts")]]'
    )

    if len(elements) == 0:
        raise EmptyPageException("Empty page or source's end!")

    for element in elements:
        driver.execute_script("arguments[0].scrollIntoView();", element)
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
            vacancy_salary = vacancy_soup.select(
                'span[class*="compensation-text"]'
            )[0].text
        except (Exception,):
            currency_types = '|'.join((
                '₽', r'\$', '€', '₸'
            ))
            try:
                vacancy_salary = vacancy_soup.find(
                    text=re.compile(currency_types)
                ).parent.text
            except (Exception,):
                vacancy_salary = None

        try:
            vacancy_required_experience = vacancy_soup.find(attrs={
                'data-qa': 'vacancy-serp__vacancy-work-experience'
            }).text
        except (Exception,):
            exp_pattern = (
                '|'.join(exp_level.replace(' ', r'\s') for exp_level in (
                    'Без опыта',
                    'Опыт 1-3 года',
                    'Опыт 3-6 лет',
                    'Опыт более 6 лет'
                ))
            )
            try:
                vacancy_required_experience = vacancy_soup.find(
                        text=re.compile(exp_pattern)
                )
            except (Exception,):
                vacancy_required_experience = None

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
            EC.visibility_of_element_located((
                By.CSS_SELECTOR, 'div[data-qa="drop-base"], div[data-qa="bloko-drop-down"]'
            ))
        )
        contacts_soup = BeautifulSoup(contacts_form.get_attribute('innerHTML'), "lxml")
        # waiting for closing contacts form
        driver.execute_script("arguments[0].click();", show_contacts_button)
        contacts_form = WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
            EC.invisibility_of_element_located((
                By.CSS_SELECTOR, 'div[data-qa="drop-base"], div[data-qa="bloko-drop-down"]'
            ))
        )

        try:
            vacancy_hr_fio = contacts_soup.find(attrs={
                'data-qa': ['vacancy-contacts__fio',
                            'vacancy-serp__vacancy_contacts-fio',
                            'title-container',
                            'title']
            }).text
        except (Exception,):
            vacancy_hr_fio = None

        try:
            vacancy_hr_tel = ''.join(contacts_soup.find(attrs={
                'class': ['vacancy-contacts-call-tracking__phone-number',
                          'vacancy-contacts__phone vacancy-contacts__phone_search']
            }).text.split())[:12]  # 11 digits of +7 xxx xxx-xx-xx format
        except (Exception,):
            try:
                vacancy_hr_tel = contacts_soup.find(
                    href=re.compile(
                        r'tel:(\+7|8)\d{10}'
                    )
                ).text
            except (Exception,):
                vacancy_hr_tel = None

        try:
            vacancy_hr_email = contacts_soup.find(attrs={
                'data-qa': ['vacancy-contacts__email',
                            'vacancy-serp__vacancy_contacts-email']
            }).text
        except (Exception,):
            try:
                vacancy_hr_email = contacts_soup.find(
                    href=re.compile(
                        r'mailto:.*@.*.(.)*'
                    )
                ).text
            except (Exception,):
                vacancy_hr_email = None

        if not parse_source.vacancies:  # noqa
            titles = (
                'address',
                'employer',
                'name',
                'salary',
                'required_experience',
                'page_link',
                'hr_fio',
                'hr_tel',
                'hr_email'
            )
            with open(JOBS_CSV_FILE, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(titles)

        results_row = (
            vacancy_address,
            vacancy_employer,
            vacancy_name,
            vacancy_salary,
            vacancy_required_experience,
            vacancy_page_link,
            vacancy_hr_fio,
            vacancy_hr_tel,
            vacancy_hr_email
        )

        with open(JOBS_CSV_FILE, 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(results_row)

        parse_source.vacancies += 1  # noqa


def parse_source(driver: webdriver.Chrome, logger: logging.Logger) -> None:
    """
    The function for parsing all pages in source.

    If an exception occurs, the function will throw an error after exhausting the set retries.

    Args:
        driver (webdriver.Chrome): Browser driver object.
        logger (logging.Logger): Logger object.

    Raises:
        MaxRetriesException: If the number of retries is exceeded.

    """
    parse_source.vacancies = 0
    parse_source.pages = 0
    base_page = driver.current_url

    while True:
        try:
            parse_page(driver)
            logger.info(f'Parsed: {parse_source.vacancies} vacancies | {parse_source.pages + 1} pages...')
        except EmptyPageException:
            break

        parse_source.pages += 1

        try:
            next_page = driver.find_element(
                By.CSS_SELECTOR,
                'a[data-qa="pager-next"], a[data-qa="number-pages-next"]'
            )
            driver.execute_script("arguments[0].scrollIntoView();", next_page)
            driver.execute_script("arguments[0].click();", next_page)
            WebDriverWait(driver, driver.TIMEOUT).until(  # noqa
                EC.url_changes(driver.current_url)
            )
        except NoSuchElementException:
            next_page = base_page + f'&page={parse_source.pages}'
            wait_less_timeout(driver, next_page)
