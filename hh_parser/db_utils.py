"""
This module performs utilities for database management.

Functions:
    - get_db_password: The function returns the db password from the secrets file or system environment.

"""


import logging
import os
import typing as ty
from pathlib import Path

import psycopg2


logger = logging.getLogger(__name__)


def get_db_password(secrets_path: ty.Union[Path, str], secrets_env_var: str) -> str:
    """
    The function returns the db password from the secrets file or system environment.

    Args:
        secrets_path (str): Path to the secrets file.
        secrets_env_var (str): Environment variable name for the secrets file.

    """
    try:
        return get_db_password.PASSWORD
    except AttributeError:
        try:
            with open(secrets_path) as file:
                get_db_password.PASSWORD = file.readline().strip()
        except (Exception,):
            with open(os.environ[secrets_env_var]) as file:
                get_db_password.PASSWORD = file.readline().strip()

    return get_db_password.PASSWORD  # noqa


class DBManager:
    def __init__(self, conn_attrs: dict):
        self.__conn = psycopg2.connect(
            database=conn_attrs['database'],
            user=conn_attrs['user'],
            password=conn_attrs['password'],
            host=conn_attrs['host'],
            port=conn_attrs['port']
        )

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            return object.__getattribute__(self.__conn, attr)

    def execute_query(self, query: str) -> None:
        with self.__conn:
            with self.__conn.cursor() as cursor:
                cursor.execute(query)
