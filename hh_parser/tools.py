# -*- coding: utf-8 -*-


from functools import wraps


class MaxRetriesException(Exception):
    pass


def retry_connect(times, msg):
    retry_connect.times = 0
    exceptions = []

    def outer_wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            nonlocal times

            while True:
                retry_connect.times += 1

                if retry_connect.times > times:
                    raise MaxRetriesException(msg + ':\n' + ';\n'.join(exceptions))

                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    exceptions.append(f'{err}')
                    continue
        return inner_wrapper
    return outer_wrapper
