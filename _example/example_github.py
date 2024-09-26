from _connect import _connect as _connect_
from _common import _common as _common_


def example_github():
    github_obj = _connect_.get_object("github")
    _common_.info_logger(f"github object: {github_obj}")
    github_obj.git_clone("jianhuanggo/pg_deployment", "/tmp/testX000")
