import logging
import sys

from hh_parser.db_utils import get_db_password, DBManager


logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s]: %(message)s",
        stream=sys.stdout
)
logger = logging.getLogger(__name__)

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
logger.info("Table 'vacancies' ready for writing.")

db_conn.close()
