import os
import functools
from jinja2 import Template
from time import sleep
from _common import _common as _common_
from _util import _util_common as _util_common_


_WAIT_TIME_ = 4


def deployment(cloud_type="aws"):
    def decorator_deployment(func):
        @functools.wraps(func)
        def wrapper_deployment(*args, **kwargs):
            # Log or handle cloud deployment details
            if func.__doc__ and 'not implemented' in func.__doc__.lower():
                print(f"Function '{func.__name__}' is not yet implemented.")
            print(f"Deploying to {cloud_type} cloud")
            result = func(*args, **kwargs)
            return result
        return wrapper_deployment
    return decorator_deployment


lambda_template = """
def lambda_handler(event, context):
    response = main(event, context)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(response)
    }
"""


def generate_lambda_template():
    # Define the Jinja2 template

    # Render the template
    template = Template(lambda_template)
    rendered_template = template.render()

    # Save the rendered template to a file
    with open('lambda_function.py', 'w') as file:
        file.write(rendered_template)


# Call the function to generate and save the template


@deployment(cloud_type="aws")
def deployment(ecr_repository_name: str,
               aws_account_number: str,
               aws_region: str,
               project_path: str,
               api_gateway_api_name: str):

    """This function is implemented for aws."""

    lambda_function_role = f"role-auto-deployment-lambda-{_util_common_.get_random_string(6)}"
    lambda_function_name = f"lambda-{ecr_repository_name}"

    from _deployment.deploy_ec2 import deploy_ec2
    deploy_ec2.run(ecr_repository_name,
                   aws_account_number,
                   aws_region,
                   project_path,
                   lambda_function_name,
                   lambda_function_role
                   )


if __name__ == "__main__":

    current_directory = os.getcwd()
    project_directory = current_directory.split("/")[-1]
    _common_.info_logger(deployment(project_directory,
                                    "717435123117",
                                    "us-east-1",
                                    os.path.abspath(current_directory),
                                    "MyApi"
                                    )
                         )