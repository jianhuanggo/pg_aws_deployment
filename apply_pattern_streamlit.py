import click
from logging import Logger as Log
from _common import _common as _common_
from _task import _deploy_aws_website_streamlit
from _config import _config as _config_


def streamlit_project_specific(logger: Log = None):
    policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:ListAccessPointsForObjectLambda",
                "s3:GetAccessPoint",
                "s3:PutAccountPublicAccessBlock",
                "s3:ListAccessPoints",
                "s3:CreateStorageLensGroup",
                "s3:ListJobs",
                "s3:PutStorageLensConfiguration",
                "s3:ListMultiRegionAccessPoints",
                "s3:ListStorageLensGroups",
                "s3:ListStorageLensConfigurations",
                "s3:GetAccountPublicAccessBlock",
                "s3:ListAllMyBuckets",
                "s3:ListAccessGrantsInstances",
                "s3:PutAccessPointPublicAccessBlock",
                "s3:CreateJob"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::pg-web-app-0001",
                "arn:aws:s3:::pg-web-app-0001/*"
            ]
        }
    ]
    }

    from _aws import iam_role
    if policy_detail := iam_role.get_iam_policy_from_name(policy_name="iam_policy_full_access_pg-web-app-0001"):
        if policy_arn := policy_detail.get("Arn"):
            iam_role.delete_iam_policy_by_arn(policy_arn=policy_arn)

    policy_arn = iam_role.create_iam_policy(policy_name="iam_policy_full_access_pg-web-app-0001", policy_document=policy_document)

    _config = _config_.PGConfigSingleton()
    _config.config["project_iam_policy_arn"]=policy_arn
    _common_.info_logger(policy_arn, logger=logger)

@click.command()
@click.option('--project_filepath', required=True, type=str)
@click.option('--project_name', required=True, type=str)
@click.option('--aws_account_number', required=True, type=str)
@click.option('--aws_region', required=True, type=str)
def apply_pattern_streamlit(project_filepath: str,
                            project_name: str,
                            aws_account_number: str,
                            aws_region: str = "us-east-1",
                            logger: Log = None):

    _common_.info_logger(f"passing parameter project_filepath: {project_filepath}", logger=logger)
    _common_.info_logger(f"passing parameter project_name: {project_name}", logger=logger)
    _common_.info_logger(f"passing parameter aws_account_number: {aws_account_number}", logger=logger)
    _common_.info_logger(f"passing parameter aws_region:: {aws_region}", logger=logger)

    streamlit_project_specific()

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


    # project_name = "pg_wa_make_story_1"
    # project_path = "/Users/jianhuang/anaconda3/envs/pg-wa-make-story-1/pg-wa-make-story-1"

    # project_path = "/Users/jianhuang/anaconda3/envs/pg_simple_login_ui/pg_simple_login_ui"


    _deploy_aws_website_streamlit.create_deployment(project_name=project_name,
                                                    project_path=project_filepath,
                                                    aws_account_number=aws_account_number,
                                                    aws_region=aws_region)

    _common_.info_logger(f"created deployment for {project_name}", logger=logger)


if __name__ == '__main__':
    apply_pattern_streamlit()