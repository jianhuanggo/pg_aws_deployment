from collections import defaultdict
from inspect import currentframe
from typing import Dict
from _common import _common as _common_
from _util import _util_file as _util_file_

__version__ = "0.5"


class PGConfigSingleton:
    def __new__(cls, config_loc: str = ".".join(__file__.split(".")[:-1]) + ".yaml"):
        """

        Args:
            config_loc: default configuration file location
        """
        if not hasattr(cls, "instance"):
            cls.config = defaultdict(str)
            cls.instance = super(PGConfigSingleton, cls).__new__(cls)

            try:
                if not _util_file_.is_file_empty(config_loc):
                    for _name, _val in _util_file_.yaml_load(config_loc).items():
                        cls.config[_name] = _val
            except Exception as err:
                _common_.error_logger(currentframe().f_code.co_name,
                                      err,
                                      logger=None,
                                      mode="error",
                                      ignore_flag=False)
        return cls.instance


class PGConfig:
    def __init__(self, config_loc: str = ".".join(__file__.split(".")[:-1]) + ".yaml"):
        """
        Args:
            config_loc: default configuration file location
        """
        try:
            self._config = defaultdict(str)
            if not _util_file_.is_file_empty(config_loc):
                for _name, _val in _util_file_.yaml_load(config_loc).items():
                    self._config[_name] = _val
        except Exception as err:
            _common_.error_logger(currentframe().f_code.co_name,
                                  err,
                                  logger=None,
                                  mode="error",
                                  ignore_flag=False)

    def add(self, configuration: Dict):
        """ add name value pair as configuration

        Args:
            configuration: contains a map of configuration in name value pair

        Returns:

        """
        try:
            for _name, _val in configuration.items():
                self._config[_name] = _val
        except Exception as err:
            _common_.error_logger(currentframe().f_code.co_name,
                                  err,
                                  logger=None,
                                  mode="error",
                                  ignore_flag=False)

    @property
    def config(self):
        return self._config
