"""SQL built for Snowflake and Redshift must keep synced string values as data.

These tests fail while string values are interpolated by doubling single quotes
only. Snowflake and Redshift both treat a backslash inside a single-quoted
literal as an escape, so a backslash before a quote closes the literal early
and the rest of the value is parsed as SQL.

They pass once each value is either bound as a driver parameter or quoted so
that a backslash-aware literal decodes back to the original value.
"""
import io
import json
import sys
import types
import unittest
import unittest.mock


def _stub_module(name):
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


def _install_import_stubs():
    """Allow this test to import the destinations where optional drivers are absent.

    The drivers are not executed. The SQL assertion stops at the cursor the
    destination's connection already calls.
    """
    try:
        import singer  # noqa: F401
    except ImportError:
        singer = _stub_module('singer')

        class _SilentLog:
            def info(self, *args, **kwargs):
                pass

            def error(self, *args, **kwargs):
                pass

            def exception(self, *args, **kwargs):
                pass

            def debug(self, *args, **kwargs):
                pass

            def warning(self, *args, **kwargs):
                pass

        singer.get_logger = lambda *args, **kwargs: _SilentLog()

    try:
        import pandas  # noqa: F401
    except ImportError:
        pandas = _stub_module('pandas')
        pandas.DataFrame = object

    try:
        import snowflake.connector.pandas_tools  # noqa: F401
    except ImportError:
        snowflake = _stub_module('snowflake')
        connector = _stub_module('snowflake.connector')
        pandas_tools = _stub_module('snowflake.connector.pandas_tools')
        pandas_tools.write_pandas = lambda *args, **kwargs: None
        connector.connect = lambda **kwargs: None
        connector.pandas_tools = pandas_tools
        snowflake.connector = connector

    try:
        import redshift_connector  # noqa: F401
    except ImportError:
        redshift_connector = _stub_module('redshift_connector')
        redshift_connector.connect = lambda **kwargs: None


_install_import_stubs()

from mage_integrations.destinations.redshift import Redshift  # noqa: E402
from mage_integrations.destinations.snowflake import Snowflake  # noqa: E402


# Snowflake single-quoted literals. Documented escape table: a backslash starts
# an escape, \' is one quote, \\ is one backslash, and '' is also one quote.
# https://docs.snowflake.com/en/sql-reference/data-types-text
# Redshift QUOTE_LITERAL doubles embedded quotes and backslashes, so a single
# backslash is an escape there as well.
# https://docs.aws.amazon.com/redshift/latest/dg/r_QUOTE_LITERAL.html
_SIMPLE_ESCAPES = {
    "'": "'",
    '"': '"',
    '\\': '\\',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
}
_HEX_DIGITS = set('0123456789abcdefABCDEF')
_OCTAL_DIGITS = set('01234567')
MARKER = 'MAGE_BREAKOUT'
# Second column of a four-column INSERT (id, body, _mage_created_at, _mage_updated_at).
# After quote-doubling, \' becomes \'' which a backslash escape reads as
# "end of the literal", and the marker is then SQL rather than data.
BREAKOUT_VALUE = "\\' AS VARCHAR), NULL, NULL) " + MARKER + " --"
ARRAY_BREAKOUT_VALUE = "\\') " + MARKER + " --"


def split_backslash_escaped_sql(sql):
    """Return (code_outside_literals, [(decoded_literal, closed), ...]).

    Single-quoted literals use the Snowflake escape table above. Doubled quotes
    and backslash escapes are both decoded. Comments and double-quoted
    identifiers stay in the code region, so text that has left a literal is
    visible there.
    """
    code = []
    literals = []
    index = 0
    length = len(sql)
    while index < length:
        character = sql[index]
        if character == '-' and index + 1 < length and sql[index + 1] == '-':
            newline = sql.find('\n', index)
            if newline < 0:
                code.append(sql[index:])
                break
            code.append(sql[index:newline + 1])
            index = newline + 1
            continue
        if character == '/' and index + 1 < length and sql[index + 1] == '*':
            end = sql.find('*/', index + 2)
            if end < 0:
                code.append(sql[index:])
                break
            code.append(sql[index:end + 2])
            index = end + 2
            continue
        if character == '"':
            cursor = index + 1
            while cursor < length:
                if sql[cursor] == '"':
                    if cursor + 1 < length and sql[cursor + 1] == '"':
                        cursor += 2
                        continue
                    cursor += 1
                    break
                cursor += 1
            code.append(sql[index:cursor])
            index = cursor
            continue
        if character == "'":
            decoded, cursor, closed = _decode_literal(sql, index + 1)
            literals.append((decoded, closed))
            index = cursor
            continue
        code.append(character)
        index += 1
    return ''.join(code), literals


def _decode_literal(sql, index):
    decoded = []
    length = len(sql)
    while index < length:
        character = sql[index]
        if character == '\\':
            if index + 1 >= length:
                decoded.append('\\')
                index += 1
                break
            nxt = sql[index + 1]
            if nxt in _OCTAL_DIGITS:
                end = index + 1
                while end < length and end < index + 4 and sql[end] in _OCTAL_DIGITS:
                    end += 1
                decoded.append(chr(int(sql[index + 1:end], 8)))
                index = end
                continue
            if nxt == 'x' and index + 3 < length and set(sql[index + 2:index + 4]) <= _HEX_DIGITS:
                decoded.append(chr(int(sql[index + 2:index + 4], 16)))
                index += 4
                continue
            if nxt == 'u' and index + 5 < length and set(sql[index + 2:index + 6]) <= _HEX_DIGITS:
                decoded.append(chr(int(sql[index + 2:index + 6], 16)))
                index += 6
                continue
            if nxt in _SIMPLE_ESCAPES:
                decoded.append(_SIMPLE_ESCAPES[nxt])
                index += 2
                continue
            decoded.append(nxt)
            index += 2
            continue
        if character == "'":
            if index + 1 < length and sql[index + 1] == "'":
                decoded.append("'")
                index += 2
                continue
            return ''.join(decoded), index + 1, True
        decoded.append(character)
        index += 1
    return ''.join(decoded), index, False


class _CapturingCursor:
    def __init__(self, sink):
        self.sink = sink
        self.description = [('column', None, None, None, None, None, None)]
        self.redshift_rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, query, *args):
        self.sink.append((query, args))

    def fetchall(self):
        return []

    def close(self):
        return None


class _CapturingConnection:
    def __init__(self, sink):
        self.sink = sink

    def cursor(self):
        return _CapturingCursor(self.sink)

    def commit(self):
        return None

    def close(self):
        return None


def _flatten(value):
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from _flatten(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _flatten(item)
    else:
        yield value


class BackslashQuoteInjectionTests(unittest.TestCase):
    def test_documented_string_literal_escapes(self):
        samples = {
            "'Today''s sales'": "Today's sales",
            "'C:\\\\user'": "C:\\user",
            "'Hello\\tWorld'": "Hello\tWorld",
            "'Hello\\nWorld'": "Hello\nWorld",
            "'-\\041-'": "-!-",
            "'-\\x21-'": "-!-",
            "'-\\u26c4-'": "-\u26c4-",
            "'\\z'": "z",
            "'\\''": "'",
        }
        for literal, expected in samples.items():
            code, literals = split_backslash_escaped_sql('SELECT ' + literal)
            self.assertEqual([(expected, True)], literals, literal)
            self.assertNotIn(expected, code)

    def test_snowflake_sync_keeps_backslash_quote_in_the_literal(self):
        calls = self._sync_snowflake(BREAKOUT_VALUE, disable_column_type_check=None)
        self._assert_value_stays_data(calls, BREAKOUT_VALUE)

    def test_snowflake_sync_keeps_backslash_quote_when_column_check_is_on(self):
        calls = self._sync_snowflake(BREAKOUT_VALUE, disable_column_type_check=False)
        self._assert_value_stays_data(calls, BREAKOUT_VALUE)

    def test_snowflake_merge_insert_keeps_backslash_quote_in_the_literal(self):
        calls = self._sync_snowflake(
            BREAKOUT_VALUE,
            disable_column_type_check=None,
            unique_constraints=['id'],
            unique_conflict_method='UPDATE',
        )
        self._assert_value_stays_data(calls, BREAKOUT_VALUE)

    def test_snowflake_array_element_keeps_backslash_quote_in_the_literal(self):
        calls = self._sync_snowflake(
            None,
            disable_column_type_check=None,
            array_value=[ARRAY_BREAKOUT_VALUE],
        )
        self._assert_value_stays_data(calls, ARRAY_BREAKOUT_VALUE)

    def test_redshift_sync_keeps_backslash_quote_in_the_literal(self):
        calls = self._sync_redshift(BREAKOUT_VALUE, disable_column_type_check=None)
        self._assert_value_stays_data(calls, BREAKOUT_VALUE)

    def test_redshift_sync_keeps_backslash_quote_when_column_check_is_on(self):
        calls = self._sync_redshift(BREAKOUT_VALUE, disable_column_type_check=False)
        self._assert_value_stays_data(calls, BREAKOUT_VALUE)

    def test_redshift_merge_load_keeps_backslash_quote_in_the_literal(self):
        calls = self._sync_redshift(
            BREAKOUT_VALUE,
            disable_column_type_check=None,
            use_merge_load=True,
        )
        self._assert_value_stays_data(calls, BREAKOUT_VALUE)

    def _assert_value_stays_data(self, calls, value):
        self.assertTrue(calls, 'destination did not execute any SQL')
        inserts = [
            sql for sql, _args in calls
            if sql.lstrip().upper().startswith('INSERT')
        ]
        self.assertTrue(inserts, 'destination did not execute an INSERT: %r' % (calls,))
        code_regions = []
        found = False
        for sql, args in calls:
            code, literals = split_backslash_escaped_sql(sql)
            code_regions.append(code)
            if any(decoded == value and closed for decoded, closed in literals):
                found = True
            if value in list(_flatten(args)):
                found = True
        code_text = '\n'.join(code_regions)
        self.assertNotIn(
            MARKER,
            code_text,
            'synced text was parsed as SQL outside a string literal:\n%s' % code_text,
        )
        self.assertTrue(
            found,
            'synced text was not preserved as a decoded literal or a bound parameter. '
            'SQL sent to the cursor: %r' % (calls,),
        )

    def _sync_snowflake(
        self,
        body,
        disable_column_type_check,
        unique_constraints=None,
        unique_conflict_method=None,
        array_value=None,
    ):
        properties = {
            'id': {'type': ['null', 'string']},
        }
        record = {'id': 'ticket-1'}
        if array_value is None:
            properties['body'] = {'type': ['null', 'string']}
            record['body'] = body
        else:
            properties['labels'] = {
                'type': ['null', 'array'],
                'items': {'type': ['null', 'string']},
            }
            record['labels'] = array_value
        config = {
            'account': 'placeholder',
            'database': 'warehouse',
            'password': 'placeholder',
            'schema': 'analytics',
            'table': 'tickets',
            'username': 'placeholder',
            'warehouse': 'placeholder',
        }
        return self._run_sync(
            Snowflake,
            'mage_integrations.connections.snowflake.connect',
            config,
            properties,
            record,
            disable_column_type_check,
            unique_constraints,
            unique_conflict_method,
        )

    def _sync_redshift(
        self,
        body,
        disable_column_type_check,
        use_merge_load=False,
        unique_constraints=None,
        unique_conflict_method=None,
    ):
        config = {
            'database': 'warehouse',
            'host': 'placeholder',
            'password': 'placeholder',
            'port': 5439,
            'schema': 'analytics',
            'table': 'tickets',
            'user': 'placeholder',
            'use_merge_load': use_merge_load,
        }
        properties = {
            'id': {'type': ['null', 'string']},
            'body': {'type': ['null', 'string']},
        }
        record = {'id': 'ticket-1', 'body': body}
        return self._run_sync(
            Redshift,
            'mage_integrations.connections.redshift.connect',
            config,
            properties,
            record,
            disable_column_type_check,
            unique_constraints,
            unique_conflict_method,
        )

    def _run_sync(
        self,
        destination_class,
        connect_path,
        config,
        properties,
        record,
        disable_column_type_check,
        unique_constraints,
        unique_conflict_method,
    ):
        schema_message = {
            'type': 'SCHEMA',
            'stream': 'tickets',
            'schema': {
                'type': 'object',
                'properties': properties,
            },
            'replication_method': 'FULL_TABLE',
            'key_properties': ['id'],
        }
        if disable_column_type_check is not None:
            schema_message['disable_column_type_check'] = disable_column_type_check
        if unique_constraints is not None:
            schema_message['unique_constraints'] = unique_constraints
        if unique_conflict_method is not None:
            schema_message['unique_conflict_method'] = unique_conflict_method
        record_message = {
            'type': 'RECORD',
            'stream': 'tickets',
            'record': record,
        }
        payload = '\n'.join([
            json.dumps(schema_message),
            json.dumps(record_message),
        ]) + '\n'
        calls = []

        def connect(**kwargs):
            return _CapturingConnection(calls)

        destination = destination_class(
            batch_processing=True,
            config=config,
        )
        with unittest.mock.patch(connect_path, connect):
            destination.process(io.BytesIO(payload.encode('utf-8')))
        return calls


if __name__ == '__main__':
    unittest.main()
