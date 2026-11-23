from types import SimpleNamespace
from typing import Dict

from mage_ai.api.errors import ApiError
from mage_ai.api.operations.constants import OperationType
from mage_ai.api.policies.BlockPolicy import BlockPolicy
from mage_ai.data_preparation.models.pipeline import Pipeline
from mage_ai.server.api.base import BaseApiHandler
from mage_ai.settings.repo import get_repo_path


class ApiPipelineBlockAnalysisHandler(BaseApiHandler):
    async def get(self, pipeline_uuid, block_uuid):
        if self.request.error:
            return self.__write_error(self.request.error)

        user = self.request.current_user

        # Authorize against the pipeline uuid from the path before anything is read from or
        # written to disk; the pipeline loaded afterwards must be this exact pipeline.
        policy = BlockPolicy(
            None,
            user,
            parent_model=SimpleNamespace(uuid=pipeline_uuid),
        )
        try:
            await policy.authorize_action(OperationType.DETAIL)
        except ApiError as err:
            return self.__write_error(dict(
                code=err.code,
                message=err.message,
                type=err.type,
            ))

        pipeline = Pipeline.get(
            pipeline_uuid,
            repo_path=get_repo_path(user=user),
            check_if_exists=True,
        )
        if pipeline is None or pipeline.uuid != pipeline_uuid:
            return self.__write_error(ApiError.RESOURCE_NOT_FOUND)

        block = pipeline.get_block(block_uuid)
        if block is None or block.pipeline_uuid != pipeline_uuid:
            return self.__write_error(ApiError.RESOURCE_NOT_FOUND)

        analyses = block.get_analyses()
        self.write(dict(analyses=analyses))

    def __write_error(self, error: Dict):
        self.set_status(error.get('code') or 500)
        self.write(dict(error=error))
