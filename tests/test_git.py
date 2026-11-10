"""Git runner contracts and real repository integration tests."""

import os
import subprocess
from unittest.mock import patch

import pytest

import support_python
from support_python import git


@pytest.mark.parametrize("locks", [True, False])
def test_runner_configuration(locks):
    result = subprocess.CompletedProcess([], 0, "output", "")
    with patch.object(git.subprocess, "run", return_value=result) as run:
        assert (
            git.run_git_command(".", "status", no_optional_locks=locks, env={"GIT_TERMINAL_PROMPT": "1"}, input_data="input")
            is result
        )
    args, kwargs = run.call_args
    assert args[0] == ["git", *(["--no-optional-locks"] if locks else []), "status"]
    assert kwargs["env"] == {**os.environ, **git.DEFAULT_GIT_ENV, "GIT_TERMINAL_PROMPT": "1"}
    assert kwargs["input"] == "input"
    assert kwargs["timeout"] == 10.0
    assert kwargs["shell"] is False
    assert kwargs["encoding"] == "utf-8"


def test_return_codes():
    result = subprocess.CompletedProcess([], 1, "out", "err")
    with patch.object(git.subprocess, "run", return_value=result):
        with pytest.raises(subprocess.CalledProcessError) as error:
            git.run_git_command(".", "diff")
        assert error.value.output == "out"
        assert error.value.stderr == "err"
        assert git.run_git_command(".", "diff", allowed_returncodes=(0, 1)) is result


@pytest.mark.parametrize("error", [OSError("missing"), subprocess.TimeoutExpired("git", 1)])
def test_runner_propagates_errors(error):
    with patch.object(git.subprocess, "run", side_effect=error):
        with pytest.raises(type(error)):
            git.run_git_command(".", "status")


QUERIES = [
    (git.get_repo_root, ()),
    (git.get_head_commit, ()),
    (git.get_current_branch, ()),
    (git.branch_exists, ("main",)),
    (git.is_git_clean, ()),
    (git.has_remote, ()),
    (git.list_worktrees, ()),
    (git.get_working_tree_status, ()),
    (git.get_default_branch, ()),
    (git.get_remote_url, ()),
    (git.get_github_repo, ()),
]


@pytest.mark.parametrize("query,args", QUERIES)
@pytest.mark.parametrize(
    "error", [OSError("missing"), subprocess.TimeoutExpired("git", 1), subprocess.CalledProcessError(128, "git")]
)
def test_query_failures(query, args, error):
    with patch.object(git, "run_git_command", side_effect=error):
        assert query(".", *args) is None


@pytest.mark.parametrize("query,args", QUERIES)
def test_outside_repository(tmp_path, query, args):
    assert query(tmp_path, *args) is None


def test_status_parsing():
    expected = [{"status": "R ", "path": "new name", "original_path": "old name"}, {"status": "??", "path": "extra"}]
    assert git.parse_status_porcelain("R  old name -> new name\n?? extra\n") == expected
    assert git.parse_status_porcelain("R  new name\0old name\0?? extra\0") == expected
    assert git.parse_status_porcelain(" M file\0") == [{"status": " M", "path": "file"}]
    assert git.parse_status_porcelain("") == []


def test_worktree_parsing():
    raw = "worktree /repo with spaces\nHEAD abc\nbranch refs/heads/main\n\nworktree /other\nHEAD def\ndetached\n"
    expected = [
        {"worktree": "/repo with spaces", "HEAD": "abc", "branch": "refs/heads/main"},
        {"worktree": "/other", "HEAD": "def", "detached": ""},
    ]
    assert git.parse_worktree_porcelain(raw) == expected
    assert git.parse_worktree_porcelain(raw.replace("\n", "\0")) == expected
    assert git.parse_worktree_porcelain("") == []


def test_repository_lifecycle(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def run(*args):
        return subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *args],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )

    run("init", "-b", "main")
    assert git.get_head_commit(repo) is None
    assert git.get_current_branch(repo) == "main"
    assert git.is_git_clean(repo) is True
    assert git.has_remote(repo) is False
    assert git.branch_exists(repo, "main") is False
    file = repo / "file.txt"
    file.write_text("first", encoding="utf-8")
    assert git.is_git_clean(repo) is False
    assert git.get_working_tree_status(repo) == [{"status": "??", "path": "file.txt"}]
    assert git.get_working_tree_status(repo, untracked=False) == []
    run("add", ".")
    run("commit", "-m", "Initial commit")
    assert git.is_git_clean(repo) is True
    assert git.get_repo_root(repo) == repo.resolve()
    head = git.get_head_commit(repo)
    assert len(head) == 40
    assert head.startswith(git.get_head_commit(repo, short=True))
    run("branch", "topic")
    assert git.branch_exists(repo, "topic") is True
    assert git.branch_exists(repo, "missing") is False
    run("remote", "add", "origin", str(tmp_path / "local-remote"))
    assert git.has_remote(repo) is True
    assert git.has_remote(repo, "other") is False
    run("mv", "file.txt", "new name.txt")
    assert git.get_working_tree_status(repo) == [{"status": "R ", "path": "new name.txt", "original_path": "file.txt"}]
    run("commit", "-m", "Renamed file")
    file = repo / "new name.txt"
    file.write_text("changed", encoding="utf-8")
    assert git.is_git_clean(repo) is False
    assert git.get_working_tree_status(repo)[0]["status"] == " M"
    run("worktree", "add", str(tmp_path / "second"), "topic")
    assert len(git.list_worktrees(repo)) == 2
    run("checkout", "--detach")
    assert git.get_current_branch(repo) == "(detached)"
    assert any("detached" in item for item in git.list_worktrees(repo))


def test_public_exports():
    for name in git.__all__:
        assert getattr(support_python, name) is getattr(git, name)


def test_untracked_arrow_is_not_a_rename():
    assert git.parse_status_porcelain("?? name -> other\n") == [{"status": "??", "path": "name -> other"}]


def test_nul_worktree_preserves_newlines_in_path():
    assert git.parse_worktree_porcelain("worktree /repo\n\0HEAD abc\0\0") == [{"worktree": "/repo\n", "HEAD": "abc"}]


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/owner/name.git\n", ("owner", "name")),
        ("https://github.com/owner/name/", ("owner", "name")),
        ("git@github.com:owner/support.python.git", ("owner", "support.python")),
        ("ssh://git@github.com/owner/name", ("owner", "name")),
        ("https://gitlab.com/owner/name.git", None),
        ("", None),
    ],
)
def test_github_remote_parsing(url, expected):
    assert git.parse_github_remote(url) == expected


def test_remote_queries(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def run(*args):
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *args], cwd=repo, check=True)

    run("init", "-q", "-b", "trunk")
    assert git.get_remote_url(repo) is None
    assert git.get_github_repo(repo) is None
    run("commit", "-q", "--allow-empty", "-m", "Initial commit")
    run("remote", "add", "origin", "git@github.com:owner/name.git")
    run("remote", "add", "mirror", "https://gitlab.com/owner/name.git")
    assert git.get_remote_url(repo) == "git@github.com:owner/name.git"
    assert git.get_github_repo(repo) == ("owner", "name")
    assert git.get_github_repo(repo, "mirror") is None
    assert git.get_default_branch(repo) is None
    run("update-ref", "refs/remotes/origin/trunk", "HEAD")
    run("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
    assert git.get_default_branch(repo) == "trunk"
    assert git.get_default_branch(repo, "mirror") is None
