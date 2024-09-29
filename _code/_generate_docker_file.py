from os import path
from _common import _common as _common_
from _util import _util_file as _util_file_
from _code import _generate_common as _generate_common_

@_common_.exception_handlers(logger=None)
def generate_docker_file(docker_filepath: str,
                         docker_template: str) -> bool:
    """
    Generate a lambda handler function from a given Python file.
    """


    if _util_file_.is_file_exist(docker_filepath):
        return
    else:
        _common_.info_logger(f"{docker_filepath} does not exists, generating it...")
        _util_file_.write_file(docker_filepath,
                               convert_docker_file(docker_template)
                               )
    return True

@_common_.exception_handlers(logger=None)
def convert_docker_file(template_name: str = "generic_lambda_docker_template") -> str:
    dockerfile_template = _generate_common_.get_function(template_name)
    return _generate_common_.apply_template(dockerfile_template, {})

