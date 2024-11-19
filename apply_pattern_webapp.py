import click
from logging import Logger as Log
from _common import _common as _common_
from _config import _config as _config_



@click.command()
@click.option('--project_filepath', required=True, type=str)
@click.option('--project_name', required=True, type=str)
@click.option('--aws_account_number', required=True, type=str)
@click.option('--aws_region', required=True, type=str)
def apply_pattern_webapp(project_filepath: str,
                         project_name: str,
                         aws_account_number: str,
                         aws_region: str,
                         logger: Log = None):

    _common_.info_logger(f"passing parameter project_filepath: {project_filepath}", logger=logger)
    _common_.info_logger(f"passing parameter project_name: {project_name}", logger=logger)
    _common_.info_logger(f"passing parameter aws_account_number: {aws_account_number}", logger=logger)
    _common_.info_logger(f"passing parameter aws_region:: {aws_region}", logger=logger)

    kms_alias_name = "alias/ec2-custom-kms-key-5"
    from _aws import _kms
    kms_id = ""
    kms_arn = ""
    if not _kms.check_alias_exists(kms_alias_name):
        kms_id, kms_arn = _kms.create_kms_keys()
        if kms_id:
            _kms.create_kms_key_alias(alias_name=kms_alias_name,
                                      key_id=kms_id)
    else:
        kms_arn = _kms.get_key_alias_arn(alias_name="alias/ec2-custom-kms-key-5")

    _config = _config_.PGConfigSingleton()
    # _config.config["kms_arn"] = "arn:aws:kms:us-east-1:515966537984:key/9ef67a77-0c8b-4a98-a25d-662c29f7017c"
    _config.config["kms_arn"] = kms_arn
    print(kms_id, kms_arn)


    from _example import example_deployment_website, example_deployment_website_react
    # return example_deployment_website_react.example_website_ec2_react_destroy()
    return example_deployment_website_react.example_website_ec2_react(project_name="react-app",
                                                                      project_path="/Users/jianhuang/projects/ui/pg_website_react2/template/vertical_timeline",
                                                                      aws_account_number=aws_account_number,
                                                                      aws_region=aws_region
                                                                      )
    # return example_deployment_website.example_website_ec2_destroy()
    # return example_deployment_website.example_website_ec2()

if __name__ == '__main__':
    apply_pattern_webapp()