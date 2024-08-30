# -*- coding: utf-8 -*-
"""
The main script. Runs scrapping of hh.ru process for searching relevant vacancies.

"""


import logging
import sys
from time import perf_counter

import chromedriver_autoinstaller

from hh_parser.core import (
    create_driver, log_in, find_vacancies, parse_source
)
from hh_parser.tools import EmptyPageException


if __name__ == '__main__':
    start_time = perf_counter()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s]: %(message)s",
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)

    chromedriver_autoinstaller.install()

    driver = create_driver(logger, headless=False)
    log_in(driver, '../credentials.json', logger)
    find_vacancies(driver, logger, 'Data Engineer')
    parse_source(driver)

    logger.info(f'Parsed {parse_source.vacancies} relevant vacancies '  # noqa
                f'from {parse_source.pages} pages.')  # noqa
    logger.info(f'Completed for total time: {perf_counter() - start_time} seconds.')
