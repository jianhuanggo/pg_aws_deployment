from _util import _util_file as _util_file_
from _common import _common as _common_



def generic_lambda_handler():

    template = """from _common import _common as _common_
from _util import _util_file as _util_file_
{{ from_imports }}
    
def lambda_handler(event, context):
    
{{ declare_variables }}
    try:
        query_params = event.get('queryStringParameters', {})
        print(query_params)
        if query_params:
{{ variables_extraction }}

{{ check_variables }}
            return {
                    'statusCode': 404,
                    'headers': {
                        'Access-Control-Allow-Headers': '*',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': _util_file_.json_dumps("input variable is missing")
            }
        
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': _util_file_.json_dumps({{ return_statement }})
        }

    except Exception as err:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': _util_file_.json_dumps(f"Something is error while processing, {err}")
        }
    """
    return template


def generic_lambda_docker_template():
    template = """FROM public.ecr.aws/lambda/python:3.11
RUN yum update -y
RUN yum install vi tar xz wget -y
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["lambda_function.lambda_handler"]

    """

    return template


def generic_streamlit_docker_template():
    template = """FROM python:3.11-slim
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt
RUN pip install streamlit

# Expose port 8501 for the Streamlit app
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
"""
    return template