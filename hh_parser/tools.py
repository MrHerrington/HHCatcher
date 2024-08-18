# -*- coding: utf-8 -*-
"""
This module performs additional service tools for web scraping tools.

Classes:
    - MaxRetriesException: The class of exceptions raised
      when the number of retries is exceeded.

Functions:
    - retry_connect: The decorator repeats the function a
      specified number of times when an exception occurs.

"""


import typing as ty
from functools import wraps


class MaxRetriesException(Exception):
    """
    The class of exceptions raised when the number of retries is exceeded.

    """
    pass


def retry_connect(times: int, msg: str) -> ty.Callable:
    """
    The decorator repeats the function a specified number of times when an exception occurs.

    Args:
        times (int): Count of retries for the function.
        msg (str): Message to display when the number of retries is exceeded.

    """
    def outer_wrapper(func: ty.Callable) -> ty.Callable:
        @wraps(func)
        def inner_wrapper(*args, **kwargs) -> ty.Any:
            tries = 1
            exceptions = []

            while True:
                if tries > times:
                    raise MaxRetriesException(msg + ':\n' + ';\n'.join(exceptions))

                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    tries += 1
                    exceptions.append(f'{err}')
                    continue

        return inner_wrapper
    return outer_wrapper
