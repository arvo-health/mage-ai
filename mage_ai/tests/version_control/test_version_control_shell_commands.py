import os
import shutil
import subprocess
import tempfile
import unittest
import urllib.parse
import uuid
from contextlib import contextmanager
from unittest.mock import patch

# The database URL is chosen when mage_ai.orchestration.db is first imported.
os.environ['ENV'] = 'test_mage'

from mage_ai.api.errors import ApiError  # noqa: E402
from mage_ai.api.operations.constants import LIST, UPDATE, WRITE  # noqa: E402
from mage_ai.api.policies.VersionControlBranchPolicy import (  # noqa: E402
    VersionControlBranchPolicy,
)
from mage_ai.api.policies.VersionControlFilePolicy import (  # noqa: E402
    VersionControlFilePolicy,
)
from mage_ai.api.policies.VersionControlProjectPolicy import (  # noqa: E402
    VersionControlProjectPolicy,
)
from mage_ai.api.policies.VersionControlRemotePolicy import (  # noqa: E402
    VersionControlRemotePolicy,
)
from mage_ai.api.resources.VersionControlBranchResource import (  # noqa: E402
    VersionControlBranchResource,
)
from mage_ai.api.resources.VersionControlFileResource import (  # noqa: E402
    VersionControlFileResource,
)
from mage_ai.api.resources.VersionControlProjectResource import (  # noqa: E402
    VersionControlProjectResource,
)
from mage_ai.api.resources.VersionControlRemoteResource import (  # noqa: E402
    VersionControlRemoteResource,
)
from mage_ai.orchestration.db import db_connection  # noqa: E402
from mage_ai.orchestration.db.models.base import Base  # noqa: E402
from mage_ai.orchestration.db.models.oauth import User  # noqa: E402
from mage_ai.version_control.models import Project  # noqa: E402

import mage_ai.orchestration.db.models.oauth  # noqa: E402, F401


NOTEBOOK_EDIT_FLAGS = (
    'mage_ai.settings.server.DISABLE_NOTEBOOK_EDIT_ACCESS',
    'mage_ai.settings.DISABLE_NOTEBOOK_EDIT_ACCESS',
    'mage_ai.api.utils.DISABLE_NOTEBOOK_EDIT_ACCESS',
    'mage_ai.api.policies.BasePolicy.DISABLE_NOTEBOOK_EDIT_ACCESS',
    'mage_ai.api.policies.mixins.user_permissions.DISABLE_NOTEBOOK_EDIT_ACCESS',
)


@contextmanager
def notebook_edit_disabled():
    with contextmanager_patches(NOTEBOOK_EDIT_FLAGS, 1):
        yield


@contextmanager
def contextmanager_patches(targets, value):
    from contextlib import ExitStack

    with ExitStack() as stack:
        for target in targets:
            stack.enter_context(patch(target, value))
        yield


class VersionControlShellCommandTest(unittest.IsolatedAsyncioTestCase):
    """Shell metacharacters in version-control updates must not be executed.

    These tests follow the editor update path: policy authorization, then the
    resource method, then the git runner. They fail while that runner rebuilds
    a shell command. Branch push is not covered here: it does not reach that
    runner. It hands the branch name to GitPython as an argument.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        db_connection.start_session(force=True)
        Base.metadata.create_all(db_connection.session.get_bind())

    @classmethod
    def tearDownClass(cls):
        db_connection.close_session()
        database_path = os.path.abspath('test.db')
        if os.path.exists(database_path):
            os.remove(database_path)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        suffix = uuid.uuid4().hex[:12]
        self.editor = User.create(
            email=f'editor-{suffix}@example.com',
            roles=2,
            username=f'editor-{suffix}',
        )
        self.viewer = User.create(
            email=f'viewer-{suffix}@example.com',
            roles=4,
            username=f'viewer-{suffix}',
        )

    def _marker(self) -> str:
        directory = tempfile.mkdtemp(prefix='vc-marker-')
        self.addCleanup(shutil.rmtree, directory, True)
        return os.path.join(directory, 'marker')

    def _project(self) -> Project:
        root = tempfile.mkdtemp(prefix='vc-project-')
        self.addCleanup(shutil.rmtree, root, True)
        previous = os.environ.get('MAGE_REPO_PATH')
        os.environ['MAGE_REPO_PATH'] = root

        def restore():
            if previous is None:
                os.environ.pop('MAGE_REPO_PATH', None)
            else:
                os.environ['MAGE_REPO_PATH'] = previous

        self.addCleanup(restore)
        with open(os.path.join(root, 'settings.yaml'), 'w') as settings_file:
            settings_file.write('version_control:\n  project: {}\n')
        project = Project.load(uuid='project')
        os.makedirs(project.repo_path, exist_ok=True)
        subprocess.run(['git', 'init', '-q', project.repo_path], check=True)
        return project

    def _assert_not_executed(self, marker: str) -> None:
        self.assertFalse(
            os.path.exists(marker),
            'a shell metacharacter in a version-control field was executed',
        )

    def _assert_refused(self, error, marker: str) -> None:
        self._assert_not_executed(marker)
        self.assertIsInstance(error, ApiError)
        self.assertEqual(403, error.code)

    async def _authorized_call(
        self,
        policy,
        action: str,
        call,
        payload=None,
        query=None,
    ):
        error = None
        try:
            await policy.authorize_action(action)
            if payload is not None:
                await policy.authorize_attributes(
                    WRITE,
                    list(payload.keys()),
                    api_operation_action=action,
                )
            if query:
                await policy.authorize_query(query, api_operation_action=action)
            result = call()
            if hasattr(result, '__await__'):
                await result
        except ApiError as err:
            error = err
        return error

    async def test_command_field_does_not_execute_shell_metacharacters(self):
        cases = {
            'semicolon': 'status; touch {marker}',
            'and': 'status && touch {marker}',
            'pipe': 'status | touch {marker}',
            'substitution': 'status $(touch {marker})',
            'backtick': 'status `touch {marker}`',
            'git_prefix': 'git status; touch {marker}',
        }
        for name, template in cases.items():
            with self.subTest(command=name):
                marker = self._marker()
                project = self._project()
                resource = await VersionControlFileResource.member(
                    'readme',
                    self.editor,
                    parent_model=project,
                )
                payload = {'command': template.format(marker=marker)}
                async def update():
                    await resource.process_update(payload)

                error = await self._authorized_call(
                    VersionControlFilePolicy(
                        resource,
                        self.editor,
                        api_operation_action=UPDATE,
                    ),
                    UPDATE,
                    update,
                    payload=payload,
                )
                self.assertIsNone(error)
                self._assert_not_executed(marker)

    async def test_file_update_fields_do_not_execute_shell_metacharacters(self):
        marker = self._marker()
        cases = {
            'add': {'add': f'foo; touch {marker}'},
            'commit': {'commit': f'x"; touch {marker}; echo "'},
            'reset': {'reset': f'HEAD; touch {marker}'},
        }
        for name, payload in cases.items():
            with self.subTest(field=name):
                case_marker = self._marker()
                case_payload = {
                    key: value.replace(marker, case_marker)
                    for key, value in payload.items()
                }
                project = self._project()
                resource = await VersionControlFileResource.member(
                    'readme',
                    self.editor,
                    parent_model=project,
                )
                async def update():
                    await resource.process_update(case_payload)

                error = await self._authorized_call(
                    VersionControlFilePolicy(
                        resource,
                        self.editor,
                        api_operation_action=UPDATE,
                    ),
                    UPDATE,
                    update,
                    payload=case_payload,
                )
                self.assertIsNone(error)
                self._assert_not_executed(case_marker)

    async def test_quoted_commit_message_semicolon_is_not_executed(self):
        marker = self._marker()
        project = self._project()
        resource = await VersionControlFileResource.member(
            'readme',
            self.editor,
            parent_model=project,
        )
        payload = {'commit': f'hello; touch {marker}'}
        error = await self._authorized_call(
            VersionControlFilePolicy(
                resource,
                self.editor,
                api_operation_action=UPDATE,
            ),
            UPDATE,
            lambda: resource.process_update(payload),
            payload=payload,
        )
        self.assertIsNone(error)
        self._assert_not_executed(marker)

    async def test_branch_update_does_not_execute_shell_metacharacters(self):
        for action in ('checkout', 'merge', 'pull', 'rebase', 'clone'):
            with self.subTest(action=action):
                marker = self._marker()
                project = self._project()
                name = f'main; touch {marker}'
                resource = await VersionControlBranchResource.member(
                    urllib.parse.quote(name, safe=''),
                    self.editor,
                    parent_model=project,
                )
                payload = {action: True}
                async def update():
                    await resource.process_update(payload)

                error = await self._authorized_call(
                    VersionControlBranchPolicy(
                        resource,
                        self.editor,
                        api_operation_action=UPDATE,
                    ),
                    UPDATE,
                    update,
                    payload=payload,
                )
                self.assertIsNone(error)
                self._assert_not_executed(marker)

    async def test_branch_remote_query_does_not_execute_shell_metacharacters(self):
        marker = self._marker()
        project = self._project()
        # The trailing branch name is appended after the remote name. The
        # comment keeps that extra argument out of the shell command.
        query = {'remote': [f'origin; touch {marker} #']}
        resource = await VersionControlBranchResource.member(
            'main',
            self.editor,
            parent_model=project,
            query=query,
        )
        payload = {'pull': True}
        error = await self._authorized_call(
            VersionControlBranchPolicy(
                resource,
                self.editor,
                api_operation_action=UPDATE,
            ),
            UPDATE,
            lambda: resource.process_update(payload),
            payload=payload,
            query=query,
        )
        self.assertIsNone(error)
        self._assert_not_executed(marker)

    async def test_diff_file_names_are_not_executed_as_shell(self):
        marker = self._marker()
        project = self._project()
        relative_name = f'pwn; touch {marker}'
        planted = os.path.join(project.repo_path, relative_name)
        os.makedirs(os.path.dirname(planted), exist_ok=True)
        with open(planted, 'w') as planted_file:
            planted_file.write('x')

        query = {'diff': ['1']}
        error = await self._authorized_call(
            VersionControlFilePolicy(
                None,
                self.editor,
                api_operation_action=LIST,
            ),
            LIST,
            lambda: VersionControlFileResource.collection(
                query,
                {},
                self.editor,
                parent_model=project,
            ),
            query=query,
        )
        self.assertIsNone(error)
        self._assert_not_executed(marker)

    async def test_argument_list_git_commands_do_not_execute_shell_metacharacters(self):
        marker = self._marker()
        project = self._project()
        cases = []

        file_name = f'foo; touch {marker}'
        file_resource = await VersionControlFileResource.member(
            urllib.parse.quote(file_name, safe=''),
            self.editor,
            parent_model=project,
        )
        cases.append((
            'file_delete',
            VersionControlFilePolicy(
                file_resource,
                self.editor,
                api_operation_action='delete',
            ),
            'delete',
            None,
            lambda resource=file_resource: resource.process_delete(),
        ))

        create_payload = {'name': file_name}

        async def create_file():
            await VersionControlFileResource.create(
                create_payload,
                self.editor,
                parent_model=project,
            )

        cases.append((
            'file_create',
            VersionControlFilePolicy(
                None,
                self.editor,
                api_operation_action='create',
            ),
            'create',
            create_payload,
            create_file,
        ))

        branch_name = f'feature; touch {marker}'
        branch_resource = await VersionControlBranchResource.member(
            urllib.parse.quote(branch_name, safe=''),
            self.editor,
            parent_model=project,
        )
        cases.append((
            'branch_delete',
            VersionControlBranchPolicy(
                branch_resource,
                self.editor,
                api_operation_action='delete',
            ),
            'delete',
            None,
            lambda resource=branch_resource: resource.process_delete(),
        ))
        branch_payload = {'name': branch_name}

        async def create_branch():
            await VersionControlBranchResource.create(
                branch_payload,
                self.editor,
                parent_model=project,
            )

        cases.append((
            'branch_create',
            VersionControlBranchPolicy(
                None,
                self.editor,
                api_operation_action='create',
            ),
            'create',
            branch_payload,
            create_branch,
        ))

        remote_payload = {
            'name': f'origin; touch {marker}',
            'url': 'https://example.invalid/repo.git',
        }

        async def create_remote():
            await VersionControlRemoteResource.create(
                remote_payload,
                self.editor,
                parent_model=project,
            )

        cases.append((
            'remote_create',
            VersionControlRemotePolicy(
                None,
                self.editor,
                api_operation_action='create',
            ),
            'create',
            remote_payload,
            create_remote,
        ))

        project_resource = await VersionControlProjectResource.member(
            project.uuid,
            self.editor,
        )
        email_payload = {'email': f'person@example.com"; touch {marker}; echo "'}

        async def update_email():
            await project_resource.process_update(email_payload)

        cases.append((
            'project_email',
            VersionControlProjectPolicy(
                project_resource,
                self.editor,
                api_operation_action=UPDATE,
            ),
            UPDATE,
            email_payload,
            update_email,
        ))

        for name, policy, action, payload, call in cases:
            with self.subTest(operation=name):
                error = await self._authorized_call(
                    policy,
                    action,
                    call,
                    payload=payload,
                )
                self.assertIsNone(error)
                self._assert_not_executed(marker)

    async def test_viewer_cannot_update_version_control_file(self):
        marker = self._marker()
        project = self._project()
        resource = await VersionControlFileResource.member(
            'readme',
            self.viewer,
            parent_model=project,
        )
        payload = {'command': f'status; touch {marker}'}
        error = await self._authorized_call(
            VersionControlFilePolicy(
                resource,
                self.viewer,
                api_operation_action=UPDATE,
            ),
            UPDATE,
            lambda: resource.process_update(payload),
            payload=payload,
        )
        self._assert_refused(error, marker)

    async def test_disabled_notebook_edit_refuses_file_update(self):
        marker = self._marker()
        project = self._project()
        resource = await VersionControlFileResource.member(
            'readme',
            self.editor,
            parent_model=project,
        )
        payload = {'command': f'status; touch {marker}'}
        with notebook_edit_disabled():
            error = await self._authorized_call(
                VersionControlFilePolicy(
                    resource,
                    self.editor,
                    api_operation_action=UPDATE,
                ),
                UPDATE,
                lambda: resource.process_update(payload),
                payload=payload,
            )
        self._assert_refused(error, marker)

    async def test_disabled_notebook_edit_refuses_branch_update(self):
        marker = self._marker()
        project = self._project()
        name = f'main; touch {marker}'
        resource = await VersionControlBranchResource.member(
            urllib.parse.quote(name, safe=''),
            self.editor,
            parent_model=project,
        )
        payload = {'checkout': True}
        with notebook_edit_disabled():
            error = await self._authorized_call(
                VersionControlBranchPolicy(
                    resource,
                    self.editor,
                    api_operation_action=UPDATE,
                ),
                UPDATE,
                lambda: resource.process_update(payload),
                payload=payload,
            )
        self._assert_refused(error, marker)
