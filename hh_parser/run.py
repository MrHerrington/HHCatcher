# -*- coding: utf-8 -*-
"""
The main script. Runs scrapping of hh.ru process for searching relevant vacancies.

"""


import asyncio
import logging
import sys
from time import perf_counter

import chromedriver_autoinstaller
from pyspark.sql import SparkSession

from hh_parser.core import (
    create_driver,
    find_vacancies,
    log_in,
    parse_source
)
from hh_parser.db_utils import (
    DBManager,
    get_db_password
)


async def extract_data():
    logger.info('Data extraction started...')
    start_time = perf_counter()

    chromedriver_autoinstaller.install()

    driver = create_driver(headless=True)
    log_in(driver, '../hh_login.txt', '../hh_password.txt')
    find_vacancies(driver, 'Data Engineer')
    parse_source(driver, 5)

    logger.info(f'Parsed {parse_source.vacancies} relevant vacancies '  # noqa
                f'from {parse_source.pages} pages.')  # noqa
    logger.info(f'Data successfully extracted for total time: {perf_counter() - start_time} seconds.')


async def prepare_warehouse():
    logger.info('Preparing warehouse started...')
    pg_password = get_db_password('../pg_password.txt', 'POSTGRES_PASSWORD_FILE')
    db_conn = DBManager(
        {
            'database': 'hh_results',
            'user': 'admin',
            'password': pg_password,
            'host': '172.18.0.2',
            'port': '5432'
        }
    )

    main.db_conn = db_conn

    db_conn.execute_query(
        '''
        DO $$

        BEGIN

          CREATE TABLE IF NOT EXISTS vacancies (
            id SERIAL PRIMARY KEY,
            address VARCHAR DEFAULT NULL,
            employer VARCHAR DEFAULT NULL,
            position VARCHAR DEFAULT NULL,
            salary VARCHAR DEFAULT NULL,
            required_experience VARCHAR DEFAULT NULL,
            page_link VARCHAR DEFAULT NULL,
            hr_fio VARCHAR DEFAULT NULL,
            hr_tel VARCHAR DEFAULT NULL,
            hr_email VARCHAR DEFAULT NULL
          );

          IF EXISTS (SELECT 1 FROM information_schema.tables
                      WHERE table_schema = current_schema()
                        AND table_name = 'vacancies') THEN
            TRUNCATE vacancies;
          END IF;

        END;

        $$ LANGUAGE plpgsql;
        '''
    )
    logger.info("Table 'vacancies' in DB 'hh_results' ready for loading data.")

    db_conn.close()


async def main():
    main.db_conn: DBManager  # noqa

    logger.info('Create PySpark session...')
    spark = SparkSession.builder.getOrCreate()
    logger.info('PySpark session created.')

    logger.info('Extracting data and preparing warehouse started...')
    await asyncio.gather(extract_data(), prepare_warehouse())
    logger.info('Data extracted to CSV file and warehouse prepared for writing.')

    logger.info('Loading process started...')
    vacancies_data = spark.read.format('csv').option('header', 'true').load('/csv_vault/jobs_info.csv')

    pg_url = 'postgres://%s:%s@%s:%s/%s' % (
        main.db_conn.conn_attrs['user'],
        main.db_conn.conn_attrs['password'],
        main.db_conn.conn_attrs['host'],
        main.db_conn.conn_attrs['port'],
        main.db_conn.conn_attrs['database']
    )

    vacancies_data.write.format('jdbc').options(
        url='jdbc:%s' % pg_url,
        driver='org.postgresql.Driver',
        dbtable='vacancies',
        user=main.db_conn.conn_attrs['user'],
        password=main.db_conn.conn_attrs['password']
    ).mode('append').save()

    logger.info('ETL process finished.')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s]: %(message)s",
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)

    asyncio.run(main())
