from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import json
from time import sleep


sleep_duration = 3

with open('credentials.json') as file:
    creds = json.load(file)
    creds_login, creds_password = creds['credentials']['login'], creds['credentials']['password']

chrome_options = webdriver.ChromeOptions()
print('Browser driver is created.')
chrome_options.add_argument("--headless")
browser = webdriver.Chrome(options=chrome_options)
browser.get("https://hh.ru/account/login?backurl=%2F")
print('Authentication form is open.')
browser.find_element(By.CSS_SELECTOR, 'button[data-qa="expand-login-by-password"]').click()
print('Authentication form is switched.')
browser.find_element(By.CSS_SELECTOR, 'input[data-qa="login-input-username"]').send_keys(creds_login)
print('Login input is filled.')
browser.find_element(By.CSS_SELECTOR, 'input[data-qa="login-input-password"]').send_keys(creds_password)
print('Password input is filled.')
browser.find_element(By.CSS_SELECTOR, 'button[data-qa="account-login-submit"]').click()
print('Authentication is complete.')
sleep(sleep_duration)


def find_vacancy(vacancy: str) -> None:
    browser.get(
        "https://hh.ru/search/vacancy?search_field=name&search_field=company_name&search_field=description&"
        f"text={'+'.join(vacancy.split(' '))}&enable_snippets=true&L_save_area=true"
    )


find_vacancy('Data Engineer')
print('Page with vacancies is opened.')
sleep(sleep_duration)

# soup = BeautifulSoup(browser.page_source, "lxml")
# sleep(sleep_duration)
