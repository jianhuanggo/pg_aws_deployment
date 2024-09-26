import subprocess
from typing import List, Union
from inspect import currentframe
from logging import Logger as Log
from _common import _common as _common_


@_common_.exception_handler
def run_command_simple(command: List, logger: Log=None):
    try:
        # Execute the command and capture the output
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        _common_.info_logger(f"Command output: {result.stdout}")

    except subprocess.CalledProcessError as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"An error occurred while executing the command. \n"
                              f"Error code: {err.returncode} \n"
                              f"Error message: {err.stderr}",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

@_common_.exception_handler
def run_command_progress(command: Union[str, List], logger: Log=None):
    try:
        _common_.info_logger(f"running {command} ...")
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                _common_.info_logger(output.strip())

        # stdout = subprocess.PIPE, stderr = subprocess.STDOUT, text = True)

        _common_.info_logger(process.stdout)
        _common_.info_logger(process.stderr)
        return process
    except subprocess.CalledProcessError as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"An error occurred while executing the command. \n"
                              f"Error code: {err.returncode} \n"
                              f"Error message: {err.stderr}",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)