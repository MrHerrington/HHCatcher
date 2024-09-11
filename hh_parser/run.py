import logging
import sys

import psycopg2

from hh_parser.tools import get_db_password


logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s]: %(message)s",
        stream=sys.stdout
)
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
            # '''
            #
            # CREATE TABLE IF NOT EXISTS vacancies (
            #
            #   id smallint SERIAL PRIMARY KEY,
            #   address VARCHAR DEFAULT NULL,
            #   employer VARCHAR DEFAULT NULL,
            #   position VARCHAR DEFAULT NULL,
            #   salary VARCHAR DEFAULT NULL,
            #   required_experience VARCHAR DEFAULT NULL,
            #   page_link VARCHAR DEFAULT NULL,
            #   hr_fio VARCHAR DEFAULT NULL,
            #   hr_tel VARCHAR DEFAULT NULL,
            #   hr_email VARCHAR DEFAULT NULL
            #
            # );
            #
            # '''

            '''
            
            DROP TABLE IF EXISTS temp;
            
            CREATE TABLE IF NOT EXISTS temp (id integer, nums integer, msg VARCHAR);
            
            DO $$
            
            DECLARE
               x integer := 100;
            BEGIN
               FOR i IN 1..10 LOOP
                  IF MOD(i,2) = 0 THEN     -- i is even
                     INSERT INTO temp VALUES (i, x, 'i is even');
                  ELSE
                     INSERT INTO temp VALUES (i, x, 'i is odd');
                  END IF;
                  x := x + 100;
               END LOOP;
            END;
            
            $$ LANGUAGE plpgsql;
            
            COMMIT;
            
            '''
        )
        logger.info('Table "temp" created.')

connection.close()
