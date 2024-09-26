from _api import _openai


def example():
    _openai.pipeline_assistant("I want to know my order status", [])


if __name__ == "__main__":
    example()

