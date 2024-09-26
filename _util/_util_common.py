from typing import List, Union, Dict
import collections
import uuid
from base64 import b64decode, b64encode
from inspect import currentframe
from logging import Logger as Log
from _common import _common as _common_

def get_size(fpath: str, size_name: str = "MB", logger: Log = None) -> int:
    size = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    if size_name not in size:
        _common_.error_logger(currentframe().f_code.co_name,
                             f"size_name {size_name} not found, valid list is {size}",
                             logger=logger,
                             mode="error",
                             ignore_flag=False)
    from os import path
    return int(path.getsize(fpath) / 1024 ** size.index(size_name))

def sq_whitespace(input_string: str) -> str:
    return input_string.replace(" ", "-")


def get_random_string(string_length: int) -> str:
    return uuid.uuid4().hex[:string_length]


def string_index(string: str, pattern: str, first_char: str = None) -> int:
    _lp_ptr, _str_ptr, _lps = 1, 0, [0]
    while _str_ptr < len(pattern):
        if pattern[_str_ptr] == pattern[_lp_ptr]:
            _lps.append(_lp_ptr + 1)
            _lp_ptr, _str_ptr = _lp_ptr + 1, _str_ptr + 1
        elif _lp_ptr == 0:
            _lps.append(0)
            _str_ptr += 1
        else:
            _lp_ptr = _lps[_lp_ptr - 1]

    _lp_ptr, _str_ptr = 0, 0
    while _str_ptr < len(string):
        if first_char and string[_str_ptr] == first_char:
            return _str_ptr
        if string[_str_ptr] == pattern[_lp_ptr]:
            _lp_ptr, _str_ptr = _lp_ptr + 1, _str_ptr + 1
        elif _lp_ptr == 0:
            _str_ptr += 1
        else:
            _lp_ptr = _lps[_lp_ptr - 1]
        if _lp_ptr == len(pattern):
            return _str_ptr - _lp_ptr
    return -1


def search_name(json_obj: Union[Dict, List], name: str) -> Dict:
    _result = collections.defaultdict(list)

    def _identity_search_name(identity_obj: Union[Dict, List], identity_name: str):
        if isinstance(identity_obj, List):
            for _item in identity_obj:
                _identity_search_name(_item, identity_name)
        elif isinstance(identity_obj, Dict):
            for _ind, _val in identity_obj.items():
                _identity_search_name(_val, identity_name)
                if _ind == identity_name:
                    if _val not in _result.get(_ind, []):
                        _result[_ind].append(_val)
        else:
            return

    _identity_search_name(json_obj, name)
    return _result


@_common_.exception_handlers(logger=None)
def is_base64_encoded(input_string: str) -> bool:
    # Check if length of string is a multiple of 4
    if len(input_string) % 4 != 0: return False

    # Try to decode the string
    decoded = b64decode(input_string, validate=True)

    # Encode it again and compare with the original string
    # to ensure it was properly base64 encoded
    return b64encode(decoded).decode('utf-8') == input_string


@_common_.exception_handlers(logger=None)
def string_to_base64(input_string: str):

    # Encode the byte data to base64
    base64_encoded = b64encode(input_string.encode('utf-8'))

    # Convert the base64 bytes back to a string
    return base64_encoded.decode('utf-8')

