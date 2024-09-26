import os
import shutil
from inspect import currentframe
from logging import Logger as Log
from _common import _common as _common_
from pathlib import Path


def create_directory(dirpath: str, logger: Log = None) -> bool:
    try:
        o_umask = os.umask(0)
        os.makedirs(dirpath)
    except FileExistsError:
        return True
    except OSError:
        if not os.path.isdir(dirpath):
            _common_.error_logger(currentframe().f_code.co_name,
                                 f"creation of the directory {dirpath} failed",
                                  logger=logger,
                                  mode="error",
                                  ignore_flag=True)
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=logger,
                              mode="error",
                              ignore_flag=True)
    else:
        _common_.info_logger(f"Successfully created the directory {dirpath}", logger=logger)
    finally:
        os.umask(o_umask)

    return True


def identity_remove_directory(dirpath: str, logger: Log = None) -> bool:
    try:
        shutil.rmtree(dirpath)
        return True
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=logger,
                              mode="error",
                              ignore_flag=True)


def is_directory_exist(dirpath: str, logger: Log = None) -> bool:
    """
    Args:
        dirpath: github repository name
        logger: whether error msg should be persisted in a log file

    Returns:
        return True if the directory exists, otherwise return False
    """
    return Path(dirpath).is_dir()


def is_directory_empty(dirpath: str, logger: Log = None) -> bool:
    """
    Args:
        dirpath: github repository name
        logger: whether error msg should be persisted in a log file

    Returns:
        return True if the directory is not empty, otherwise return False
    """
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        # List directory contents
        return len(os.listdir(dirpath)) == 0
    else:
        return False
