from typing import Union, List
from logging import Logger as Log
from inspect import currentframe
from time import sleep
from boto3 import client
from _common import _common as _common_
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

_WAIT_TIME_ = 4


@_common_.aws_client_handle_exceptions()
def aws_client(service_name: str, aws_region: str):
    return boto3.client(service_name, region_name=aws_region)


@_common_.aws_client_handle_exceptions()
def api_gateway_get_name(api_gateway_name: str,
                         aws_region: str = "us-east-1",
                         logger: Log = None
                         ) -> Union[str, None]:
    """check whether API Gateway name exists.

    Args:
        aws_region: aws region
        api_gateway_name: the name of the api gateway api
        logger: logger object

    Returns:
        the id of the resource if it exists otherwise None

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    # Get the list of all APIs
    response = apigateway_client.get_rest_apis()

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    api_gateway_api_id = [item.get("id") for item in response.get("items") if api_gateway_name == item.get("name")]
    return api_gateway_api_id[0] if len(api_gateway_api_id) > 0 else None


@_common_.aws_client_handle_exceptions()
def api_gateway_delete_by_name(api_gateway_name: str,
                               aws_region: str = "us-east-1",
                               logger: Log = None
                               ) -> bool:
    """delete the API Gateway by name

    Args:
        aws_region: aws region
        api_gateway_name: the name of the api gateway api
        logger: logger object

    Returns:
        True if the operation is successful otherwise False

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    if api_id := api_gateway_get_name(api_gateway_name=api_gateway_name,  aws_region=aws_region):
        response = apigateway_client.delete_rest_api(restApiId=api_id)

        if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
            _common_.error_logger(currentframe().f_code.co_name,
                                  f"operation failed, reason response code is not 200",
                                  logger=logger,
                                  mode="error",
                                  ignore_flag=False)

        _common_.info_logger(f"API {api_gateway_name} with ID {api_id} has been deleted")
    return True


# @_common_.aws_client_handle_exceptions()
def api_gateway_create_by_name(api_gateway_name: str,
                               aws_region: str = "us-east-1",
                               logger: Log = None
                               ) -> str:
    """delete the API Gateway by name

    Args:
        aws_region: aws region
        api_gateway_name: the name of the api gateway api
        logger: logger object

    Returns:
        True if the operation is successful otherwise False

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    # Check if API with the same name already exists
    if api_id := api_gateway_get_name(api_gateway_name, aws_region):
        _common_.info_logger(f"API {api_gateway_name} already exists with ID {api_id}")
        return api_id

    # Create a new API
    _parameter = {
        "name": api_gateway_name,
        "description": "'resource created via api",
        "version": "1.0.0",
        # "apiKeySource": "HEADER"
    }
    response = apigateway_client.create_rest_api(**_parameter)
    # from pprint import pprint
    # pprint(response)
    # exit(0)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Created API '{api_gateway_name}' with ID: {api_id}")
    return response.get("id")


@_common_.aws_client_handle_exceptions()
def api_gateway_get_root_resource(api_gateway_api_id: str,
                                  aws_region: str = "us-east-1",
                                  logger: Log = None
                                  ) -> Union[str, None]:
    """check whether API Gateway name exists.
    Args:
        api_gateway_api_id: the id of the api gateway api
        aws_region: aws region
        logger: logger object
    Returns:
        the id of the resource if it exists otherwise None
    """

    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    # Get the list of all APIs
    response = apigateway_client.get_resources(restApiId=api_gateway_api_id)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    sleep(_WAIT_TIME_)
    # Get the Root Resource ID

    api_gateway_root_res_id = [item.get("id") for item in response.get("items") if item.get("path") == '/']
    return api_gateway_root_res_id[0] if len(api_gateway_root_res_id) > 0 else None


@_common_.aws_client_handle_exceptions()
def get_api_gateway_resource_id(api_gateway_api_id: str,
                                lambda_function_name: str,
                                aws_region: str = "us-east-1",
                                logger: Log = None
                                ) -> Union[str, None]:

    """Checks if an API Gateway resource exists.

    Args:
        api_gateway_api_id: the id of the api gateway api.
        lambda_function_name: the name of the lambda function (used as the resource path)
        aws_region: aws region
        logger: logger object

    Returns:
        the id of the resource if it exists, None otherwise.

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    # Get the list of resources
    response = apigateway_client.get_resources(restApiId=api_gateway_api_id)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    api_gateway_res_id = [item.get("id") for item in response.get("items") if item.get("pathPart") == lambda_function_name]
    return api_gateway_res_id[0] if len(api_gateway_res_id) > 0 else None


@_common_.aws_client_handle_exceptions()
def delete_api_gateway_resource(api_gateway_api_id: str,
                                resource_id: str,
                                aws_region: str = "us-east-1",
                                logger: Log = None
                                ):
    """Deletes an API Gateway resource.

    Args:
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource to be deleted
        aws_region: aws region
        logger: logger object

    Returns:
        True if the resource was deleted successfully, False otherwise.

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    _parameter = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id
    }
    response = apigateway_client.delete_resource(**_parameter)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Resource with ID '{resource_id}' deleted successfully.")
    return True


@_common_.aws_client_handle_exceptions()
def create_api_gateway_resource(api_gateway_api_id: str,
                                api_gateway_root_res_id: str,
                                lambda_function_name: str,
                                aws_region: str = "us-east-1",
                                logger: Log = None
                                ) -> Union[str, None]:
    """Creates a new API Gateway resource.

    Args:
        api_gateway_api_id: the id of the api gateway api.
        api_gateway_root_res_id: the id of the root resource in the api gateway.
        lambda_function_name: the name of the lambda function (used as the resource path)
        aws_region: aws region
        logger: logger object

    Returns:
        the id of the newly created resource.

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    # Create the new resource
    _parameters = {
        "restApiId": api_gateway_api_id,
        "parentId": api_gateway_root_res_id,
        "pathPart": lambda_function_name
    }
    response = apigateway_client.create_resource(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Resource '{lambda_function_name}' created successfully")
    return response.get("id")


# @_common_.aws_client_handle_exceptions()
@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def get_api_gateway_method(api_gateway_api_id: str,
                           resource_id: str,
                           http_method: str,
                           aws_region: str = "us-east-1",
                           logger: Log = None
                           ) -> Union[str, None]:

    """ checks if an api gateway method exists.

    Args:
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the method.
        http_method: the http method
        aws_region: aws region
        logger: logger object

    Returns:
        the id of the resource if it exists, None otherwise.

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)
    # try:

        # Get the list of method

    _parameters = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id,
        "httpMethod": http_method
    }
    response = apigateway_client.get_method(**_parameters)
    # except apigateway_client.exceptions.NotFoundException:
    #     print("AAAA")
    #     _common_.info_logger(f"HTTP method '{http_method}' does not exist for resource ID '{resource_id}'.")
    # except NoCredentialsError:
    #     _common_.info_logger("Error: No AWS credentials found.")
    # except PartialCredentialsError:
    #     _common_.info_logger("Error: Incomplete AWS credentials found.")
    # except ClientError as err:
    #     _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    # except Exception as err:
    #     _common_.error_logger(currentframe().f_code.co_name,
    #                           err,
    #                           logger=None,
    #                           mode="error",
    #                           ignore_flag=False)

    print(response)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    return response


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def delete_api_gateway_method(api_gateway_api_id: str,
                              resource_id: str,
                              http_method: str,
                              aws_region: str = "us-east-1",
                              logger: Log = None
                              ) -> bool:

    """ deletes an api gateway method if it exists.

    Args:
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the method.
        http_method: the http method
        aws_region: aws region
        logger: logger object

    Returns:
        True if it is successful otherwise False.

    """

    apigateway_client = boto3.client('apigateway', region_name=aws_region)
    _parameters = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id,
        "httpMethod": http_method
    }
    response = apigateway_client.delete_method(**_parameters)
    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    _common_.info_logger(f"Method '{http_method}' deleted successfully for resource ID {resource_id}")
    return True


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def create_api_gateway_method(api_gateway_api_id: str,
                              resource_id: str,
                              http_method='GET',
                              aws_region: str = "us-east-1",
                              logger: Log = None
                              ) -> bool:

    """creates an api gateway method.

    Args:
        api_gateway_api_id: the id of the api gateway api
        resource_id: the id of the resource that contains the method
        http_method: the http method
        aws_region: aws region
        logger: logger object

    Returns:
        True if it is successful otherwise False.

    """

    apigateway_client = boto3.client('apigateway', region_name=aws_region)
    _parameters = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id,
        "httpMethod": http_method,
        "authorizationType": "NONE",
        "apiKeyRequired": False
    }
    response = apigateway_client.put_method(**_parameters)
    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Method '{http_method}' created successfully for resource ID {resource_id}")
    return True


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def get_api_gateway_integration(api_gateway_api_id: str,
                                resource_id: str,
                                http_method='GET',
                                aws_region: str = "us-east-1",
                                logger: Log = None
                                ) -> Union[str, None]:
    """Checks if an api Gateway integration exists.

    Args:
        api_gateway_api_id: the id of the api gateway api
        resource_id: the id of the resource that contains the method
        http_method: the http method
        aws_region: aws region
        logger: logger object

    Returns:
        True if the integration exists, False otherwise.

    """

    apigateway_client = boto3.client('apigateway', region_name=aws_region)
    # apigateway_client = boto3.client('apigatewayv2')


    _parameters = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id,
        "httpMethod": http_method,
    }
    response = apigateway_client.get_integration(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Method '{http_method}' created successfully for resource ID {resource_id}")
    return response


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def delete_api_gateway_integration(api_gateway_api_id: str,
                                   resource_id: str,
                                   http_method: str,
                                   aws_region: str = "us-east-1",
                                   logger: Log = None
                                   ) -> bool:
    """ deletes an existing integration in an API Gateway resource.

    Args:
        api_gateway_api_id: the id of the api gateway api
        resource_id: the id of the resource that contains the integration
        http_method: the http method
        aws_region: aws region
        logger: logger object

    Returns:
        True if the integration exists other False.

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    _parameters = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id,
        "httpMethod": http_method
    }
    response = apigateway_client.delete_integration(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Integration for HTTP method '{http_method}' deleted successfully for resource ID {resource_id}")
    return True


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def create_api_gateway_integration(api_gateway_api_id: str,
                                   resource_id: str,
                                   http_method: str,
                                   aws_account_number: str,
                                   lambda_function_name: str,
                                   aws_region: str = "us-east-1",
                                   logger: Log = None
                                   ) -> bool:
    """ creates a new integration in an api Gateway resource

    Args:
        api_gateway_api_id: The ID of the API Gateway API
        resource_id: the id of the resource that contains the integration
        http_method: the http method
        aws_account_number: the aws account number
        lambda_function_name: the name of the Lambda function
        aws_region: aws region
        logger: logger object

    Returns:
        true if the integration exists other false.

    """

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
    response = apigateway_client.put_integration(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Integration for HTTP method '{http_method}' created successfully for resource ID {resource_id}")

    return True


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def get_api_gateway_method_response(api_gateway_api_id: str,
                                    resource_id: str,
                                    http_method: str,
                                    status_code: str,
                                    aws_region: str = "us-east-1",
                                    logger: Log = None
                                    ) -> Union[str, None]:
    """ checks if an api gateway method response exists

    Args:
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the method.
        http_method: the http method
        status_code: the status code
        aws_region: aws region
        logger: logger object

    Returns:
        true if the integration exists, false otherwise.

    """

    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    _parameters = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id,
        "httpMethod": http_method,
        "statusCode": status_code
    }
    response = apigateway_client.get_method_response(**_parameters)
    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    print(response)
    return response


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def delete_api_gateway_method_response(api_gateway_api_id: str,
                                       resource_id: str,
                                       http_method: str,
                                       status_code: str,
                                       aws_region: str,
                                       logger: Log = None
                                       ) -> bool:

    """ deletes an existing api_gateway method response in an api gateway resource

    Args:
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the integration
        http_method: the http method
        status_code: the status code
        aws_region: aws region
        logger: logger object

    Returns:
        True if the integration exists other False.

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)
    _parameters = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id,
        "httpMethod": http_method,
        "statusCode": status_code
    }
    response = apigateway_client.delete_method_response(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                          f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Deleted existing method response for {http_method} {status_code}")
    return True


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def create_api_gateway_method_response(api_gateway_api_id,
                                       resource_id: str,
                                       http_method: str,
                                       status_code: str,
                                       aws_region: str,
                                       logger: Log = None
                                       ) -> bool:
    """ creates a new api gateway method response

    Args:
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the integration
        http_method: the http method
        status_code: the status code
        aws_region: aws region
        logger: logger object

    Returns:
        True if the integration exists other False.

    """
    # Create a new method response
    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    _parameters = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id,
        "httpMethod": http_method,
        "statusCode": status_code,
        "responseParameters": {},
        "responseModels": {'application/json': 'Empty'}
    }

    response = apigateway_client.put_method_response(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                          f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Created new method response for {http_method} {status_code}")
    return True


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client("apigateway", "us-east-1").exceptions.NotFoundException)
def create_api_gateway_deployment(api_gateway_api_id: str,
                                  api_stage_name: str,
                                  aws_region: str,
                                  logger: Log = None
                                  ) -> bool:

    """ creates an api gateway deployment

    Args:
        api_gateway_api_id: the id of the api gateway api
        api_stage_name: the name of the stage
        aws_region: aws region
        logger: logger object

    Returns:
        true if api gateway deployment is created

    """

    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    _parameters = {
        "restApiId": api_gateway_api_id,
        "stageName": api_stage_name,
        "description": "Deploying new method to prod"
    }
    response = apigateway_client.create_deployment(**_parameters)
    sleep(_WAIT_TIME_)

    if response.get("ResponseMetadata").get("HTTPStatusCode") // 100 != 2:
        _common_.error_logger(currentframe().f_code.co_name,
                          f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"api gateway deployment created successfully for {api_gateway_api_id}")
    return True







