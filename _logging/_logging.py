import _logging
from inspect import currentframe
from contextlib import contextmanager
from typing import TypeVar, Callable, Union
from _logging import Logger as Log
from _logging.handlers import RotatingFileHandler
from functools import wraps
from pgcommon import pgcommon as _common_
from pgutil import pgdirectory

RT = TypeVar('RT')  # return type


"""
one _logging class
one decorator
"""


def info_logger(message: str = "",
                func_str: str = "",
                logger: Log = None,
                addition_msg: str = "") -> None:
    try:
        if func_str:
            message = f"{func_str}: {message}"
        logger.info(f"{message} {addition_msg}") if logger else print(f"{message} {addition_msg}")
    except Exception as err:
        raise err


def error_logger(func_str: str, error,
                 logger: Log = None,
                 addition_msg: str = "",
                 mode: str = "critical",
                 ignore_flag: bool = True,
                 set_trace: bool = False) -> None:
    def _not_found(*args, **kwargs):
        raise "error mode should be 'critical', 'debug', 'error' and 'info'"
    if logger:
        _logger_mode = {"critical": logger.critical,
                        "debug": logger.debug,
                        "error": logger.error,
                        "info": logger.info
                        }
    try:
        _logger_mode.get(mode, _logger_mode)(f"Error in {func_str} {addition_msg} {error}") if logger \
            else print(f"Error in {func_str} {addition_msg} {error}")
        if logger and set_trace: logger.exception("trace")
        return exit(99) if not ignore_flag else None
    except Exception as err:
        raise err



class MyLogger:
    def __init__(self):
        _logging.basicConfig(level=_logging.DEBUG)

    def get_logger(self, name=None):
        return _logging.getLogger(name)


class PGLoggerSingleton:

    def __new__(cls):
        if not hasattr(cls, 'logger'):
            cls.logger = setup_log("myTestLog", "/Users/jianhuang/temp/test.log")
            # cls.instance = super(PGLoggerSingleton, cls).__new__(cls)

        return cls.logger


def setup_log(log_name: str, log_filepath: str) -> Log:
    """Start a logger with rotation setup
    Args:
        log_name: name of log object
        log_filepath: the filepath of the log
    Returns:
        return logger object
    """
    try:

        if not log_filepath.endswith(".log"):
            _common_.error_logger(currentframe().f_code.co_name,
                                  f"the log filepath {log_filepath} does not end with .log", None, ignore_flag=False)
        _directory = '/'.join(log_filepath.split("/")[:-1])
        pgdirectory.createdirectory(_directory)
        logger = _logging.getLogger(log_name)
        logger.setLevel(_logging.INFO)

        handler = RotatingFileHandler(log_filepath, maxBytes=10000, backupCount=10)
        formatter = _logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    except Exception as err:
        raise err



def bind_logger(_func: Callable[..., RT] = None,
                *,
                logger: Union[Log, str] = "auto",
                variable_name: str = "logger") -> Callable[[Callable[..., RT]], Callable[..., RT]]:

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            func_params = func.__code__.co_varnames

            session_in_args = variable_name in func_params and func_params.index(variable_name) < len(args)
            session_in_kwargs = variable_name in kwargs

            if (session_in_args or session_in_kwargs) and (isinstance(kwargs[variable_name], Log)
                                                           or isinstance(kwargs[variable_name], PGLoggerSingleton)):
                return func(*args, **kwargs)
            else:
                if logger != "auto" and (isinstance(logger, Log) or isinstance(logger, PGLoggerSingleton)):
                    kwargs[variable_name] = logger
                else:
                    first_args = next(iter(args), None)
                    _logger_params = [x for x in kwargs.values() if isinstance(x, Log) or isinstance(x, PGLoggerSingleton)]\
                                      + [x for x in args if isinstance(x, Log) or isinstance(x, PGLoggerSingleton)]
                    if hasattr(first_args, "__dict__"):
                        _logger_params += [x for x in first_args.__dict__.values() if isinstance(x, Log)
                                           or isinstance(x, PGLoggerSingleton)]
                    kwargs[variable_name] = None if logger is None else next(iter(_logger_params), PGLoggerSingleton())
                return func(*args, **kwargs)

        return wrapper
    return decorator






def petllog(_func: Callable[..., RT] = None, _mode: str = "print", *, petllogger: Union[MyLogger, Log] = None):
    def deco_log(func):
        wraps(func)

        def wrapper(*args, **kwargs):
            logger = None if _mode == "print" else get_default_logger()
            try:
                if petllogger is None:
                    first_args = next(iter(args), None)  # capture first arg to check for `self`
                    logger_params = [  # does kwargs have any logger
                                        x
                                        for x in kwargs.values()
                                        if isinstance(x, Log) or isinstance(x, MyLogger)
                                    ] + [
                                        x
                                        for x in args
                                        if isinstance(x, Log) or isinstance(x, MyLogger)
                                    ]
                    if hasattr(first_args, "__dict__"):  # is first argument `self`
                        logger_params = logger_params + [
                            x
                            for x in first_args.__dict__.values()  # does class (dict) members have any logger
                            if isinstance(x, Log)
                               or isinstance(x, MyLogger)
                        ]
                    h_logger = next(iter(logger_params), MyLogger())  # get the next/first/default logger
                else:
                    h_logger = petllogger  # logger is passed explicitly to the decorator

                if isinstance(h_logger, MyLogger):
                    logger = h_logger.get_logger(func.__name__)
                else:
                    logger = h_logger
                _common_.info_logger(f"function {func.__name__} called with args "
                                     f"{', '.join([repr(a) for a in args] + [f'{k}={v!r}' for k, v in kwargs.items()])}",
                                     logger=logger)
            except Exception as err:
                pass

            try:
                return func(*args, **kwargs)
            except Exception as err:
                _common_.error_logger(func.__name__,
                                      f"exception: {str(err)}",
                                      logger=logger,
                                      mode="error",
                                      ignore_flag=False)
                raise err

        return wrapper

    if _func is None:
        return deco_log
    else:
        return deco_log(_func)


def petllog(_func: Callable[..., RT] = None, _mode: str = "print", *, petllogger: Union[MyLogger, Log] = None):
    def deco_log(func):
        wraps(func)

        def wrapper(*args, **kwargs):
            logger = None if _mode == "print" else setup_log("mylogging", "/Users/jianhuang/temp")
            try:
                if petllogger is None:
                    first_args = next(iter(args), None)  # capture first arg to check for `self`
                    logger_params = [  # does kwargs have any logger
                                        x
                                        for x in kwargs.values()
                                        if isinstance(x, Log) or isinstance(x, MyLogger)
                                    ] + [
                                        x
                                        for x in args
                                        if isinstance(x, Log) or isinstance(x, MyLogger)
                                    ]
                    if hasattr(first_args, "__dict__"):  # is first argument `self`
                        logger_params = logger_params + [
                            x
                            for x in first_args.__dict__.values()  # does class (dict) members have any logger
                            if isinstance(x, Log)
                               or isinstance(x, MyLogger)
                        ]
                    h_logger = next(iter(logger_params), MyLogger())  # get the next/first/default logger
                else:
                    h_logger = petllogger  # logger is passed explicitly to the decorator

                if isinstance(h_logger, MyLogger):
                    logger = h_logger.get_logger(func.__name__)
                else:
                    logger = h_logger
                _common_.info_logger(f"function {func.__name__} called with args "
                                     f"{', '.join([repr(a) for a in args] + [f'{k}={v!r}' for k, v in kwargs.items()])}",
                                     logger=logger)
            except Exception as err:
                pass

            try:
                return func(*args, **kwargs)
            except Exception as err:
                _common_.error_logger(func.__name__,
                                      f"exception: {str(err)}",
                                      logger=logger,
                                      mode="error",
                                      ignore_flag=False)
                raise err

        return wrapper

    if _func is None:
        return deco_log
    else:
        return deco_log(_func)


