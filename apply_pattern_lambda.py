import click
from logging import Logger as Log
from _common import _common as _common_
from _config import _config as _config_



@click.command()
@click.option('--project_filepath', required=True, type=str)
@click.option('--project_name', required=True, type=str)
@click.option('--aws_account_number', required=True, type=str)
@click.option('--aws_region', required=True, type=str)
def apply_pattern_lambda(project_filepath: str,
                         project_name: str,
                         aws_account_number: str,
                         aws_region: str,
                         logger: Log = None):

    _common_.info_logger(f"passing parameter project_filepath: {project_filepath}", logger=logger)
    _common_.info_logger(f"passing parameter project_name: {project_name}", logger=logger)
    _common_.info_logger(f"passing parameter aws_account_number: {aws_account_number}", logger=logger)
    _common_.info_logger(f"passing parameter aws_region:: {aws_region}", logger=logger)


    from _task import _aws_apigateway_lambda

    _aws_apigateway_lambda.create_deployment(project_name=project_name,
                                             project_path=project_filepath,
                                             aws_account_number=aws_account_number,
                                             aws_region=aws_region)




if __name__ == '__main__':
    apply_pattern_lambda()