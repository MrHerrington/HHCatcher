import logging

import psycopg2

from hh_parser.tools import get_db_password


logger = logging.getLogger(__name__)

pg_password = get_db_password('../pg_password.txt', 'POSTGRES_PASSWORD_FILE')
connection = psycopg2.connect(
    database='hh_results',
    user='admin',
    password=pg_password,
    host='172.18.0.2',
    port='5432'
)

with connection:
    with connection.cursor() as cursor:
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS finger (
    
                 id SERIAL PRIMARY KEY,
                 url VARCHAR
    
               );'''
        )
        logger.info('Table "finger" created.')

connection.close()
