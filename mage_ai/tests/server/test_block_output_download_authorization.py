import logging
import os
import secrets
import shutil
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

import pandas as pd
import tornado.testing

from mage_ai.api.utils import has_at_least_viewer_role
from mage_ai.authentication.oauth2 import generate_access_token
from mage_ai.data_preparation.models.block import Block
from mage_ai.data_preparation.models.constants import DATAFRAME_SAMPLE_COUNT
from mage_ai.data_preparation.models.pipeline import Pipeline
from mage_ai.data_preparation.models.triggers import ScheduleType
from mage_ai.data_preparation.repo_manager import get_project_uuid, init_project_uuid
from mage_ai.orchestration.constants import Entity
from mage_ai.orchestration.db import TEST_DB, db_connection
from mage_ai.orchestration.db.database_manager import database_manager
from mage_ai.orchestration.db.models.oauth import Oauth2Application, Permission, Role
from mage_ai.orchestration.db.models.schedules import PipelineRun, PipelineSchedule
from mage_ai.server.server import make_app
from mage_ai.settings.repo import get_variables_dir, set_repo_path
from mage_ai.tests.factory import create_user


def _output_frame(marker):
    row_count = DATAFRAME_SAMPLE_COUNT + 1
    values = ['row-{0}'.format(index) for index in range(row_count)]
    values[-1] = marker
    return pd.DataFrame({'warehouse_value': values})


class BlockOutputDownloadAuthorizationTest(tornado.testing.AsyncHTTPTestCase):
    """
    Spec for GET /api/pipelines/{pipeline_uuid}/block_outputs/{block_uuid}/downloads.

    The route already accepts a valid session. These tests require the same project
    viewer rule as BlockOutputPolicy before any block output is written. They fail
    while a signed-in account without that role can still download the block.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repo_path = os.path.join(os.getcwd(), 'test')
        if os.path.exists(cls.repo_path):
            shutil.rmtree(cls.repo_path)
        set_repo_path(cls.repo_path)
        if not Path(cls.repo_path).exists():
            Path(cls.repo_path).mkdir()
        init_project_uuid()
        database_manager.run_migrations(log_level=40)
        db_connection.start_session(force=True)
        logging.getLogger('tornado').setLevel(logging.CRITICAL)

        cls.project_uuid = get_project_uuid()
        if not cls.project_uuid:
            raise RuntimeError('project uuid was not initialized')

        Role.create_default_roles()
        cls.viewer_role = Role.get_role(Role.DefaultRole.VIEWER)

        cls.marker_a = 'block-output-marker-pipeline-a'
        cls.marker_b = 'block-output-marker-pipeline-b'
        cls.marker_partition = 'block-output-marker-pipeline-run'
        cls.marker_other_partition = 'block-output-marker-other-run'

        cls.pipeline_a, cls.block_a = cls._pipeline_with_output(
            'download_auth_pipeline_a',
            'download_auth_block_a',
            cls.marker_a,
        )
        cls.pipeline_b, cls.block_b = cls._pipeline_with_output(
            'download_auth_pipeline_b',
            'download_auth_block_b',
            cls.marker_b,
        )

        cls.partition = 'download_auth_partition'
        cls.block_a.store_variables(
            {'output_0': _output_frame(cls.marker_partition)},
            execution_partition=cls.partition,
        )
        schedule = PipelineSchedule.create(
            name='download_auth_trigger',
            pipeline_uuid=cls.pipeline_a.uuid,
            schedule_type=ScheduleType.TIME,
        )
        cls.pipeline_run = PipelineRun.create(
            create_block_runs=False,
            pipeline_schedule_id=schedule.id,
            pipeline_uuid=cls.pipeline_a.uuid,
            variables={'execution_partition': cls.partition},
        )

        other_partition = 'download_auth_other_partition'
        cls.block_b.store_variables(
            {'output_0': _output_frame(cls.marker_other_partition)},
            execution_partition=other_partition,
        )
        other_schedule = PipelineSchedule.create(
            name='download_auth_other_trigger',
            pipeline_uuid=cls.pipeline_b.uuid,
            schedule_type=ScheduleType.TIME,
        )
        cls.other_pipeline_run = PipelineRun.create(
            create_block_runs=False,
            pipeline_schedule_id=other_schedule.id,
            pipeline_uuid=cls.pipeline_b.uuid,
            variables={'execution_partition': other_partition},
        )

        cls.owner = create_user(
            _owner=True,
            email='download-auth-owner@example.com',
            username='download_auth_owner',
        )
        cls.project_viewer = create_user(
            email='download-auth-viewer@example.com',
            roles_new=[cls.viewer_role],
            username='download_auth_viewer',
        )
        cls.legacy_viewer = create_user(
            email='download-auth-legacy@example.com',
            roles=4,
            username='download_auth_legacy',
        )
        cls.project_permission_viewer = create_user(
            email='download-auth-project@example.com',
            roles_new=[Role.create(
                name='download_auth_project_viewer',
                permissions=[Permission.create(
                    access=Permission.Access.VIEWER.value,
                    entity=Entity.PROJECT,
                    entity_id=cls.project_uuid,
                )],
            )],
            username='download_auth_project',
        )
        cls.other_project_viewer = create_user(
            email='download-auth-other-project@example.com',
            roles_new=[Role.create(
                name='download_auth_other_project_viewer',
                permissions=[Permission.create(
                    access=Permission.Access.VIEWER.value,
                    entity=Entity.PROJECT,
                    entity_id='different-project',
                )],
            )],
            username='download_auth_other_project',
        )
        cls.pipeline_only_viewer = create_user(
            email='download-auth-pipeline@example.com',
            roles_new=[Role.create(
                name='download_auth_pipeline_viewer',
                permissions=[Permission.create(
                    access=Permission.Access.VIEWER.value,
                    entity=Entity.PIPELINE,
                    entity_id=cls.pipeline_a.uuid,
                )],
            )],
            username='download_auth_pipeline',
        )
        cls.no_role_user = create_user(
            email='download-auth-norole@example.com',
            username='download_auth_norole',
        )

        cls.api_key = secrets.token_urlsafe()
        cls.oauth_client = Oauth2Application.create(
            client_id=cls.api_key,
            client_type=Oauth2Application.ClientType.PUBLIC,
            name='frontend',
            user_id=cls.owner.id,
        )
        cls.tokens = {
            'owner': generate_access_token(cls.owner, application=cls.oauth_client).token,
            'project_viewer': generate_access_token(
                cls.project_viewer,
                application=cls.oauth_client,
            ).token,
            'legacy_viewer': generate_access_token(
                cls.legacy_viewer,
                application=cls.oauth_client,
            ).token,
            'project_permission_viewer': generate_access_token(
                cls.project_permission_viewer,
                application=cls.oauth_client,
            ).token,
            'other_project_viewer': generate_access_token(
                cls.other_project_viewer,
                application=cls.oauth_client,
            ).token,
            'pipeline_only_viewer': generate_access_token(
                cls.pipeline_only_viewer,
                application=cls.oauth_client,
            ).token,
            'no_role_user': generate_access_token(
                cls.no_role_user,
                application=cls.oauth_client,
            ).token,
        }
        db_connection.session.commit()

    @classmethod
    def tearDownClass(cls):
        db_connection.close_session()
        try:
            shutil.rmtree(cls.repo_path)
            shutil.rmtree(get_variables_dir())
        except Exception:
            pass
        if Path(TEST_DB).is_file():
            Path(TEST_DB).unlink()
        super().tearDownClass()

    @classmethod
    def _pipeline_with_output(cls, pipeline_name, block_name, marker):
        pipeline = Pipeline.create(pipeline_name, repo_path=cls.repo_path)
        block = Block.create(
            block_name,
            'data_loader',
            cls.repo_path,
            pipeline=pipeline,
        )
        block.store_variables({'output_0': _output_frame(marker)})
        return pipeline, block

    def setUp(self):
        super().setUp()
        self.auth_patch = patch(
            'mage_ai.server.api.downloads.REQUIRE_USER_AUTHENTICATION',
            True,
        )
        self.auth_patch.start()

    def tearDown(self):
        self.auth_patch.stop()
        super().tearDown()

    def get_app(self):
        return make_app()

    def _download(self, token, pipeline_uuid, block_uuid, pipeline_run_id=None):
        params = {'api_key': self.api_key}
        if token is not None:
            params['token'] = token
        if pipeline_run_id is not None:
            params['pipeline_run_id'] = str(pipeline_run_id)
        path = '/api/pipelines/{0}/block_outputs/{1}/downloads?{2}'.format(
            pipeline_uuid,
            block_uuid,
            urlencode(params),
        )
        try:
            response = self.fetch(path, raise_error=False)
        except Exception:
            raise AssertionError('block output download request failed') from None
        return response.code, response.body.decode('utf-8', errors='replace')

    def _assert_denied(self, token, pipeline, block, marker, pipeline_run_id=None):
        _code, body = self._download(
            token,
            pipeline.uuid,
            block.uuid,
            pipeline_run_id=pipeline_run_id,
        )
        for secret in (
            marker,
            self.marker_a,
            self.marker_b,
            self.marker_partition,
            self.marker_other_partition,
        ):
            leaked = secret in body
            self.assertFalse(leaked, 'download included block output')

    def _assert_full_output(self, token, pipeline, block, marker, pipeline_run_id=None):
        code, body = self._download(
            token,
            pipeline.uuid,
            block.uuid,
            pipeline_run_id=pipeline_run_id,
        )
        lines = body.splitlines()
        self.assertEqual(200, code)
        self.assertEqual(DATAFRAME_SAMPLE_COUNT + 2, len(lines))
        self.assertEqual('warehouse_value', lines[0])
        self.assertEqual(marker, lines[-1])
        forbidden = {
            self.marker_a,
            self.marker_b,
            self.marker_partition,
            self.marker_other_partition,
        }
        forbidden.discard(marker)
        for other_marker in forbidden:
            self.assertNotIn(other_marker, body)

    def test_role_fixtures_match_block_output_policy(self):
        project = (Entity.PROJECT, self.project_uuid)
        self.assertNotEqual('different-project', self.project_uuid)
        self.assertTrue(has_at_least_viewer_role(self.owner, *project))
        self.assertTrue(has_at_least_viewer_role(self.project_viewer, *project))
        self.assertTrue(has_at_least_viewer_role(self.legacy_viewer, *project))
        self.assertTrue(has_at_least_viewer_role(self.project_permission_viewer, *project))
        self.assertFalse(has_at_least_viewer_role(self.other_project_viewer, *project))
        self.assertFalse(has_at_least_viewer_role(self.pipeline_only_viewer, *project))
        self.assertFalse(has_at_least_viewer_role(self.no_role_user, *project))
        self.assertEqual([], list(self.no_role_user.roles_new))
        self.assertFalse(self.no_role_user._owner)

    def test_project_viewer_downloads_only_the_requested_block(self):
        self._assert_full_output(
            self.tokens['project_viewer'],
            self.pipeline_a,
            self.block_a,
            self.marker_a,
        )
        self._assert_full_output(
            self.tokens['project_viewer'],
            self.pipeline_b,
            self.block_b,
            self.marker_b,
        )

    def test_owner_and_legacy_and_project_permission_can_download(self):
        for key in ('owner', 'legacy_viewer', 'project_permission_viewer'):
            self._assert_full_output(
                self.tokens[key],
                self.pipeline_a,
                self.block_a,
                self.marker_a,
            )

    def test_project_viewer_downloads_the_pipeline_run_partition(self):
        self._assert_full_output(
            self.tokens['project_viewer'],
            self.pipeline_a,
            self.block_a,
            self.marker_partition,
            pipeline_run_id=self.pipeline_run.id,
        )

    def test_pipeline_run_id_does_not_select_a_different_pipeline(self):
        self._assert_denied(
            self.tokens['project_viewer'],
            self.pipeline_a,
            self.block_a,
            self.marker_other_partition,
            pipeline_run_id=self.other_pipeline_run.id,
        )

    def test_signed_in_user_without_a_role_cannot_download(self):
        self._assert_denied(
            self.tokens['no_role_user'],
            self.pipeline_a,
            self.block_a,
            self.marker_a,
        )
        self._assert_denied(
            self.tokens['no_role_user'],
            self.pipeline_b,
            self.block_b,
            self.marker_b,
        )

    def test_signed_in_user_without_a_role_cannot_download_pipeline_run(self):
        self._assert_denied(
            self.tokens['no_role_user'],
            self.pipeline_a,
            self.block_a,
            self.marker_partition,
            pipeline_run_id=self.pipeline_run.id,
        )

    def test_viewer_of_another_project_cannot_download_this_project(self):
        self._assert_denied(
            self.tokens['other_project_viewer'],
            self.pipeline_a,
            self.block_a,
            self.marker_a,
        )

    def test_pipeline_only_viewer_cannot_download(self):
        self._assert_denied(
            self.tokens['pipeline_only_viewer'],
            self.pipeline_a,
            self.block_a,
            self.marker_a,
        )

    def test_missing_session_cannot_download(self):
        self._assert_denied(None, self.pipeline_a, self.block_a, self.marker_a)
