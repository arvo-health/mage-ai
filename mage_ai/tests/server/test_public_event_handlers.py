"""Security spec for event ingestion and event-matcher handlers.

These tests describe the required behavior when user authentication is on.
They fail while the handlers stay open, while an empty matcher pattern
matches every event, or while a caller can bind or start a pipeline schedule
they are not allowed to run.
"""
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from tornado.testing import AsyncHTTPTestCase

from mage_ai.api.utils import (
    authenticate_client_and_token,
    has_at_least_editor_role,
    has_at_least_viewer_role,
)
from mage_ai.authentication.permissions.constants import PermissionAccess
from mage_ai.data_preparation.models.triggers import ScheduleStatus, ScheduleType
from mage_ai.orchestration.constants import Entity
from mage_ai.orchestration.db import db_connection
from mage_ai.orchestration.db.models.oauth import (
    Oauth2AccessToken,
    Oauth2Application,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from mage_ai.orchestration.db.models.schedules import (
    BlockRun,
    EventMatcher,
    PipelineRun,
    PipelineSchedule,
    pipeline_schedule_event_matcher_association_table,
)
from mage_ai.orchestration.pipeline_scheduler import schedule_all
from mage_ai.server.api.constants import HEADER_API_KEY, HEADER_OAUTH_TOKEN
from mage_ai.server.server import make_app
from mage_ai.settings import OAUTH2_APPLICATION_CLIENT_ID
from mage_ai.tests.base_test import DBTestCase
from mage_ai.tests.factory import create_pipeline_with_blocks

EDITOR_TOKEN = 'placeholder-editor-token'
VIEWER_TOKEN = 'placeholder-viewer-token'
PATTERN_SENTINEL = 'stored-pattern-sentinel'
EVENT_MARKER = 'attacker-event-marker'
AUTHORIZED_MARKER = 'authorized-event-marker'


class PublicEventHandlerTests(AsyncHTTPTestCase, DBTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pipeline_a = create_pipeline_with_blocks(
            'event auth pipeline a',
            cls.repo_path,
        )
        cls.pipeline_b = create_pipeline_with_blocks(
            'event auth pipeline b',
            cls.repo_path,
        )
        cls._create_users()

    @classmethod
    def _create_users(cls):
        Role.create_default_roles()
        viewer_role = Role.get_role(Role.DefaultRole.VIEWER)

        editor_role = Role.create(name='pipeline-a-only-editor')
        editor_permission = Permission.create(
            access=PermissionAccess.EDITOR.value,
            entity=Entity.PIPELINE,
            entity_id=cls.pipeline_a.uuid,
            role_id=editor_role.id,
        )
        RolePermission.create(
            permission_id=editor_permission.id,
            role_id=editor_role.id,
        )

        cls.viewer = User.create(
            email='event-viewer@example.com',
            roles=0,
            username='event-viewer',
            roles_new=[viewer_role],
        )
        cls.editor = User.create(
            email='event-editor@example.com',
            roles=0,
            username='event-editor',
            roles_new=[editor_role],
        )
        UserRole.create(role_id=viewer_role.id, user_id=cls.viewer.id)
        UserRole.create(role_id=editor_role.id, user_id=cls.editor.id)

        application = Oauth2Application.create(
            client_id=OAUTH2_APPLICATION_CLIENT_ID,
            client_type=Oauth2Application.ClientType.PUBLIC,
            name='frontend',
            user_id=cls.editor.id,
        )
        expires = datetime.utcnow() + timedelta(days=1)
        Oauth2AccessToken.create(
            expires=expires,
            oauth2_application_id=application.id,
            token=EDITOR_TOKEN,
            user_id=cls.editor.id,
        )
        Oauth2AccessToken.create(
            expires=expires,
            oauth2_application_id=application.id,
            token=VIEWER_TOKEN,
            user_id=cls.viewer.id,
        )

    def setUp(self):
        self._auth_patches = [
            patch('mage_ai.api.middleware.REQUIRE_USER_AUTHENTICATION', True),
            patch('mage_ai.api.policies.BasePolicy.REQUIRE_USER_AUTHENTICATION', True),
            patch('mage_ai.settings.REQUIRE_USER_AUTHENTICATION', True),
            patch('mage_ai.settings.server.REQUIRE_USER_AUTHENTICATION', True),
        ]
        for auth_patch in self._auth_patches:
            auth_patch.start()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self._reset_trigger_state()
        for auth_patch in self._auth_patches:
            auth_patch.stop()

    def get_app(self):
        return make_app()

    def _reset_trigger_state(self):
        BlockRun.query.delete()
        PipelineRun.query.delete()
        db_connection.session.execute(
            pipeline_schedule_event_matcher_association_table.delete(),
        )
        EventMatcher.query.delete()
        PipelineSchedule.query.delete()
        db_connection.session.commit()

    def _headers(self, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers[HEADER_API_KEY] = OAUTH2_APPLICATION_CLIENT_ID
            headers[HEADER_OAUTH_TOKEN] = token
        return headers

    def _request(self, path, method='GET', payload=None, token=None):
        kwargs = {'method': method, 'headers': self._headers(token)}
        if payload is not None:
            kwargs['body'] = json.dumps(payload).encode()
        return self.fetch(path, **kwargs)

    def _schedule(self, pipeline, name, status=ScheduleStatus.ACTIVE):
        return PipelineSchedule.create(
            name=name,
            pipeline_uuid=pipeline.uuid,
            schedule_interval=None,
            schedule_type=ScheduleType.EVENT,
            status=status,
        )

    def _state(self):
        db_connection.session.expire_all()
        matchers = []
        for matcher in EventMatcher.query.order_by(EventMatcher.id).all():
            matchers.append({
                'id': matcher.id,
                'name': matcher.name,
                'pattern': matcher.pattern,
                'schedule_ids': sorted(
                    schedule.id for schedule in matcher.pipeline_schedules
                ),
            })
        runs = []
        for run in PipelineRun.query.order_by(PipelineRun.id).all():
            runs.append({
                'schedule_id': run.pipeline_schedule_id,
                'event': (run.variables or {}).get('event'),
                'status': run.status.value if run.status else None,
            })
        return {'matchers': matchers, 'runs': runs}

    def _contains(self, value, marker):
        if value == marker:
            return True
        if isinstance(value, dict):
            return any(self._contains(item, marker) for item in value.values())
        if isinstance(value, list):
            return any(self._contains(item, marker) for item in value)
        return False

    def _queued_events(self):
        recorded = []
        manager = MagicMock()

        def add_job(*args, **kwargs):
            recorded.append(args)

        manager.add_job.side_effect = add_job
        with patch(
            'mage_ai.orchestration.pipeline_scheduler_original.get_job_manager',
            return_value=manager,
        ):
            schedule_all()

        events = []
        for args in recorded:
            for arg in args:
                if isinstance(arg, dict) and 'event' in arg:
                    events.append(arg['event'])
        return events

    def _patterns(self, response):
        try:
            payload = json.loads(response.body.decode())
        except Exception:
            return []
        found = []
        if isinstance(payload, dict):
            matcher = payload.get('event_matcher')
            if isinstance(matcher, dict):
                found.append(matcher.get('pattern'))
            for item in payload.get('event_matchers') or []:
                if isinstance(item, dict):
                    found.append(item.get('pattern'))
        return found

    def _runs_for(self, schedule):
        db_connection.session.expire_all()
        return PipelineRun.query.filter(
            PipelineRun.pipeline_schedule_id == schedule.id,
        ).all()

    def test_role_fixtures_match_pipeline_authorization(self):
        application = Oauth2Application.query.filter(
            Oauth2Application.client_id == OAUTH2_APPLICATION_CLIENT_ID,
        ).one()
        editor_token, editor_valid = authenticate_client_and_token(
            application.id,
            EDITOR_TOKEN,
        )
        viewer_token, viewer_valid = authenticate_client_and_token(
            application.id,
            VIEWER_TOKEN,
        )
        self.assertTrue(editor_valid)
        self.assertTrue(viewer_valid)
        self.assertTrue(has_at_least_editor_role(
            editor_token.user,
            Entity.PIPELINE,
            self.pipeline_a.uuid,
        ))
        self.assertFalse(has_at_least_editor_role(
            editor_token.user,
            Entity.PIPELINE,
            self.pipeline_b.uuid,
        ))
        self.assertFalse(has_at_least_editor_role(
            viewer_token.user,
            Entity.PIPELINE,
            self.pipeline_a.uuid,
        ))
        self.assertTrue(has_at_least_viewer_role(
            viewer_token.user,
            Entity.PIPELINE,
            self.pipeline_a.uuid,
        ))

    def test_unauthenticated_handlers_do_not_read_change_or_start_pipelines(self):
        schedule = self._schedule(self.pipeline_a, 'active event schedule')
        other = self._schedule(self.pipeline_b, 'other active event schedule')
        matcher = EventMatcher.create(
            name='stored matcher',
            pattern={'source': [PATTERN_SENTINEL]},
        )
        matcher.update(pipeline_schedules=[schedule])
        before = self._state()

        protected = self._request('/api/pipelines')
        listed = self._request('/api/event_matchers')
        detail = self._request(
            f'/api/event_matchers/{matcher.id}?include_pipeline_schedules=true',
        )
        created = self._request(
            '/api/event_matchers',
            method='POST',
            payload={
                'event_matcher': {
                    'name': 'match all',
                    'pattern': {},
                    'pipeline_schedule_ids': [schedule.id, other.id],
                },
            },
        )
        created_batch = self._request(
            '/api/event_matchers',
            method='POST',
            payload={
                'event_matchers': [
                    {
                        'name': 'batch match all',
                        'pattern': {},
                        'pipeline_schedule_ids': [other.id],
                    },
                    {
                        'id': matcher.id,
                        'pattern': {},
                        'pipeline_schedule_ids': [schedule.id, other.id],
                    },
                ],
            },
        )
        updated = self._request(
            f'/api/event_matchers/{matcher.id}',
            method='PUT',
            payload={
                'event_matcher': {
                    'pattern': {},
                    'pipeline_schedule_ids': [other.id],
                },
            },
        )
        deleted = self._request(
            f'/api/event_matchers/{matcher.id}',
            method='DELETE',
        )
        triggered = self._request(
            '/api/events',
            method='POST',
            payload={'marker': EVENT_MARKER},
        )
        queued = self._queued_events()

        problems = []
        responses = {
            'protected pipelines': protected,
            'list event matchers': listed,
            'detail event matcher': detail,
            'create event matcher': created,
            'batch upsert event matchers': created_batch,
            'update event matcher': updated,
            'delete event matcher': deleted,
            'ingest event': triggered,
        }
        for label, response in responses.items():
            if response.code not in (401, 403):
                problems.append(f'{label} returned {response.code}')
        if self._state() != before:
            problems.append('event matcher or pipeline run state changed')
        if any(
            self._contains(pattern, PATTERN_SENTINEL)
            for pattern in self._patterns(listed) + self._patterns(detail)
        ):
            problems.append('event matcher response included stored patterns')
        if any(self._contains(event, EVENT_MARKER) for event in queued):
            problems.append('scheduler queued a block run with the posted event')
        if any(self._contains(event, PATTERN_SENTINEL) for event in queued):
            problems.append('scheduler queued a block run for the stored matcher')
        self.assertEqual(problems, [])

    def test_viewer_can_read_but_cannot_bind_or_start_schedules(self):
        schedule = self._schedule(self.pipeline_a, 'viewer target schedule')
        matcher = EventMatcher.create(
            name='viewer readable matcher',
            pattern={'source': [PATTERN_SENTINEL]},
        )
        matcher.update(pipeline_schedules=[schedule])
        before = self._state()

        listed = self._request('/api/event_matchers', token=VIEWER_TOKEN)
        detail = self._request(
            f'/api/event_matchers/{matcher.id}?include_pipeline_schedules=true',
            token=VIEWER_TOKEN,
        )
        triggered = self._request(
            '/api/events',
            method='POST',
            payload={'source': PATTERN_SENTINEL, 'marker': EVENT_MARKER},
            token=VIEWER_TOKEN,
        )
        created = self._request(
            '/api/event_matchers',
            method='POST',
            payload={
                'event_matcher': {
                    'name': 'viewer matcher',
                    'pattern': {'source': ['viewer']},
                    'pipeline_schedule_ids': [schedule.id],
                },
            },
            token=VIEWER_TOKEN,
        )
        updated = self._request(
            f'/api/event_matchers/{matcher.id}',
            method='PUT',
            payload={
                'event_matcher': {
                    'pattern': {'source': ['changed']},
                    'pipeline_schedule_ids': [schedule.id],
                },
            },
            token=VIEWER_TOKEN,
        )
        deleted = self._request(
            f'/api/event_matchers/{matcher.id}',
            method='DELETE',
            token=VIEWER_TOKEN,
        )

        problems = []
        if listed.code != 200:
            problems.append(f'viewer list returned {listed.code}')
        if detail.code != 200:
            problems.append(f'viewer detail returned {detail.code}')
        for label, response in (
            ('viewer create', created),
            ('viewer update', updated),
            ('viewer delete', deleted),
            ('viewer event', triggered),
        ):
            if response.code not in (401, 403):
                problems.append(f'{label} returned {response.code}')
        if self._state() != before:
            problems.append('viewer changed matchers or started a pipeline run')
        self.assertEqual(problems, [])

    def test_editor_cannot_bind_or_start_a_schedule_they_cannot_run(self):
        schedule_a = self._schedule(self.pipeline_a, 'editor owned schedule')
        schedule_b = self._schedule(self.pipeline_b, 'other pipeline schedule')
        matcher_a = EventMatcher.create(
            name='owned matcher',
            pattern={'owned': ['yes']},
        )
        matcher_a.update(pipeline_schedules=[schedule_a])
        matcher_b = EventMatcher.create(
            name='foreign matcher',
            pattern={'foreign': ['yes']},
        )
        matcher_b.update(pipeline_schedules=[schedule_b])
        foreign_before = matcher_b.pattern

        responses = [
            self._request(
                '/api/event_matchers',
                method='POST',
                payload={
                    'event_matcher': {
                        'name': 'bind both',
                        'pattern': {'bind': ['both']},
                        'pipeline_schedule_ids': [schedule_a.id, schedule_b.id],
                    },
                },
                token=EDITOR_TOKEN,
            ),
            self._request(
                '/api/event_matchers',
                method='POST',
                payload={
                    'event_matchers': [{
                        'name': 'bind foreign first',
                        'pattern': {'bind': ['foreign-first']},
                        'pipeline_schedule_ids': [schedule_b.id, schedule_a.id],
                    }],
                },
                token=EDITOR_TOKEN,
            ),
            self._request(
                '/api/event_matchers',
                method='POST',
                payload={
                    'event_matchers': [{
                        'id': matcher_b.id,
                        'pattern': {'hijacked': ['yes']},
                        'pipeline_schedule_ids': [schedule_b.id],
                    }],
                },
                token=EDITOR_TOKEN,
            ),
            self._request(
                f'/api/event_matchers/{matcher_a.id}',
                method='PUT',
                payload={
                    'event_matcher': {
                        'pipeline_schedule_ids': [schedule_a.id, schedule_b.id],
                    },
                },
                token=EDITOR_TOKEN,
            ),
            self._request(
                '/api/events',
                method='POST',
                payload={'bind': 'both', 'marker': EVENT_MARKER},
                token=EDITOR_TOKEN,
            ),
            self._request(
                '/api/events',
                method='POST',
                payload={'hijacked': 'yes', 'marker': EVENT_MARKER},
                token=EDITOR_TOKEN,
            ),
        ]

        db_connection.session.expire_all()
        problems = []
        for index, response in enumerate(responses):
            if response.code not in (200, 400, 401, 403):
                problems.append(f'request {index} returned {response.code}')
        linked_to_b = []
        for matcher in EventMatcher.query.all():
            if schedule_b.id in [item.id for item in matcher.pipeline_schedules]:
                linked_to_b.append(matcher.id)
        if linked_to_b != [matcher_b.id]:
            problems.append(f'schedule B is linked to matchers {linked_to_b}')
        matcher_b = EventMatcher.query.get(matcher_b.id)
        if matcher_b is None or matcher_b.pattern != foreign_before:
            problems.append('foreign matcher pattern changed')
        if self._runs_for(schedule_b):
            problems.append('pipeline run created for the other pipeline')
        self.assertEqual(problems, [])

    def test_empty_pattern_does_not_start_an_authorized_schedule(self):
        schedule = self._schedule(self.pipeline_a, 'empty pattern schedule')
        seeded = EventMatcher.create(
            name='seeded empty pattern',
            pattern={},
        )
        seeded.update(pipeline_schedules=[schedule])

        created = self._request(
            '/api/event_matchers',
            method='POST',
            payload={
                'event_matcher': {
                    'name': 'created empty pattern',
                    'pattern': {},
                    'pipeline_schedule_ids': [schedule.id],
                },
            },
            token=EDITOR_TOKEN,
        )
        triggered = self._request(
            '/api/events',
            method='POST',
            payload={'marker': EVENT_MARKER, 'anything': True},
            token=EDITOR_TOKEN,
        )
        queued = self._queued_events()

        problems = []
        if created.code not in (200, 400, 401, 403):
            problems.append(f'create empty pattern returned {created.code}')
        if triggered.code not in (200, 400, 401, 403):
            problems.append(f'event post returned {triggered.code}')
        if self._runs_for(schedule):
            problems.append('empty pattern started the schedule')
        if any(self._contains(event, EVENT_MARKER) for event in queued):
            problems.append('scheduler queued the event for an empty pattern')
        db_connection.session.expire_all()
        for matcher in EventMatcher.query.all():
            if matcher.pattern == {} and matcher.match({'marker': EVENT_MARKER}):
                problems.append(f'matcher {matcher.id} empty pattern matches any event')
        self.assertEqual(problems, [])

    def test_editor_can_start_only_the_matching_allowed_schedule(self):
        schedule = self._schedule(self.pipeline_a, 'matching schedule')
        inactive = self._schedule(
            self.pipeline_a,
            'inactive matching schedule',
            status=ScheduleStatus.INACTIVE,
        )
        created = self._request(
            '/api/event_matchers',
            method='POST',
            payload={
                'event_matcher': {
                    'name': 'deploy matcher',
                    'pattern': {'kind': ['deploy']},
                    'pipeline_schedule_ids': [schedule.id],
                },
            },
            token=EDITOR_TOKEN,
        )
        EventMatcher.create(
            name='inactive matcher',
            pattern={'kind': ['deploy']},
        ).update(pipeline_schedules=[inactive])

        matched = self._request(
            '/api/events',
            method='POST',
            payload={'kind': 'deploy', 'marker': AUTHORIZED_MARKER},
            token=EDITOR_TOKEN,
        )
        runs = self._runs_for(schedule)
        queued = self._queued_events()
        missed = self._request(
            '/api/events',
            method='POST',
            payload={'kind': 'other', 'marker': EVENT_MARKER},
            token=EDITOR_TOKEN,
        )

        problems = []
        if created.code != 200:
            problems.append(f'create matcher returned {created.code}')
        if matched.code != 200:
            problems.append(f'matching event returned {matched.code}')
        if len(runs) != 1:
            problems.append(f'expected one pipeline run, found {len(runs)}')
        elif (runs[0].variables or {}).get('event', {}).get('marker') != AUTHORIZED_MARKER:
            problems.append('pipeline run variables do not contain the posted event')
        if not any(self._contains(event, AUTHORIZED_MARKER) for event in queued):
            problems.append('scheduler did not queue the matching event')
        if self._runs_for(inactive):
            problems.append('inactive schedule started')
        if len(self._runs_for(schedule)) != 1:
            problems.append('non-matching event started another run')
        if missed.code not in (200, 400):
            problems.append(f'non-matching event returned {missed.code}')
        self.assertEqual(problems, [])
