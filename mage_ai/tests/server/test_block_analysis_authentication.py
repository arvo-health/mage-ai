"""Authentication tests for the block-analysis HTTP route.

These tests exercise GET /api/pipelines/<pipeline_uuid>/blocks/<block_uuid>/analyses
on the Tornado app from mage_ai.server.server.make_app. They fail while that
route returns stored dataframe analysis without a session, API token, or
viewer permission, and they pass once an unauthenticated caller is rejected
and a caller is allowed to read only a pipeline they can view.

Run:

    ENV=test_mage REQUIRE_USER_AUTHENTICATION=1 \\
        python -m unittest mage_ai.tests.server.test_block_analysis_authentication
"""
import hashlib
import json
import os
import shutil
import tempfile
from urllib.parse import urlencode

# The test database URL is chosen when mage_ai.orchestration.db is imported.
os.environ['ENV'] = 'test_mage'
os.environ['REQUIRE_USER_AUTHENTICATION'] = '1'

import pandas as pd
from tornado.testing import AsyncHTTPTestCase

from mage_ai.authentication.oauth2 import generate_access_token
from mage_ai.data_preparation.models.block import Block
from mage_ai.data_preparation.models.constants import BlockStatus
from mage_ai.data_preparation.models.pipeline import Pipeline
from mage_ai.data_preparation.models.variables.constants import VariableType
from mage_ai.data_preparation.repo_manager import get_project_uuid, init_project_uuid
from mage_ai.orchestration.constants import Entity
from mage_ai.orchestration.db import TEST_DB, db_connection, engine
from mage_ai.orchestration.db.database_manager import database_manager
from mage_ai.orchestration.db.models.oauth import (
    Oauth2Application,
    Permission,
    Role,
    User,
)
from mage_ai.server.api.constants import HEADER_API_KEY, HEADER_OAUTH_TOKEN
from mage_ai.server.server import make_app
from mage_ai.settings import OAUTH2_APPLICATION_CLIENT_ID
from mage_ai.settings.repo import set_repo_path
from mage_ai.settings.server import REQUIRE_USER_AUTHENTICATION

MARKER_ALPHA = 'analysis-marker-alpha-7c1e'
MARKER_BETA = 'analysis-marker-beta-4d90'
BLOCK_UUID = 'shared_loader'
PIPELINE_ALPHA_NAME = 'pipeline_alpha'
PIPELINE_BETA_NAME = 'pipeline_beta'


def _snapshot(root):
    recorded = {}
    if not root or not os.path.exists(root):
        return recorded
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            with open(path, 'rb') as handle:
                recorded[path] = hashlib.sha256(handle.read()).hexdigest()
    return recorded


def _store_analysis(pipeline, block, marker):
    block.update_status(BlockStatus.EXECUTED)
    frame = pd.DataFrame({'value': [1, 2, 3]})
    manager = pipeline.variable_manager
    manager.add_variable(pipeline.uuid, block.uuid, 'output_0', frame)
    manager.add_variable(
        pipeline.uuid,
        block.uuid,
        'output_0',
        {
            'statistics': {
                'marker': marker,
                'original_row_count': int(frame.shape[0]),
                'original_column_count': int(frame.shape[1]),
            },
            'metadata': {'column_types': {'value': 'number'}},
            'insights': [],
            'suggestions': [],
        },
        disable_variable_type_inference=True,
        variable_type=VariableType.DATAFRAME_ANALYSIS,
    )


class PipelineBlockAnalysisAuthenticationTest(AsyncHTTPTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repo_path = tempfile.mkdtemp(prefix='mage-block-analysis-auth-')
        set_repo_path(cls.repo_path)
        init_project_uuid()
        # The engine is created at import and may already hold test.db. Drop that
        # connection before replacing the file so later writes are not applied to
        # an unlinked database.
        engine.dispose()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        database_manager.run_migrations()
        db_connection.start_session(force=True)

        cls.pipeline_alpha = Pipeline.create(PIPELINE_ALPHA_NAME, repo_path=cls.repo_path)
        cls.pipeline_beta = Pipeline.create(PIPELINE_BETA_NAME, repo_path=cls.repo_path)
        block_alpha = Block.create(
            BLOCK_UUID,
            'data_loader',
            cls.repo_path,
            language='python',
            pipeline=cls.pipeline_alpha,
        )
        block_beta = Block.create(
            BLOCK_UUID,
            'data_loader',
            cls.repo_path,
            language='python',
            pipeline=cls.pipeline_beta,
        )
        cls.pipeline_alpha.add_block(block_alpha)
        cls.pipeline_beta.add_block(block_beta)
        _store_analysis(cls.pipeline_alpha, block_alpha, MARKER_ALPHA)
        _store_analysis(cls.pipeline_beta, block_beta, MARKER_BETA)

        # Reload from disk the same way the HTTP handler does.
        cls.pipeline_alpha = Pipeline.get(cls.pipeline_alpha.uuid, repo_path=cls.repo_path)
        cls.pipeline_beta = Pipeline.get(cls.pipeline_beta.uuid, repo_path=cls.repo_path)
        reloaded_alpha = cls.pipeline_alpha.get_block(BLOCK_UUID).get_analyses()
        reloaded_beta = cls.pipeline_beta.get_block(BLOCK_UUID).get_analyses()
        if MARKER_ALPHA not in json.dumps(reloaded_alpha):
            raise RuntimeError('fixture did not persist pipeline alpha analysis')
        if MARKER_BETA not in json.dumps(reloaded_beta):
            raise RuntimeError('fixture did not persist pipeline beta analysis')

        cls.project_uuid = get_project_uuid()
        owner = User.create(email='owner@example.com', username='owner_user')
        cls.application = Oauth2Application.create(
            client_id=OAUTH2_APPLICATION_CLIENT_ID,
            client_type=Oauth2Application.ClientType.PUBLIC,
            name='frontend',
            user_id=owner.id,
        )

        viewer_role_alpha = Role.create(
            name='pipeline_alpha_viewer',
            permissions=[
                Permission.create(
                    access=int(Permission.Access.VIEWER),
                    entity=Entity.PIPELINE,
                    entity_id=cls.pipeline_alpha.uuid,
                ),
            ],
        )
        project_viewer_role = Role.create(
            name='project_viewer',
            permissions=[
                Permission.create(
                    access=int(Permission.Access.VIEWER),
                    entity=Entity.PROJECT,
                    entity_id=cls.project_uuid,
                ),
            ],
        )
        cls.viewer_alpha = User.create(
            email='viewer-alpha@example.com',
            roles_new=[viewer_role_alpha],
            username='viewer_alpha',
        )
        cls.project_viewer = User.create(
            email='viewer-project@example.com',
            roles_new=[project_viewer_role],
            username='viewer_project',
        )
        cls.no_access_user = User.create(
            email='no-access@example.com',
            username='no_access_user',
        )
        cls.token_viewer_alpha = generate_access_token(
            cls.viewer_alpha,
            application=cls.application,
        ).token
        cls.token_project_viewer = generate_access_token(
            cls.project_viewer,
            application=cls.application,
        ).token
        cls.token_no_access = generate_access_token(
            cls.no_access_user,
            application=cls.application,
        ).token

    @classmethod
    def tearDownClass(cls):
        db_connection.close_session()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(cls.repo_path):
            shutil.rmtree(cls.repo_path)
        super().tearDownClass()

    def get_app(self):
        return make_app()

    def _url(self, pipeline_uuid, block_uuid=BLOCK_UUID, query=None):
        path = f'/api/pipelines/{pipeline_uuid}/blocks/{block_uuid}/analyses'
        if query:
            path = f'{path}?{urlencode(query)}'
        return path

    def _headers(self, token):
        return {
            HEADER_API_KEY: OAUTH2_APPLICATION_CLIENT_ID,
            HEADER_OAUTH_TOKEN: token,
        }

    def _body(self, response):
        return response.body.decode('utf-8', errors='replace')

    def _assert_denied(self, response, markers):
        self.assertIn(
            response.code,
            (401, 403),
            msg=self._body(response)[:800],
        )
        body = self._body(response)
        for marker in markers:
            self.assertNotIn(marker, body)
        self.assertNotIn('"analyses"', body)

    def _assert_allowed(self, response, marker, forbidden_markers):
        body = self._body(response)
        self.assertEqual(200, response.code, msg=body[:800])
        payload = json.loads(body)
        self.assertIn(marker, body)
        for other in forbidden_markers:
            self.assertNotIn(other, body)
        analyses = payload.get('analyses')
        self.assertIsInstance(analyses, list)
        self.assertEqual(1, len(analyses))
        self.assertEqual('output_0', analyses[0].get('variable_uuid'))

    def test_authentication_is_enabled(self):
        self.assertTrue(REQUIRE_USER_AUTHENTICATION)

    def test_authenticated_pipeline_route_rejects_anonymous_callers(self):
        """Control: the OAuth middleware already rejects this route."""
        response = self.fetch(f'/api/pipelines/{self.pipeline_alpha.uuid}')
        self._assert_denied(response, [MARKER_ALPHA, MARKER_BETA])

    def test_unauthenticated_get_does_not_return_dataframe_analysis(self):
        before_alpha = _snapshot(self.pipeline_alpha.dir_path)
        before_beta = _snapshot(self.pipeline_beta.dir_path)
        response = self.fetch(self._url(self.pipeline_alpha.uuid))
        self._assert_denied(response, [MARKER_ALPHA, MARKER_BETA])
        self.assertEqual(before_alpha, _snapshot(self.pipeline_alpha.dir_path))
        self.assertEqual(before_beta, _snapshot(self.pipeline_beta.dir_path))

    def test_authenticated_user_without_access_does_not_return_analysis(self):
        before = _snapshot(self.pipeline_alpha.dir_path)
        response = self.fetch(
            self._url(self.pipeline_alpha.uuid),
            headers=self._headers(self.token_no_access),
        )
        self._assert_denied(response, [MARKER_ALPHA, MARKER_BETA])
        self.assertEqual(before, _snapshot(self.pipeline_alpha.dir_path))

    def test_pipeline_viewer_cannot_read_another_pipeline(self):
        """The pipeline in the path is the pipeline that must be authorized."""
        before = _snapshot(self.pipeline_beta.dir_path)
        response = self.fetch(
            self._url(self.pipeline_beta.uuid),
            headers=self._headers(self.token_viewer_alpha),
        )
        self._assert_denied(response, [MARKER_ALPHA, MARKER_BETA])
        self.assertEqual(before, _snapshot(self.pipeline_beta.dir_path))

    def test_query_parameters_cannot_select_a_different_pipeline(self):
        """Authorizing pipeline alpha must not return pipeline beta's analysis.

        The path names pipeline beta and block shared_loader. The query string
        names pipeline alpha, which this caller is allowed to view. A check
        that authorizes the query value and then loads the path value, or the
        reverse, would put the wrong marker in the body or allow the request.
        """
        before_alpha = _snapshot(self.pipeline_alpha.dir_path)
        before_beta = _snapshot(self.pipeline_beta.dir_path)
        response = self.fetch(
            self._url(
                self.pipeline_beta.uuid,
                query={
                    'block_uuid': BLOCK_UUID,
                    'pipeline_uuid': self.pipeline_alpha.uuid,
                },
            ),
            headers=self._headers(self.token_viewer_alpha),
        )
        self._assert_denied(response, [MARKER_ALPHA, MARKER_BETA])
        self.assertEqual(before_alpha, _snapshot(self.pipeline_alpha.dir_path))
        self.assertEqual(before_beta, _snapshot(self.pipeline_beta.dir_path))

    def test_pipeline_viewer_can_read_that_pipeline(self):
        response = self.fetch(
            self._url(self.pipeline_alpha.uuid),
            headers=self._headers(self.token_viewer_alpha),
        )
        self._assert_allowed(response, MARKER_ALPHA, [MARKER_BETA])

    def test_project_viewer_can_read_pipeline_analysis(self):
        response = self.fetch(
            self._url(self.pipeline_beta.uuid),
            headers=self._headers(self.token_project_viewer),
        )
        self._assert_allowed(response, MARKER_BETA, [MARKER_ALPHA])

    def test_missing_pipeline_is_not_created_for_an_anonymous_caller(self):
        missing_uuid = 'missing_pipeline_uuid'
        pipeline_dir = os.path.join(self.repo_path, 'pipelines', missing_uuid)
        self.assertFalse(os.path.exists(pipeline_dir))
        before = set(os.listdir(os.path.join(self.repo_path, 'pipelines')))
        response = self.fetch(self._url(missing_uuid))
        self._assert_denied(response, [MARKER_ALPHA, MARKER_BETA])
        self.assertFalse(os.path.exists(pipeline_dir))
        self.assertEqual(before, set(os.listdir(os.path.join(self.repo_path, 'pipelines'))))

    def test_other_methods_do_not_return_analysis_without_authentication(self):
        # ApiPipelineBlockAnalysisHandler implements get only. POST, PUT, and
        # DELETE are not separate analysis reads today; they must not start
        # returning the records without the same authentication.
        for method in ('POST', 'PUT', 'DELETE'):
            kwargs = {}
            if method != 'DELETE':
                kwargs['body'] = b'{}'
                kwargs['headers'] = {'Content-Type': 'application/json'}
            response = self.fetch(
                self._url(self.pipeline_alpha.uuid),
                method=method,
                **kwargs,
            )
            body = self._body(response)
            self.assertNotIn(MARKER_ALPHA, body)
            self.assertNotIn(MARKER_BETA, body)
            self.assertNotEqual(200, response.code)
