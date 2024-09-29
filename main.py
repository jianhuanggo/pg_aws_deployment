"""
poetry add pygithub
poetry add pyyaml
poetry add pandas
poetry add pygit2
poetry add gitpython

# update poetry

poetry add boto3


Advantage:

skip cloudformation stack which often cause problems and takes longer to deploy






quick start:

For lambda/api gateway deployment or stateless app:
_example.example_lambda_deploy.example_end_2_end() -> end to end to deploy code to lambda and create api gateway resource to
                                channel the traffic to the lambda function



For ec2 deployment or stateful/web app:

_example.example_deploy_website.example_website_ec2() -> end to end to deploy website to ec2 instance



Notables:

Add security:

1) deploy EC2 instance into a private subnet, need to create a NAT gateway and load balancer
2) least privilege principle for IAM role and security group
3) use AWS WAF and AWS shield to protect the website
4) add CDN to cache the static content
5)


Add parallel deployment:

1) put jobs into DAG and figure out dependencies between jobs and create aws resource in parallel to pace the deployment



Add monitoring:



Add self healing capability:
- log past errors, fits well with LLM




"""
from _util import _util_common as _util_common_


def main_pattern_ec2_react():
    from _example import example_deployment_website, example_deployment_website_react
    # return example_deployment_website_react.example_website_ec2_react_destroy()
    return example_deployment_website_react.example_website_ec2_react(project_name="react-app",
                                                                      project_path="/Users/jianhuang/projects/ui/pg_website_react2/template/vertical_timeline")
    # return example_deployment_website.example_website_ec2_destroy()
    # return example_deployment_website.example_website_ec2()


def main_pattern_ec2_streamlit():
    from _task import _deploy_aws_website_streamlit

    project_name = "pg_wa_make_story_1"
    project_path = "/Users/jianhuang/anaconda3/envs/pg-wa-make-story-1/pg-wa-make-story-1"

    # project_path = "/Users/jianhuang/anaconda3/envs/pg_simple_login_ui/pg_simple_login_ui"


    _deploy_aws_website_streamlit.create_deployment(project_name=project_name,
                                                    project_path=project_path)


def main_pattern_apigateway_lambda():
    # from _code import _generate_lambda_function
    # _generate_lambda_function.run("/Users/jianhuang/anaconda3/envs/transcribe_5/transcribe_5")
    #
    # exit(0)


    from _task import _aws_apigateway_lambda
    ecr_repository_name = "pg_transcribe_5_test"

    lambda_function_role = f"role-auto-deployment-lambda-{_util_common_.get_random_string(6)}"
    lambda_function_name = f"lambda-{ecr_repository_name}"
    project_path = "/Users/jianhuang/anaconda3/envs/transcribe_5/transcribe_5"
    api_gateway_api_name = "MyApi_new4"
    aws_account_number = "717435123117"
    api_method = "GET"
    aws_region = "us-east-1"

    _aws_apigateway_lambda.create_deployment(ecr_repository_name=ecr_repository_name,
                                             lambda_function_role=lambda_function_role,
                                             lambda_function_name=lambda_function_name,
                                             project_path=project_path,
                                             api_gateway_api_name=api_gateway_api_name,
                                             aws_account_number=aws_account_number,
                                             api_method=api_method,
                                             aws_region=aws_region)

    exit(0)

    _aws_apigateway_lambda.destroy_deployment(lambda_function_name=lambda_function_name,
                                              api_gateway_api_name=api_gateway_api_name,
                                              aws_region=aws_region)





if __name__ == "__main__":
    print(main_pattern_ec2_streamlit())
    exit(0)
    print(main_pattern_apigateway_lambda())
