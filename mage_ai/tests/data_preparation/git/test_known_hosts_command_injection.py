import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from mage_ai.api.resources.SyncResource import SyncResource
from mage_ai.data_preparation.git import Git
from mage_ai.data_preparation.git.utils import add_host_to_known_hosts
from mage_ai.data_preparation.sync import AuthType, GitConfig
from mage_ai.data_preparation.sync.git_sync import GitSync


class KnownHostsCommandInjectionTest(unittest.TestCase):
    """Git remote hostnames must not be executed by a shell.

    These tests fail while add_host_to_known_hosts interpolates the parsed
    hostname into a shell command. They pass once that hostname is rejected
    or passed to ssh-keyscan as an argument without a shell.

    execute_on_remote_branch in mage_ai/data_preparation/git/utils.py calls the
    same helper with the git remote's name, but Branch.auth_type is a one-tuple,
    so AuthType.SSH never matches and that wrapper does not reach the helper.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.home = os.path.join(self.root, 'home')
        self.ssh_dir = os.path.join(self.root, 'ssh')
        self.known_hosts = os.path.join(self.ssh_dir, 'known_hosts')
        os.makedirs(self.home)
        os.makedirs(self.ssh_dir)
        self._old_cwd = os.getcwd()
        self._old_env = {
            key: os.environ.get(key)
            for key in ('HOME', 'MAGE_REPO_PATH', 'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_SYSTEM')
        }
        os.chdir(self.root)
        os.environ['HOME'] = self.home
        os.environ['MAGE_REPO_PATH'] = self.root
        os.environ['GIT_CONFIG_GLOBAL'] = os.path.join(self.home, '.gitconfig')
        os.environ['GIT_CONFIG_SYSTEM'] = os.path.join(self.home, '.gitconfig-system')
        self._patches = [
            patch(
                'mage_ai.data_preparation.git.utils.DEFAULT_KNOWN_HOSTS_FILE',
                self.known_hosts,
            ),
            patch(
                'mage_ai.data_preparation.git.utils.DEFAULT_SSH_KEY_DIRECTORY',
                self.ssh_dir,
            ),
            patch(
                'mage_ai.data_preparation.git.DEFAULT_KNOWN_HOSTS_FILE',
                self.known_hosts,
            ),
        ]
        for item in self._patches:
            item.start()

    def tearDown(self):
        for item in self._patches:
            item.stop()
        os.chdir(self._old_cwd)
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._tmp.cleanup()

    def _clear_known_hosts(self):
        if os.path.exists(self.known_hosts):
            os.remove(self.known_hosts)

    def _assert_marker_absent(self, marker_name):
        found = []
        for directory, _subdirs, files in os.walk(self.root):
            if marker_name in files:
                found.append(os.path.join(directory, marker_name))
        self.assertEqual(
            found,
            [],
            'shell metacharacters in the git remote hostname were executed',
        )

    def _init_repo(self, name):
        repo = os.path.join(self.root, name)
        os.makedirs(repo)
        subprocess.check_call(['git', 'init', '-q', '-b', 'master', repo])
        subprocess.check_call(['git', '-C', repo, 'config', 'user.email', 'tester@example.com'])
        subprocess.check_call(['git', '-C', repo, 'config', 'user.name', 'tester'])
        readme = os.path.join(repo, 'README')
        with open(readme, 'w', encoding='utf-8') as handle:
            handle.write('readme\n')
        subprocess.check_call(['git', '-C', repo, 'add', 'README'])
        subprocess.check_call(['git', '-C', repo, 'commit', '-q', '-m', 'init'])
        return repo

    def _git(self, remote_repo_link, repo_path, setup_repo=False):
        config = GitConfig(
            remote_repo_link=remote_repo_link,
            repo_path=repo_path,
            auth_type=AuthType.SSH,
            username='tester',
            email='tester@example.com',
            branch='master',
        )
        return Git(
            auth_type=AuthType.SSH,
            git_config=config,
            repo_path=repo_path,
            setup_repo=setup_repo,
        )

    def _call(self, func):
        try:
            func()
        except Exception:
            pass

    def test_add_host_to_known_hosts_does_not_run_semicolon(self):
        marker = 'marker_semicolon'
        self._clear_known_hosts()
        self._call(lambda: add_host_to_known_hosts(f'git@127.0.0.1;>{marker};'))
        self._assert_marker_absent(marker)

    def test_add_host_to_known_hosts_does_not_run_ssh_url_semicolon(self):
        marker = 'marker_ssh_semicolon'
        self._clear_known_hosts()
        self._call(lambda: add_host_to_known_hosts(f'ssh://127.0.0.1;>{marker};'))
        self._assert_marker_absent(marker)

    def test_add_host_to_known_hosts_does_not_run_command_substitution(self):
        marker = 'marker_substitution'
        self._clear_known_hosts()
        self._call(lambda: add_host_to_known_hosts(f'git@127.0.0.1;$(touch {marker});'))
        self._assert_marker_absent(marker)

    def test_add_host_to_known_hosts_does_not_run_backticks(self):
        marker = 'marker_backtick'
        self._clear_known_hosts()
        self._call(lambda: add_host_to_known_hosts(f'git@127.0.0.1;`touch {marker}`;'))
        self._assert_marker_absent(marker)

    def test_add_host_to_known_hosts_does_not_run_ampersand(self):
        marker = 'marker_ampersand'
        self._clear_known_hosts()
        self._call(lambda: add_host_to_known_hosts(f'git@127.0.0.1&touch {marker}'))
        self._assert_marker_absent(marker)

    def test_add_host_to_known_hosts_does_not_run_pipe(self):
        marker = 'marker_pipe'
        self._clear_known_hosts()
        self._call(lambda: add_host_to_known_hosts(f'git@127.0.0.1|touch {marker}'))
        self._assert_marker_absent(marker)

    def test_remote_commands_do_not_run_hostname_metacharacters(self):
        calls = (
            ('fetch', lambda git: git.fetch()),
            ('pull', lambda git: git.pull()),
            ('push', lambda git: git.push()),
            ('clone', lambda git: git.clone()),
            ('reset_hard', lambda git: git.reset_hard()),
            ('pull_remote_branch', lambda git: git.pull_remote_branch('mage-repo', 'master')),
            ('push_remote_branch', lambda git: git.push_remote_branch('mage-repo', 'master')),
            ('submodules_update', lambda git: git.submodules_update()),
            (
                'switch_remote_branch',
                lambda git: git._switch_remote_branch('master', 'mage-repo'),
            ),
        )
        for name, call in calls:
            with self.subTest(command=name):
                marker = f'marker_remote_{name}'
                self._clear_known_hosts()
                repo = self._init_repo(f'repo_{name}')
                git = self._git(f'git@127.0.0.1;>{marker};', repo)
                self._call(lambda call=call, git=git: call(git))
                self._assert_marker_absent(marker)

    def test_remote_command_ssh_url_does_not_run_hostname_metacharacters(self):
        marker = 'marker_fetch_ssh_url'
        self._clear_known_hosts()
        repo = self._init_repo('repo_fetch_ssh')
        git = self._git(f'ssh://127.0.0.1;>{marker};', repo)
        self._call(git.fetch)
        self._assert_marker_absent(marker)

    def test_setup_repo_does_not_run_hostname_metacharacters(self):
        marker = 'marker_setup_repo'
        self._clear_known_hosts()
        repo = os.path.join(self.root, 'not_a_repo')
        os.makedirs(repo)
        self._call(lambda: self._git(f'git@127.0.0.1;>{marker};', repo, setup_repo=True))
        self._assert_marker_absent(marker)

    def test_git_sync_data_does_not_run_hostname_metacharacters(self):
        marker = 'marker_sync_data'
        self._clear_known_hosts()
        repo = self._init_repo('repo_sync_data')
        config = GitConfig(
            remote_repo_link=f'git@127.0.0.1;>{marker};',
            repo_path=repo,
            auth_type=AuthType.SSH,
            username='tester',
            email='tester@example.com',
            branch='master',
        )
        self._call(lambda: GitSync(config).sync_data())
        self._assert_marker_absent(marker)

    def test_git_sync_reset_does_not_run_hostname_metacharacters(self):
        marker = 'marker_sync_reset'
        self._clear_known_hosts()
        repo = self._init_repo('repo_sync_reset')
        config = GitConfig(
            remote_repo_link=f'git@127.0.0.1;>{marker};',
            repo_path=repo,
            auth_type=AuthType.SSH,
            username='tester',
            email='tester@example.com',
            branch='master',
        )
        self._call(lambda: GitSync(config).reset())
        self._assert_marker_absent(marker)

    def test_sync_resource_create_does_not_run_hostname_metacharacters(self):
        marker = 'marker_sync_create'
        self._clear_known_hosts()
        repo = os.path.join(self.root, 'sync_create_repo')
        os.makedirs(repo)
        payload = dict(
            remote_repo_link=f'git@127.0.0.1;>{marker};',
            repo_path=repo,
            auth_type='ssh',
            username='tester',
            email='tester@example.com',
            branch='master',
        )
        self._call(lambda: SyncResource.create(payload, None, repo_name=repo))
        self._assert_marker_absent(marker)

    def test_sync_resource_sync_data_does_not_run_hostname_metacharacters(self):
        marker = 'marker_sync_update'
        self._clear_known_hosts()
        repo = self._init_repo('sync_update_repo')
        resource = SyncResource(
            dict(
                remote_repo_link=f'git@127.0.0.1;>{marker};',
                repo_path=repo,
                auth_type='ssh',
                username='tester',
                email='tester@example.com',
                branch='master',
                user_git_settings={},
            ),
            None,
        )
        self._call(lambda: resource.update(dict(action_type='sync_data')))
        self._assert_marker_absent(marker)


if __name__ == '__main__':
    unittest.main()
