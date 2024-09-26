import base64
import os.path
from time import sleep

from sys import getsizeof
from inspect import currentframe
from typing import List, Dict, Union
from logging import Logger as Log
import git
from github import Github, InputGitTreeElement, GitBlob, AccessToken, InputGitAuthor, Repository, ContentFile
from _meta import _meta
from _common import _common as _common_
# from ivalidation import ivalidation
from _config import _config
from _util import _util_directory as _util_directory_


class PGObjectGithub(metaclass=_meta.PGObjectMeta):
    def __init__(self, config: _config.PGConfigSingleton = None, logger: Log = None):
        self._config = config if config else _config.PGConfigSingleton()
        self._token = base64.b64decode(self._config.config.get("git_token", "")).decode("UTF-8")

        if not self._token:
            _common_.error_logger(currentframe().f_code.co_name,
                                 f"git token is not found",
                                 logger=logger,
                                 mode="error",
                                 ignore_flag=False)

        self._user_info = InputGitAuthor(self._config.config.get("git_author", "jian huang"),
                                         self._config.config.get("git_email", "jianhuanggo@gmail.com"))

        # self._github = Github(base_url="https://github.intuit.com/api/v3",
        #                       login_or_token=self._token)

        self._github = Github(login_or_token=self._token)

    @_common_.exception_handler
    def git_get_repo(self, repository_name: str, logger: Log = None) -> Repository.Repository:
        """ get repository object based on the input repository name

        Args:
            repository_name: github repository name
            logger: whether error msg should be persisted in a log file

        Returns:

        """
        return self._github.get_repo(repository_name)

    @_common_.exception_handler
    def git_get_file_content(self,
                             repository: Repository.Repository,
                             branch: str,
                             filepath: str,
                             logger: Log = None) -> str:
        """ retrieve file content of specified filepath in particular branch in the repository

        Args:
            repository: github repository object
            branch: the branch name, for example, "master"
            filepath: the filepath, for example, terraform/wavefront.yaml
            logger: whether error msg should be persisted in a log file

        Returns:
            object serialized string form

        """

        if filepath in [_filename.path for _filename in self.git_contents_path(repository, "/".join(filepath.split("/")[:-1]))]:
            try:
                return repository.get_contents(filepath, ref=branch).decoded_content.decode("UTF-8")
            except Exception as err:
                return base64.b64decode(self.get_blob_content(repository, "master", filepath).content).decode("UTF-8")

    @_common_.exception_handler
    def git_push(self,
                 repository: Repository.Repository,
                 path_content: List[Dict],
                 commit_message: str,
                 branch_name: str,
                 file_stats: Dict = {},
                 logger: Log = None) -> None:
        """

        Args:
            repository: github repository object
            path_content: A list of map which each map object contains filename as the key, content as the value
            commit_message: the commit message
            branch_name: the branch name, for example, "master"
            file_stats: file stats used to determine whether to skip, add or update
            logger: whether error msg should be persisted in a log file

        Returns:
            None

        """

        source = repository.get_branch("master")
        repository.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)  # Create new branch from master
        if not isinstance(path_content, List):
            path_content = [path_content]
        for _each_item in path_content:
            _filepath = _each_item.get("path", None)
            _content = _each_item.get("content", None)
            _root_path = "/".join(_filepath.split("/")[:-1])
            _file_stats = file_stats
            _existing_file_in_path = set([_filename.path for _filename in self.git_contents_path(repository,
                                                                                                 _root_path)])
            for _key in _file_stats.keys():
                if _key not in _existing_file_in_path:
                    _file_stats[_key] = 0
            # if object found, update
            if _file_stats.get(_filepath, 0) == -1:
                continue
            elif _file_stats.get(_filepath, 0) > 0:
                #
                try:
                    contents = repository.get_contents(_filepath, ref=branch_name)  # Retrieve old file to get its SHA and path
                except Exception as err:
                    contents = self.get_blob_content(repository, branch_name, _filepath)
                repository.update_file(_filepath,
                                       commit_message,
                                       _content,
                                       contents.sha,
                                       branch=branch_name,
                                       author=self._user_info)
                _common_.info_logger(f"successfully committed {_filepath} to {branch_name} branch")
            # else add object
            else:
                repository.create_file(_filepath,
                                       commit_message,
                                       _content,
                                       branch=branch_name,
                                       author=self._user_info)
                _common_.info_logger(f"successfully committed {_filepath} to {branch_name} branch")
            sleep(2)

    @_common_.exception_handler
    def create_pull_request(self,
                            repository,
                            branch_name: str,
                            pr_title: str,
                            label: List = ["patch"],
                            logger: Log = None) -> None:
        """
        Args:
            repository: github repository object
            branch_name: branch name
            pr_title: pull request title
            label: pull request label
            logger: whether error msg should be persisted in a log file

        Returns:
            None
        """
        _pr_jira_ticket = self._config.config.get("jira_ticket", None)

        # if n := ivalidation.null_value_check({"pull_request_title": pr_title,
        #                                     "jira_ticket": _pr_jira_ticket}):
        #
        #     icommon.error_logger(currentframe().f_code.co_name,
        #                          f"not null variables {' '.join(n)} has null value",
        #                          logger=logger,
        #                          mode="error",
        #                          ignore_flag=False)

        _default_pr_msg_body = f"JIRA\n" \
                               f"https://jira.intuit.com/browse/{_pr_jira_ticket}\n\n" \
                               f"Purpose\n" \
                               f"Integrate alert configuration changes from operation-metrics to Zachboard Infra\n\n" \
                               f"Changes\n\n" \
                               f"Testing\n\n" \
                               f"Run unit tests\n" \
                               f"Updated unit tests\n" \
                               f"Create new unit tests on any new code\n"

        _identity_pull_request = repository.create_pull(title=pr_title,
                                                        body=_default_pr_msg_body,
                                                        head=branch_name,
                                                        base="master")

        _common_.info_logger(f"pull request created on {branch_name} branch")

        _identity_pull_request.add_to_labels(*label)

        if len(label) == 1:
            _common_.info_logger(f"Label {' '.join(label)} is added to {branch_name} branch")
        elif len(label) > 1:
            _common_.info_logger(f"Labels {' '.join(label)} are added to {branch_name} branch")


    @staticmethod
    @_common_.exception_handler
    def git_contents_path(repository: Repository.Repository,
                          path: str,
                          logger: Log = None) -> ContentFile.ContentFile:
        """fetch content of the specified path in the designated repository
        Args:
            repository: github repository object
            path: github filepath from root
            logger: whether error msg should be persisted in a log file

        Returns:
            content of filepath in ContentFile object
        """
        yield from repository.get_contents(path)

    @staticmethod
    @_common_.exception_handler
    def create_issue(repository: Repository.Repository,
                     issue_title: str,
                     issue_label: List = ["patch"],
                     logger: Log = None) -> None:
        """create github issue

        Args:
            repository: github repository object
            issue_title: issue title
            issue_label: issue label
            logger: whether error msg should be persisted in a log file

        Returns:
            None
        """
        repository.create_issue(title=issue_title, labels=issue_label)


    @staticmethod
    @_common_.exception_handler
    def get_issue(repository: Repository.Repository, issue_number: int, logger: Log = None):
        return repository.get_issue(issue_number)

    @staticmethod
    @_common_.exception_handler
    def git_merge(repository: Repository.Repository,
                  src_branch_name: str,
                  tgt_branch_name: str,
                  merge_msg: str,
                  logger: Log = None) -> None:
        """ git merge from source branch to target branch
        Args:
            repository: github repository object
            src_branch_name: source branch name
            tgt_branch_name: target branch name, for example, master
            merge_msg: commit message
            logger: whether error msg should be persisted in a log file

        Returns:
            None
        """
        repository.merge(tgt_branch_name,
                         repository.get_branch(src_branch_name).commit.sha,
                         merge_msg)
        _common_.info_logger(f"branch {src_branch_name} has been successfully merged into {tgt_branch_name}")


    @staticmethod
    @_common_.exception_handler
    def delete_branch(repository: Repository.Repository, branch_name: Union[str, List], logger: Log = None) -> None:
        """ git delete branch(es)
        Args:
            repository: github repository object
            branch_name: branch name, accept both a list of branch or single branch name
            logger: whether error msg should be persisted in a log file

        Returns:
            None
        """

        if isinstance(branch_name, str):
            branch_name = [branch_name]

        for _each_branch in branch_name:
            repository.get_git_ref(f"heads/{_each_branch}").delete()
            _common_.info_logger(f"branch {_each_branch} is deleted")

    @staticmethod
    @_common_.exception_handler
    def get_blob_content(repository: Repository.Repository,
                         branch_name: str,
                         filepath: str,
                         logger: Log = None) -> Union[None, GitBlob.GitBlob]:
        """ retrieve blob content of specified filepath in particular branch in the repository

        Args:
            repository: github repository object
            branch_name: branch name
            filepath: the filepath, for example, terraform/wavefront.yaml
            logger: whether error msg should be persisted in a log file

        Returns:
            GitBlob.GitBlob object or None
        """
        _ref = repository.get_git_ref(f"heads/{branch_name}")
        tree = repository.get_git_tree(_ref.object.sha, recursive="/" in filepath).tree
        _sha = [x.sha for x in tree if x.path == filepath]
        if not _sha:
            return None
        return repository.get_git_blob(_sha[0])


    @staticmethod
    @_common_.exception_handler
    def git_push_large_file(repository: Repository.Repository,
                            path_content: List[Dict],
                            commit_message: str,
                            branch_name: str,
                            logger: Log = None) -> None:
        """

        Args:
            repository: github repository object
            path_content: A list of map which each map object contains filename as the key, content as the value
            commit_message: the commit message
            branch_name: the branch name, for example, "master"
            logger: whether error msg should be persisted in a log file

        Returns:
            None

        """

        source = repository.get_branch("master")
        _ref = repository.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)
        _element = []
        for _each_file in path_content:
            _blob = repository.create_git_blob(_each_file.get("content"), "utf-8")
            _element.append(InputGitTreeElement(path=_each_file.get("path"),
                                                mode='100644',
                                                type='blob',
                                                sha=_blob.sha))
        _base_tree = repository.get_git_tree(sha=source.commit.sha)
        _tree = repository.create_git_tree(_element, _base_tree)
        parent = repository.get_git_commit(sha=source.commit.sha)
        commit = repository.create_git_commit(commit_message, _tree, [parent])
        _ref.edit(sha=commit.sha)

    @_common_.exception_handler
    def git_clone(self, repository_name: str, target_dirpath: str, logger: Log = None) -> None:
        """

        Args:
            repository_name: github repository name
            target_dirpath: target dirpath on localhost which file will be clone to
            logger: whether error msg should be persisted in a log file

        Returns:
            None

        """
        if not _util_directory_.is_directory_exist(target_dirpath):
            _util_directory_.create_directory(target_dirpath)

        if _util_directory_.is_directory_empty(target_dirpath):
            git.Repo.clone_from(self._github.get_repo(repository_name).clone_url, target_dirpath)
        else:
            _common_.info_logger(f"directory {target_dirpath} is not empty")

