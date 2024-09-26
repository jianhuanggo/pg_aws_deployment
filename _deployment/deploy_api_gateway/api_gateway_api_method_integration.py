import boto3
from logging import Logger as Log
from typing import Union, List
from inspect import currentframe
import subprocess
import json
from time import sleep
from boto3 import client
import base64
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from _common import _common as _common_
from _engine import _engine as _engine_
from _util import _util_common as _util_common
import boto3

_WAIT_TIME_ = 4


def get_api_gateway_integration(aws_region: str,
                                api_gateway_api_id: str,
                                resource_id: str,
                                http_method='GET'
                                ) -> Union[str, None]:
    """Checks if an api Gateway integration exists.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.

    Returns:
        True if the integration exists, False otherwise.

    """
    try:

        # Attempt to retrieve the integration configuration
        apigateway_client = boto3.client('apigateway', region_name=aws_region)

        # apigateway_client = boto3.client('apigatewayv2')
        all_integrations = []
        next_token = None
        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method,
        }

        response = apigateway_client.get_integration(**_parameters)
        print(response)
        print(f"HTTP method '{http_method}' exists for resource ID '{resource_id}'.")
        return response
        #
        # while True:
        #     try:
        #         # Fetch integrations with or without the NextToken
        #         if next_token:
        #             response = apigateway_client.get_integrations(
        #                 ApiId=api_gateway_api_id,
        #                 NextToken=next_token
        #             )
        #         else:
        #             _paremeters = {
        #                 "ApiId": api_gateway_api_id
        #             }
        #             print(_paremeters)
        #             response = apigateway_client.get_integrations(**_paremeters)
        #         print(response)
        #         exit(0)
        #
        #         # Append fetched integrations to the list
        #         all_integrations.extend(response.get('Items', []))
        #
        #         # Update the next_token for the next iteration
        #         next_token = response.get('NextToken')
        #
        #         # If there's no next_token, exit the loop
        #         if not next_token:
        #             break
        #
        #     except ClientError as e:
        #         # Handle client errors (e.g., authentication issues, permissions)
        #         print(f"Failed to get integrations: {e.response['Error']['Message']}")
        #         break
        #     except Exception as e:
        #         # Handle any other exceptions
        #         print(f"Unexpected error: {e}")
        #         break
        #
        # return all_integrations
        # _parameters = {
        #     "restApiId": api_gateway_api_id,
        #     "resourceId": resource_id,
        #     "httpMethod": http_method
        # }
        # print("AAAA##@@#")
        # print(_parameters)
        # exit(0)
        # integration = apigateway_client.get_integration(**_parameters)
        # print(integration)
        # _common_.info_logger(f"Integration for HTTP method '{http_method}' exists for resource ID '{resource_id}'.")
        # return True

    except apigateway_client.exceptions.NotFoundException:
        _common_.info_logger(f"Integration for HTTP method integration '{http_method}' does not exist for resource ID '{resource_id}'.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)

    return None

def delete_api_gateway_integration(aws_region: str,
                                   api_gateway_api_id: str,
                                   resource_id: str,
                                   http_method: str) -> bool:
    """deletes an existing integration in an API Gateway resource.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the integration
        http_method: the http method

    Returns:
        True if the integration exists other False.

    """

    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method
        }
        apigateway_client.delete_integration(**_parameters)
        _common_.info_logger(f"Integration for HTTP method '{http_method}' deleted successfully for resource ID '{resource_id}'.")
        return True

    except apigateway_client.exceptions.NotFoundException:
        _common_.info_logger(f"Integration for HTTP method integration  '{http_method}' not found for resource ID '{resource_id}'.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False


def create_api_gateway_integration(aws_region: str,
                                   api_gateway_api_id: str,
                                   resource_id: str,
                                   http_method: str,
                                   aws_account_number: str,
                                   lambda_function_name: str):

    """creates a new integration in an API Gateway resource.

    Args:
        aws_region: aws region
        api_gateway_api_id: The ID of the API Gateway API
        resource_id: the id of the resource that contains the integration
        http_method: the http method
        aws_account_number: the aws account number
        ecr_repository_name: the name of the repository containing the Lambda function.
        lambda_function_name: the name of the Lambda function.

    Returns:
        True if the integration exists other False.

    """

    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)

        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method,
            "type": "AWS_PROXY",
            "integrationHttpMethod": "POST",
            "uri": f"arn:aws:apigateway:{aws_region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{aws_region}:{aws_account_number}:function:{lambda_function_name}/invocations",
            "credentials": f"arn:aws:iam::{aws_account_number}:role/role-api-gateway-ex"
        }
        apigateway_client.put_integration(**_parameters)
        _common_.info_logger(f"Integration for HTTP method '{http_method}' created successfully for resource ID '{resource_id}'.")
        return True

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False


def run(ecr_repository_name: str,
        aws_region: str,
        aws_account_number: str = None,
        project_path: str = None,
        lambda_function_name: str = None,
        lambda_function_role: str = None,
        api_gateway_api_name: str = None) -> None:

    # obtain the API Gateway API ID
    from _deployment.deploy_api_gateway import api_gateway_api_id
    api_gateway_api_id = api_gateway_api_id.get_api_gateway_id(aws_region, api_gateway_api_name)

    # obtain the API Gateway root resource ID
    from _deployment.deploy_api_gateway import api_gateway_api_root_id
    api_gateway_root_res_id = api_gateway_api_root_id.get_api_gateway_root_id(aws_region, api_gateway_api_id)

    # obtain the resource ID
    from _deployment.deploy_api_gateway import api_gateway_api_resource
    resource_id = api_gateway_api_resource.get_api_gateway_resource_id(aws_region, api_gateway_api_id, lambda_function_name)

    api_gateway_integration = get_api_gateway_integration(aws_region, api_gateway_api_id, resource_id, "GET")

    if api_gateway_integration:
        # Resource exists, delete it
        if delete_api_gateway_integration(aws_region, api_gateway_api_id, resource_id, "GET"):
            # Wait before creating the new resource to ensure deletion has propagated
            sleep(_WAIT_TIME_)

    # Create the new resource
    api_integration = create_api_gateway_integration(aws_region,
                                                     api_gateway_api_id,
                                                     resource_id,
                                                     "GET",
                                                     aws_account_number,
                                                     lambda_function_name
                                                     )
    print(api_integration)
    sleep(_WAIT_TIME_)

