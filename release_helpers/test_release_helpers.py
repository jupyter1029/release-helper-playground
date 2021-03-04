import json
import os
import os.path as osp
import shlex
import shutil
import sys
from pathlib import Path
from unittest.mock import call
from unittest.mock import patch

from click.testing import CliRunner
from pytest import fixture

from release_helpers import __main__ as main

PR_ENTRY = "Mention the required GITHUB_ACCESS_TOKEN [#1](https://github.com/executablebooks/github-activity/pull/1) ([@consideRatio](https://github.com/consideRatio))"

CHANGELOG_ENTRY = f"""
# master@{{2019-09-01}}...master@{{2019-11-01}}

([full changelog](https://github.com/executablebooks/github-activity/compare/479cc4b2f5504945021e3c4ee84818a10fabf810...ed7f1ed78b523c6b9fe6b3ac29e834087e299296))

## Merged PRs

* defining contributions [#14](https://github.com/executablebooks/github-activity/pull/14) ([@choldgraf](https://github.com/choldgraf))
* updating CLI for new tags [#12](https://github.com/executablebooks/github-activity/pull/12) ([@choldgraf](https://github.com/choldgraf))
* fixing link to changelog with refs [#11](https://github.com/executablebooks/github-activity/pull/11) ([@choldgraf](https://github.com/choldgraf))
* adding contributors list [#10](https://github.com/executablebooks/github-activity/pull/10) ([@choldgraf](https://github.com/choldgraf))
* some improvements to `since` and opened issues list [#8](https://github.com/executablebooks/github-activity/pull/8) ([@choldgraf](https://github.com/choldgraf))
* Support git references etc. [#6](https://github.com/executablebooks/github-activity/pull/6) ([@consideRatio](https://github.com/consideRatio))
* adding authentication information [#2](https://github.com/executablebooks/github-activity/pull/2) ([@choldgraf](https://github.com/choldgraf))
* {PR_ENTRY}

## Contributors to this release

([GitHub contributors page for this release](https://github.com/executablebooks/github-activity/graphs/contributors?from=2019-09-01&to=2019-11-01&type=c))

[@betatim](https://github.com/search?q=repo%3Aexecutablebooks%2Fgithub-activity+involves%3Abetatim+updated%3A2019-09-01..2019-11-01&type=Issues) | [@choldgraf](https://github.com/search?q=repo%3Aexecutablebooks%2Fgithub-activity+involves%3Acholdgraf+updated%3A2019-09-01..2019-11-01&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Aexecutablebooks%2Fgithub-activity+involves%3AconsideRatio+updated%3A2019-09-01..2019-11-01&type=Issues)
"""


@fixture
def git_repo(tmp_path):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)

    run = main.run
    run("git init")
    run("git checkout -b foo")
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("dist/*\nbuild/*", encoding="utf-8")
    run("git add .")
    run('git commit -m "foo"')
    run("git tag v0.0.1")
    run(f"git remote add upstream {tmp_path}")
    run('git config user.name "snuffy"')
    run('git config user.email "snuffy@sesame.com"')

    yield tmp_path
    os.chdir(prev_dir)


def create_python_package(git_repo):
    setuppy = git_repo / "setup.py"
    setuppy.write_text(
        """
import setuptools
import os

setup_args = dict(
    name="foo",
    version="0.0.1",
    url="foo url",
    author="foo author",
    author_email="foo email",
    py_modules=["foo"],
    description="foo package",
    long_description="long_description",
    long_description_content_type="text/markdown",
    zip_safe=False,
    include_package_data=True,
)
if __name__ == "__main__":
    setuptools.setup(**setup_args)
""",
        encoding="utf-8",
    )

    tbump = git_repo / "tbump.toml"
    tbump.write_text(
        r"""
[version]
current = "0.0.1"
regex = '''
  (?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)
  ((?P<channel>a|b|rc|.dev)(?P<release>\d+))?
'''

[git]
message_template = "Bump to {new_version}"
tag_template = "v{new_version}"

[[file]]
src = "setup.py"
""",
        encoding="utf-8",
    )

    foopy = git_repo / "foo.py"
    foopy.write_text('print("hello, world!")', encoding="utf-8")

    changelog = git_repo / "CHANGELOG.md"
    changelog.write_text(
        f"""
# Changelog

{main.START_MARKER}
{main.END_MARKER}
""",
        encoding="utf-8",
    )

    pyproject = git_repo / "pyproject.toml"
    pyproject.write_text(
        """
[build-system]
requires = ["setuptools>=40.8.0", "wheel"]
build-backend = "setuptools.build_meta"
""",
        encoding="utf-8",
    )

    readme = git_repo / "README.md"
    readme.write_text("Hello from foo project", encoding="utf-8")

    main.run("git add .")
    main.run('git commit -m "initial python package"')
    return git_repo


def create_npm_package(git_repo):
    main.run("npm init -y")
    main.run("git add .")
    main.run('git commit -m "initial npm package"')
    return git_repo


@fixture
def py_package(git_repo):
    pkg = create_python_package(git_repo)
    main.run("git checkout -b bar foo")
    return pkg


@fixture
def npm_package(git_repo):
    pkg = create_npm_package(git_repo)
    main.run("git checkout -b bar foo")
    return pkg


def test_get_branch(git_repo):
    assert main.get_branch() == "foo"


def test_get_repo(git_repo):
    repo = f"{git_repo.parent.name}/{git_repo.name}"
    assert main.get_repo("upstream") == repo


def test_get_version_python(py_package):
    assert main.get_version() == "0.0.1"
    main.bump_version("0.0.2a0")
    assert main.get_version() == "0.0.2a0"


def test_get_version_npm(npm_package):
    assert main.get_version() == "1.0.0"
    print(str(py_package))
    main.run("npm version patch")
    assert main.get_version() == "1.0.1"


def test_format_pr_entry():
    with patch("release_helpers.__main__.requests.get") as mocked_get:
        resp = main.format_pr_entry("foo", 121, auth="baz")
        mocked_get.assert_called_with(
            "https://api.github.com/repos/foo/pulls/121",
            headers={"Authorization": "token baz"},
        )

    assert resp.startswith("- ")


def test_get_source_repo():
    with patch("release_helpers.__main__.requests.get") as mocked_get:
        resp = main.get_source_repo("foo/bar", auth="baz")
        mocked_get.assert_called_with(
            "https://api.github.com/repos/foo/bar",
            headers={"Authorization": "token baz"},
        )


def test_get_changelog_entry(py_package):
    changelog = py_package / "CHANGELOG.md"
    version = main.get_version()

    with patch("release_helpers.__main__.generate_activity_md") as mocked_gen:
        mocked_gen.return_value = CHANGELOG_ENTRY
        resp = main.get_changelog_entry("foo", "bar/baz", changelog, version)
        mocked_gen.assert_called_with("bar/baz", since="v0.0.1", kind="pr", auth=None)

    assert f"## {version}" in resp
    assert PR_ENTRY in resp

    with patch("release_helpers.__main__.generate_activity_md") as mocked_gen:
        mocked_gen.return_value = CHANGELOG_ENTRY
        resp = main.get_changelog_entry(
            "foo", "bar/baz", changelog, version, resolve_backports=True, auth="bizz"
        )
        mocked_gen.assert_called_with("bar/baz", since="v0.0.1", kind="pr", auth="bizz")

    assert f"## {version}" in resp
    assert PR_ENTRY in resp


def test_compute_sha256(py_package):
    sha = "9ff86928054a7791ed023c799702b0fa343f4a371127c43bdf583d4b0ee3a6f3"
    assert main.compute_sha256(py_package / "CHANGELOG.md") == sha


def test_create_release_commit(py_package):
    main.bump_version("0.0.2a0")
    version = main.get_version()
    main.run("python -m build .")
    shas = main.create_release_commit(version)
    assert "dist/foo-0.0.2a0.tar.gz" in shas
    assert "dist/foo-0.0.2a0-py3-none-any.whl" in shas
    shutil.rmtree(py_package / "dist")

    # Add an npm package and test with that
    create_npm_package(py_package)
    with open(py_package / "package.json") as fid:
        data = json.load(fid)
    data["version"] = version
    with open(py_package / "package.json", "w") as fid:
        json.dump(data, fid, indent=4)
    txt = (py_package / "tbump.toml").read_text(encoding="utf-8")
    txt += """
[[file]]
src = "package.json"
search = '"version": "{current_version}"'
"""
    (py_package / "tbump.toml").write_text(txt, encoding="utf-8")
    main.bump_version("0.0.2a1")
    version = main.get_version()
    main.run("python -m build .")
    shas = main.create_release_commit(version)
    npm_dist = f"{py_package.name}-0.0.2a1.tgz"
    assert npm_dist in shas
    assert "dist/foo-0.0.2a1.tar.gz" in shas


def test_bump_version(py_package):
    runner = CliRunner()
    for spec in ["1.0.1", "1.0.1.dev1", "1.0.3a4"]:
        main.bump_version(spec)
        assert main.get_version() == spec


def test_prep_env_simple(py_package):
    """Standard local run with no env variables."""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["prep-env", "--version-spec", "1.0.1"])
    assert result.exit_code == 0
    assert "branch=bar" in result.output
    assert "version=1.0.1" in result.output
    assert "is_prerelease=false" in result.output


def test_prep_env_pr(py_package):
    """With GITHUB_BASE_REF (Pull Request)"""
    runner = CliRunner()
    env = dict(GITHUB_BASE_REF="foo", VERSION_SPEC="1.0.1")
    result = runner.invoke(main.cli, ["prep-env"], env=env)
    assert result.exit_code == 0
    assert "branch=foo" in result.output


def test_prep_env_full(py_package, tmp_path):
    """Full GitHub Actions simulation (Push)"""
    runner = CliRunner()
    version_spec = "1.0.1a1"

    workflow = Path(f"{main.HERE}/../.github/workflows/check-release.yml")
    workflow = workflow.resolve()
    os.makedirs(py_package / ".github/workflows")
    shutil.copy(workflow, py_package / ".github/workflows")

    env_file = tmp_path / "github.env"

    env = dict(
        GITHUB_REF="refs/heads/foo",
        GITHUB_WORKFLOW="check-release",
        GITHUB_ACTIONS="true",
        GITHUB_REPOSITORY="baz/bar",
        VERSION_SPEC=version_spec,
        GITHUB_ENV=str(env_file),
    )
    with patch("release_helpers.__main__.run") as mock_run, patch(
        "release_helpers.__main__.get_source_repo"
    ) as mocked_get_source_repo:
        # Fake out the version and source repo responses
        mock_run.return_value = version_spec
        mocked_get_source_repo.return_value = "foo/bar"
        result = runner.invoke(main.cli, ["prep-env"], env=env)
        mock_run.assert_has_calls(
            [
                call(
                    'git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"'
                ),
                call('git config --global user.name "GitHub Action"'),
                call("git remote add upstream https://github.com/foo/bar"),
                call("git fetch upstream foo --tags"),
                call("git checkout -B foo upstream/foo"),
                call(
                    "git diff HEAD upstream/foo -- ./github/workflows/check-release.yml"
                ),
                call("tbump --non-interactive --only-patch 1.0.1a1"),
                call("python setup.py --version", quiet=True),
            ]
        )

    assert result.exit_code == 0
    text = env_file.read_text(encoding="utf-8")
    assert "BRANCH=foo" in text
    assert f"VERSION={version_spec}" in text
    assert "IS_PRERELEASE=true" in text
    assert "REPOSITORY=foo/bar" in text


def test_prep_changelog(py_package):
    runner = CliRunner()
    changelog = py_package / "CHANGELOG.md"

    result = runner.invoke(main.cli, ["prep-env", "--version-spec", "1.0.1"])
    assert result.exit_code == 0

    with patch("release_helpers.__main__.generate_activity_md") as mocked_gen:
        mocked_gen.return_value = CHANGELOG_ENTRY
        result = runner.invoke(main.cli, ["prep-changelog", "--path", changelog])
    assert result.exit_code == 0
    text = changelog.read_text(encoding="utf-8")
    assert main.START_MARKER in text
    assert main.END_MARKER in text
    assert PR_ENTRY in text


def test_validate_changelog(py_package, tmp_path):
    runner = CliRunner()
    changelog = py_package / "CHANGELOG.md"
    output = tmp_path / "output.md"

    # prep the changelog first
    version_spec = "1.5.1"
    result = runner.invoke(main.cli, ["prep-env", "--version-spec", version_spec])
    assert result.exit_code == 0

    with patch("release_helpers.__main__.generate_activity_md") as mocked_gen:
        mocked_gen.return_value = CHANGELOG_ENTRY
        result = runner.invoke(main.cli, ["prep-changelog", "--path", changelog])
    assert result.exit_code == 0

    # then prep the release
    main.bump_version(version_spec)
    with patch("release_helpers.__main__.generate_activity_md") as mocked_gen:
        mocked_gen.return_value = CHANGELOG_ENTRY
        result = runner.invoke(
            main.cli, ["validate-changelog", "--path", changelog, "--output", output]
        )
    assert result.exit_code == 0

    assert PR_ENTRY in output.read_text(encoding="utf-8")
    text = changelog.read_text(encoding="utf-8")
    assert f"{main.START_MARKER}\n## {version_spec}" in text
    assert main.END_MARKER in text


def test_prep_python(py_package):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["prep-python"])
    assert result.exit_code == 0


def test_prep_release(py_package):
    runner = CliRunner()
    version_spec = "1.5.1"
    # Prep the env
    result = runner.invoke(main.cli, ["prep-env", "--version-spec", version_spec])
    assert result.exit_code == 0
    # Create the dist files
    main.run("python -m build .")
    # Finalize the release
    result = runner.invoke(
        main.cli, ["prep-release", "--post-version-spec", "1.5.2.dev0"]
    )
    assert result.exit_code == 0
