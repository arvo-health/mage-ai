import json
from json.decoder import JSONDecodeError
from typing import Dict, List, Optional, Tuple

from mage_ai import settings
from mage_ai.api.errors import ApiError
from mage_ai.api.utils import (
    has_at_least_editor_role,
    has_at_least_editor_role_for_event_matcher,
    has_at_least_editor_role_for_pipeline_schedule,
    has_at_least_viewer_role,
)
from mage_ai.data_preparation.repo_manager import get_project_uuid
from mage_ai.orchestration.constants import Entity
from mage_ai.orchestration.db.models.schedules import EventMatcher, PipelineSchedule
from mage_ai.orchestration.pipeline_scheduler import (
    get_pipeline_schedules_matching_event,
    schedule_with_event,
)
from mage_ai.server.api.base import BaseApiHandler

WRITABLE_EVENT_MATCHER_ATTRIBUTES = [
    'event_type',
    'name',
    'pattern',
]


class BaseEventApiHandler(BaseApiHandler):
    def prepare(self):
        super().prepare()
        if self._finished:
            return

        if self.request.error:
            return self.render_error(self.request.error)

        if settings.REQUIRE_USER_AUTHENTICATION and not self.request.current_user:
            return self.render_error(ApiError.INVALID_OAUTH_TOKEN)

    def render_error(self, error: Dict):
        error = dict(error)
        self.set_status(error.get('code') or 500)
        self.finish(dict(error=error))

    def render_api_error(self, err: ApiError):
        self.render_error(dict(code=err.code, message=err.message, type=err.type))

    @property
    def user(self):
        return self.request.current_user

    def can_read_event_matchers(self) -> bool:
        return has_at_least_viewer_role(self.user, Entity.PROJECT, get_project_uuid())

    def can_create_unbound_event_matcher(self) -> bool:
        return has_at_least_editor_role(self.user, Entity.PROJECT, get_project_uuid())

    def get_event_matcher(self, event_matcher_id) -> Optional[EventMatcher]:
        try:
            event_matcher_id = int(event_matcher_id)
        except (TypeError, ValueError):
            return None
        return EventMatcher.query.get(event_matcher_id)

    def authorize_event_matcher_payload(
        self,
        payload: Dict,
        event_matcher: EventMatcher = None,
    ) -> Tuple[Optional[EventMatcher], Dict, Optional[List[PipelineSchedule]]]:
        """
        Resolve and authorize everything the write will touch: the existing matcher and every
        schedule it will be bound to. The returned objects are what gets written.
        """
        if not isinstance(payload, dict):
            raise ApiError(ApiError.RESOURCE_INVALID)

        if event_matcher is None and payload.get('id') is not None:
            event_matcher = self.get_event_matcher(payload.get('id'))
            if event_matcher is None:
                raise ApiError(ApiError.RESOURCE_NOT_FOUND)

        if event_matcher is not None and \
                not has_at_least_editor_role_for_event_matcher(self.user, event_matcher):
            raise ApiError(ApiError.UNAUTHORIZED_ACCESS)

        pipeline_schedules = None
        pipeline_schedule_ids = payload.get('pipeline_schedule_ids')
        if pipeline_schedule_ids is not None:
            try:
                pipeline_schedule_ids = {int(i) for i in pipeline_schedule_ids}
            except (TypeError, ValueError):
                raise ApiError(ApiError.RESOURCE_INVALID)

            pipeline_schedules = PipelineSchedule.query.filter(
                PipelineSchedule.id.in_(pipeline_schedule_ids),
            ).all()
            if len(pipeline_schedules) != len(pipeline_schedule_ids):
                raise ApiError(ApiError.RESOURCE_NOT_FOUND)

            for pipeline_schedule in pipeline_schedules:
                if not has_at_least_editor_role_for_pipeline_schedule(
                    self.user,
                    pipeline_schedule,
                ):
                    raise ApiError(ApiError.UNAUTHORIZED_ACCESS)

        if event_matcher is None and not pipeline_schedules and \
                not self.can_create_unbound_event_matcher():
            raise ApiError(ApiError.UNAUTHORIZED_ACCESS)

        attributes = {
            k: payload[k] for k in WRITABLE_EVENT_MATCHER_ATTRIBUTES if k in payload
        }

        return event_matcher, attributes, pipeline_schedules


class ApiEventHandler(BaseEventApiHandler):
    def post(self):
        try:
            payload = self.get_payload()
        except (JSONDecodeError, UnicodeDecodeError):
            return self.render_error(ApiError.RESOURCE_INVALID)

        matched_pipeline_schedules = get_pipeline_schedules_matching_event(payload)
        pipeline_schedules = [
            pipeline_schedule for pipeline_schedule in matched_pipeline_schedules
            if has_at_least_editor_role_for_pipeline_schedule(self.user, pipeline_schedule)
        ]
        if matched_pipeline_schedules and not pipeline_schedules:
            return self.render_error(ApiError.UNAUTHORIZED_ACCESS)

        print(f'Trigger by event: {payload}')
        schedule_with_event(payload, pipeline_schedules=pipeline_schedules)
        self.write(dict(event=payload))


class ApiEventMatcherDetailHandler(BaseEventApiHandler):
    model_class = EventMatcher

    def get(self, event_matcher_id):
        if not self.can_read_event_matchers():
            return self.render_error(ApiError.UNAUTHORIZED_ACCESS)

        event_matcher = self.get_event_matcher(event_matcher_id)
        if event_matcher is None:
            return self.render_error(ApiError.RESOURCE_NOT_FOUND)

        include_attributes = []
        if self.get_bool_argument('include_pipeline_schedules', False):
            include_attributes.append('pipeline_schedules')
        self.write_model(event_matcher, include_attributes=include_attributes)

    def put(self, event_matcher_id):
        event_matcher = self.get_event_matcher(event_matcher_id)
        if event_matcher is None:
            return self.render_error(ApiError.RESOURCE_NOT_FOUND)

        try:
            event_matcher, attributes, pipeline_schedules = \
                self.authorize_event_matcher_payload(
                    self.get_payload(),
                    event_matcher=event_matcher,
                )
        except ApiError as err:
            return self.render_api_error(err)

        if pipeline_schedules is not None:
            attributes['pipeline_schedules'] = pipeline_schedules
        event_matcher.update(**attributes)
        self.write_model(event_matcher)

    def delete(self, event_matcher_id):
        event_matcher = self.get_event_matcher(event_matcher_id)
        if event_matcher is None:
            return self.render_error(ApiError.RESOURCE_NOT_FOUND)

        if not has_at_least_editor_role_for_event_matcher(self.user, event_matcher):
            return self.render_error(ApiError.UNAUTHORIZED_ACCESS)

        event_matcher.delete()
        self.write_model(event_matcher)


class ApiEventMatcherListHandler(BaseEventApiHandler):
    model_class = EventMatcher

    def get(self):
        if not self.can_read_event_matchers():
            return self.render_error(ApiError.UNAUTHORIZED_ACCESS)

        event_matchers = EventMatcher.query.all()
        collection = [e.to_dict() for e in event_matchers]
        self.write(dict(event_matchers=collection))
        self.finish()

    def post(self):
        try:
            body = json.loads(self.request.body or '{}')
        except (JSONDecodeError, UnicodeDecodeError):
            return self.render_error(ApiError.RESOURCE_INVALID)
        if not isinstance(body, dict):
            return self.render_error(ApiError.RESOURCE_INVALID)

        arr = body.get('event_matchers') or []
        if not isinstance(arr, list):
            return self.render_error(ApiError.RESOURCE_INVALID)
        if len(arr) == 0:
            arr.append(self.get_payload())

        try:
            entries = [self.authorize_event_matcher_payload(payload) for payload in arr]
        except ApiError as err:
            return self.render_api_error(err)

        event_matchers = EventMatcher.save_batch(entries)

        if len(event_matchers) >= 2:
            self.write(dict(event_matchers=[em.to_dict() for em in event_matchers]))
        else:
            self.write(dict(event_matcher=event_matchers[0].to_dict()))
