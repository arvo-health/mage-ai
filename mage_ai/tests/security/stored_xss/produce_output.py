"""Build the block-output objects Mage stores and later sends to the notebook."""

import json
from enum import Enum

import pandas as pd

from mage_ai.data_preparation.models.block.outputs import format_output_data
from mage_ai.server.kernel_output_parser import parse_output_message


class _Pipeline:
    uuid = 'pipe'
    variable_manager = None


class _Block:
    uuid = 'block_a'
    pipeline = _Pipeline()
    configuration = {}
    is_dynamic_v2 = False
    upstream_blocks = []
    replicated_block = None

    def get_analysis(self, **_kwargs):
        return None


def _encode(value):
    if isinstance(value, Enum):
        return value.value
    raise TypeError(type(value))


def main():
    script_markup = '<div><script>window.__mageXss=(window.__mageXss||0)+1</script></div>'
    handler_markup = '<img src="x" onerror="window.__mageXss=(window.__mageXss||0)+1">'
    block = _Block()

    table_script, _ = format_output_data(
        block,
        pd.DataFrame({'c': [script_markup, script_markup]}),
        'output_0',
    )
    table_handler, _ = format_output_data(
        block,
        pd.DataFrame({'c': [handler_markup]}),
        'output_0',
    )
    list_script, _ = format_output_data(block, [script_markup], 'output_0')
    kernel_html = parse_output_message({
        'header': {'msg_type': 'display_data'},
        'parent_header': {'msg_id': 'm1'},
        'content': {
            'data': {
                'text/plain': 'html',
                'text/html': script_markup,
            },
            'metadata': {},
        },
    })

    print(json.dumps({
        'kernel_html': kernel_html,
        'list_script': list_script,
        'table_handler': table_handler,
        'table_script': table_script,
    }, default=_encode))


if __name__ == '__main__':
    main()
