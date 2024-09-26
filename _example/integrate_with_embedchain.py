import sys
import os


def extend_with(base_class):
    def decorator(target_class):
        class ExtendedClass(base_class, target_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        return ExtendedClass
    return decorator


def extend_classes_dynamically(base_class, target_class):
    class ExtendedClass(base_class, target_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
    return ExtendedClass


def example():

    # add root path in order to execute this from _example directory
    _root = "/Users/jianhuang/anaconda3/envs/pgtask/pgtask"
    sys.path.append(_root)
    from _common import _common as _common_

    # Need to disable telemetry in
    # /Users/jianhuang/anaconda3/envs/pgtask/pgtask/embedchain/embedchain/embedchain.py"
    # /Users/jianhuang/anaconda3/envs/pgtask/pgtask/embedchain/embedchain/embedchain.py"

    _common_.add_dirpath("/Users/jianhuang/anaconda3/envs/pgtask/pgtask/embedchain")

    from embedchain.apps import app
    os.environ["OPENAI_API_KEY"] = "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"
    elon_bot = extend_with(app.App)(type('ClassTemplate', (), {}))()
    elon_bot.add("https://en.wikipedia.org/wiki/Elon_Musk")
    elon_bot.add("https://www.forbes.com/profile/elon-musk")
    # elon_bot.add("https://www.youtube.com/watch?v=MxZpaJK74Y4")

    # Query the bot
    print(elon_bot.query("How many companies does Elon Musk run and name those?"))


if __name__ == "__main__":
    example()

