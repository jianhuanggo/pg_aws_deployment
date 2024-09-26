from openai import OpenAI
from typing import List, Dict, Tuple, Any
from _common import _common as _common_
from _config import _config as _config_
from typing import Callable
from logging import Logger as Log
import functools
import requests

"""
docs: OpenAI Function Calling Explained: Chat Completions & Assistants API https://blog.futuresmart.ai/openai-function-calling-explained-chat-completions-assistants-api
video: https://www.youtube.com/watch?v=pI1yUiNKyDA&t=1138s

"""


from _util import _util_file as _util_file_
import time


# def _chat_completion(user_message: str,
#         system_message: str="You are a helpful assistant.",
#         ):
#
#     response = openai.ChatCompletion.create(
#       model="gpt-3.5-turbo",
#       messages=[
#             {"role": "system", "content": system_message},
#             {"role": "user", "content": user_message},
#         ]
#     )
#
#     # Write the response to a file in code directory
#     return response['choices'][0]['message']['content']

def output_to_rest(logger: Log = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, str):
                if "PGError" not in result:
                    return {
                        "response": {
                            "response_code": 500,
                            "response_reason": result,
                            "response_data": None
                        }
                    }
            if not isinstance(result, List):
                result = [result]
            return {
                "response": {
                    "response_code": 200,
                    "response_reason": "",
                    "response_data": result
                }
            }
        return wrapper
    return decorator



from _api import _function
available_functions = {
    "get_order_details": _function.get_order_details,
}

functions = [
    {
        "name": "get_order_details",
        "description": "Retrieves the details of an order given its order ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "The order ID."}
            },
            "required": ["order_id"],
        },
    }
]


@_common_.exception_handlers(logger=None)
def _chat_completion(user_messages: List,
                     system_message: str="You are a helpful assistant."):

    _config = _config_.PGConfigSingleton()
    client = OpenAI(api_key=_config.config.get("openai_key"))

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_messages},
        ],
        functions=functions,
        function_call="auto"
        )
    return response.choices[0].message



@_common_.exception_handlers(logger=None)
@output_to_rest(logger=None)
def _chat_completion2(messages: List):

    _config = _config_.PGConfigSingleton()
    client = OpenAI(api_key=_config.config.get("api_key"))

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        functions=functions,
        function_call="auto"
        )
    return response.choices[0].message



@_common_.exception_handlers(logger=None)
@output_to_rest(logger=None)
def _chat_completion2_response(chat_completion_response):

    if chat_completion_response.content:
        _result = chat_completion_response.content.replace("\n", " ")
        #user_messages.append({"role": "assistant", "content": f"{_response_text}"})
        return {
            "response_type": "OPENAI API",
            "response_subtype": "content",
            "response_description": "this is a response from OpenAI API chat completion API and it is a content response",
            "response_data": _result
        }

    if chat_completion_response.function_call:
        function_name = chat_completion_response.function_call.name
        arguments = chat_completion_response.function_call.arguments
        return {
            "response_type": "OPENAI API",
            "response_subtype": "function_call",
            "response_description": "this is a response from OpenAI API chat completion API and it is a function call response",
            "response_data": {
                    "function_name": function_name,
                    "arguments": arguments
                }
        }
    return "PGError: No response from OpenAI API"




@_common_.exception_handlers(logger=None)
@output_to_rest(logger=None)
def execute_function_call(function_name, arguments):
    import importlib
    _config = _config_.PGConfigSingleton()
    module_name = _config.config.get("api_function_dir")

    def get_function_pointer(mod_name: str, func_name: str) -> Callable:
        # Dynamically import the module
        module = importlib.import_module(mod_name)

        # Retrieve the function pointer
        func_ptr = getattr(module, func_name, None)

        # Check if the function exists in the module
        if func_ptr is None:
            raise AttributeError(f"Function '{func_name}' not found in module '{mod_name}'.")

        return func_ptr

    # function = available_functions.get(function_name, None)
    function = get_function_pointer(module_name, function_name)
    if function:
        arguments = _util_file_.json_loads(arguments)
        results = function(**arguments)
        if not isinstance(results, List):
            results = [results]
        return {
            "response_type": "custom function",
            "response_description": "this is a response from custom function execute_function_call",
            "response_data": results
        }
    return f"Error: function {function_name} does not exist"


def pipeline_chat_completion(start_user_messages: List,
                             start_system_message: str) -> List:

    messages = [
        {"role": "user", "content": start_user_messages},
        {"role": "system", "content": start_system_message},
    ]

    resp = _chat_completion2(messages)

    if resp.content:
        pass
    if resp.function_call:
        func_name = resp.function_call.name
        func_arguments = resp.function_call.arguments
        _result = execute_function_call(func_name, func_arguments)
        messages.append(resp)
        messages.append({
            "role": "function",
            "name": func_name,
            "content": _result,

        })
    else:
        raise "Error: no response from OpenAI API"

    resp = _chat_completion2(messages)
    print(resp.choices[0].message)


@_common_.exception_handlers(logger=None)
def upload_file_obj(file_path: str, logger: Log = None):
    _config = _config_.PGConfigSingleton()
    client = OpenAI(api_key=_config.config.get("openai_platform_key"))
    _parameters = {
        "purpose": "assistants",
        "file": open(file_path)
    }
    return client.files.create(**_parameters)


_assistant_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Retrieves the details of an order given its order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The unique identifier of the order."
                    }
                },
                "required": ["order_id"]
            }
        }
    }
]


@_common_.exception_handlers(logger=None)
def _assistant(name: str, instructions: str, tools=None, file_ids=None, logger: Log = None):
    _config = _config_.PGConfigSingleton()
    client = OpenAI(api_key=_config.config.get("openai_platform_key"))

    _parameters = {
        "name": name,
        "instructions": instructions,
        "tools": tools,
        "model": "gpt-4-1106-preview",
    }
    if file_ids:
        _parameters["file_ids"] = file_ids

    return client.beta.assistants.create(**_parameters)


@_common_.exception_handlers(logger=None)
def submit_tool_outputs(run, thread, function_id, function_response):
    _config = _config_.PGConfigSingleton()
    client = OpenAI(api_key=_config.config.get("openai_platform_key"))

    _parameters = {
        "thread_id": thread.id,
        "run_id": run.id,
        "tool_outputs": [
            {
                "tool_call_id": function_id,
                "output": str(function_response),
            }
        ]
    }
    return client.beta.threads.runs.submit_tool_outputs(**_parameters)


@_common_.exception_handlers(logger=None)
def get_function_details(run):
    print("\nrun.required_action\n", run.required_action)
    function_name = run.required_action.submit_tool_outputs.tool_calls[0].function.name
    arguments = run.required_action.submit_tool_outputs.tool_calls[0].function.arguments
    function_id = run.required_action.submit_tool_outputs.tool_calls[0].id
    print(f"function_name: {function_name} and arguments: {arguments}")

    return function_name, arguments, function_id


def create_message_and_run(assistant, query, thread=None):
    _config = _config_.PGConfigSingleton()
    client = OpenAI(api_key=_config.config.get("openai_platform_key"))

    if not thread:
        thread = client.beta.threads.create()

    _parameters = {
        "thread_id": thread.id,
        "role": "user",
        "content": query
    }

    message = client.beta.threads.messages.create(**_parameters)

    _parameters = {
        "thread_id": thread.id,
        "assistant_id": assistant.id
    }

    run = client.beta.threads.runs.create(**_parameters)
    return run, thread


@_common_.exception_handlers(logger=None)
def pipeline_assistant(start_user_message, dirpath: str):
    _config = _config_.PGConfigSingleton()
    client = OpenAI(api_key=_config.config.get("openai_platform_key"))

    thread = client.beta.threads.create()


    #
    # _upload_files = []
    # for filepath in _util_file_.files_in_dir(dirpath):
    #     _upload_files.append(upload_file_obj(filepath))
    #
    # _upload_files_id = [file.id for file in _upload_files]

    _parameters = {
        "name": "Ecommerce bot",
        "instructions": "You are an ecommerce bot. Use the provided functions to answer questions. Synthesise answer based on provided function output and be consist",
        "tools": _assistant_tools
    }

    assistant = _assistant(**_parameters)

    _parameters = {
        "thread_id": thread.id,
        "role": "user",
        "content": start_user_message,
        "file_ids": []
    }
    message = client.beta.threads.messages.create(**_parameters)

    _parameters = {
        "thread_id": thread.id,
        "assistant_id": assistant.id
    }

    run = client.beta.threads.runs.create(**_parameters)

    while True:
        _parameters = {
            "thread_id": thread.id,
            "run_id": run.id
        }
        run = client.beta.threads.runs.retrieve(**_parameters)
        print("run status", run.status)

        if run.status == "requires_action":
            function_name, arguments, function_id = get_function_details(run)
            print(function_name, arguments, function_id)
            function_response = execute_function_call(function_name, arguments)
            run = submit_tool_outputs(run, thread, function_id, function_response)
            continue

        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            latest_message = messages.data[0]
            text = latest_message.content[0].text.value
            print(text)

            user_input = input()
            if user_input == "STOP":
                break

            run, thread = create_message_and_run(assistant=assistant, query=user_input, thread=thread)

            continue

        time.sleep(2)

















# class CacheNode:
#     past_history = {"messages": [
#         {"role": "user",
#          "content": "Base on this job description below, what is the biggest challenge someone in this "
#                     "position would face day to day?\n\n"},
#     ]
#     }
#     def __new__(cls):
#         if not hasattr(cls, 'instance'):
#             cls.instance = super(LLMCache, cls).__new__(cls)
#         return cls.instance
#
#
# class LLMCache:
#     history = CacheNode()
#
#     @classmethod
#     def run(cls, message):
#         new_user_message = {"role": "user", "content": message}
#         cls.history.past_history["messages"].append(new_user_message)
#         assistant_reply = _chat_completion2(cls.history.past_history["messages"])
#         return "Assistant:\n\n" + assistant_reply
#
#     @classmethod
#     def clean(cls):
#         cls.history.past_history = {}
