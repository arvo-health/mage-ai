import io
import json
import unittest
from unittest.mock import patch

from mage_integrations.destinations.doris import Doris

# Markers that are SQL when they appear outside a Doris string literal.
# DorisLexer.g4 STRING_LITERAL (isNoBackslashEscapes = false) treats
# backslash-plus-any-character and a doubled quote as content of the literal.
UPDATE_MARKER = 'UPDATE other_table SET col = 1'
SELECT_MARKER = 'SELECT secret FROM other_table'

STRING_BREAKOUT = (
    "x\\' AS CHAR(255)), NULL, NULL); " + UPDATE_MARKER + '; --'
)
CHAR52_BREAKOUT = (
    "x\\' AS CHAR(52)), NULL, NULL); " + UPDATE_MARKER + '; --'
)
UNSIGNED_BREAKOUT = (
    "x\\' AS UNSIGNED), NULL, NULL); " + UPDATE_MARKER + '; --'
)
ARRAY_BREAKOUT = (
    "x\\', NULL, NULL); " + UPDATE_MARKER + '; --'
)
NUMBER_BREAKOUT = '1, NULL, NULL); ' + UPDATE_MARKER + '; --'
NUMBER_EXPRESSION = '(' + SELECT_MARKER + ' LIMIT 1)'


def mask_doris_literals_and_comments(sql):
    """Return SQL with Doris string literals and comments blanked out.

    The rules match Apache Doris DorisLexer.g4 with the default
    isNoBackslashEscapes = false: a backslash consumes the next character,
    a doubled quote is one quote of content, and the next unmatched quote
    ends the literal. '--' comments run to the newline. This is only the
    lexer step used to see whether a record value became SQL text.
    """
    out = []
    index = 0
    length = len(sql)
    while index < length:
        character = sql[index]
        following = sql[index + 1] if index + 1 < length else ''
        if character == '-' and following == '-':
            while index < length and sql[index] not in '\r\n':
                out.append(' ')
                index += 1
            continue
        if character == '/' and following == '*':
            out.append(' ')
            out.append(' ')
            index += 2
            while index < length and not (
                sql[index] == '*' and index + 1 < length and sql[index + 1] == '/'
            ):
                out.append(' ')
                index += 1
            if index < length:
                out.append(' ')
                out.append(' ')
                index += 2
            continue
        if character in ('\'', '"'):
            quote = character
            out.append(' ')
            index += 1
            while index < length:
                if sql[index] == '\\' and index + 1 < length:
                    out.append(' ')
                    out.append(' ')
                    index += 2
                    continue
                if sql[index] == quote and index + 1 < length and sql[index + 1] == quote:
                    out.append(' ')
                    out.append(' ')
                    index += 2
                    continue
                if sql[index] == quote:
                    out.append(' ')
                    index += 1
                    break
                out.append(' ')
                index += 1
            continue
        out.append(character)
        index += 1
    return ''.join(out)


class _Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = None
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, query, params=None):
        self.connection.queries.append((query, params))
        normalized = ' '.join(query.split()).lower()
        if normalized.startswith('select'):
            self.description = [('column_name',)]
            if 'information_schema.tables' in normalized and self.connection.table_exists:
                self._rows = [('orders',)]
            elif 'information_schema.columns' in normalized and self.connection.table_exists:
                self._rows = [
                    ('note', 'char(255)'),
                    ('_mage_created_at', 'char(52)'),
                    ('_mage_updated_at', 'char(52)'),
                ]
            else:
                self._rows = []
        else:
            self.description = None
            self._rows = []

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, queries, table_exists):
        self.queries = queries
        self.table_exists = table_exists

    def cursor(self):
        return _Cursor(self)

    def commit(self):
        pass

    def close(self):
        pass


class DorisRecordSqlInjectionTests(unittest.TestCase):
    """Record values synced through the Doris destination must stay data.

    These tests drive Doris.process with Singer SCHEMA and RECORD messages and
    the real connection execute path. They fail while record text is
    concatenated into the statement sent to the server.
    """

    def _sync(self, record, properties, schema_message=None, table_exists=False, records=None):
        queries = []

        def fake_connect(**kwargs):
            return _Connection(queries, table_exists)

        destination = Doris(
            batch_processing=True,
            config={
                'database': 'db',
                'host': '127.0.0.1',
                'password': 'placeholder',
                'port': 9030,
                'table': 'orders',
                'username': 'mage',
            },
        )
        schema_row = {
            'type': 'SCHEMA',
            'stream': 'orders',
            'schema': {
                'type': 'object',
                'properties': properties,
            },
            'key_properties': [],
            'replication_method': 'FULL_TABLE',
        }
        if schema_message:
            schema_row.update(schema_message)
        record_rows = records if records is not None else [record]
        lines = [json.dumps(schema_row)]
        for one_record in record_rows:
            lines.append(json.dumps({
                'type': 'RECORD',
                'stream': 'orders',
                'record': one_record,
            }))
        payload = ('\n'.join(lines) + '\n').encode()
        error = None
        with patch('mage_integrations.connections.doris.connect', fake_connect):
            try:
                destination.process(io.BytesIO(payload))
            except Exception as exc:
                error = exc
        return queries, error

    def _assert_marker_is_not_sql(self, queries, error, marker):
        unsafe = []
        for sql, params in queries:
            visible = mask_doris_literals_and_comments(sql)
            if marker in visible:
                unsafe.append(sql)
            if params is not None:
                # Bound parameters are data. The statement text is what was checked above.
                continue
        inserts = [
            sql for sql, _params in queries
            if sql.lstrip().upper().startswith('INSERT')
        ]
        self.assertEqual(
            unsafe,
            [],
            'A record value was executed as SQL outside a string literal:\n'
            + '\n'.join(unsafe),
        )
        if error is None:
            self.assertTrue(
                inserts,
                'The pipeline accepted the record but did not execute an INSERT.',
            )
            return
        if inserts:
            return
        message = str(error).lower()
        rejected = any(token in message for token in (
            'is not of type',
            'not a valid',
            'numeric',
            'invalid',
            'must be',
        ))
        if not rejected:
            raise error

    def test_string_backslash_does_not_become_a_statement(self):
        queries, error = self._sync(
            {'note': STRING_BREAKOUT},
            {'note': {'type': ['null', 'string']}},
            schema_message={'disable_column_type_check': False},
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_string_backslash_on_existing_table_does_not_become_a_statement(self):
        queries, error = self._sync(
            {'note': STRING_BREAKOUT},
            {'note': {'type': ['null', 'string']}},
            schema_message={'disable_column_type_check': False},
            table_exists=True,
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_duplicate_key_update_string_does_not_become_a_statement(self):
        queries, error = self._sync(
            {'note': STRING_BREAKOUT},
            {'note': {'type': ['null', 'string']}},
            schema_message={
                'disable_column_type_check': False,
                'unique_constraints': ['note'],
                'unique_conflict_method': 'UPDATE',
            },
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_insert_ignore_string_does_not_become_a_statement(self):
        queries, error = self._sync(
            {'note': STRING_BREAKOUT},
            {'note': {'type': ['null', 'string']}},
            schema_message={
                'disable_column_type_check': False,
                'unique_constraints': ['note'],
                'unique_conflict_method': 'IGNORE',
            },
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_number_expression_is_not_executed_as_sql(self):
        queries, error = self._sync(
            {'amount': NUMBER_EXPRESSION},
            {'amount': {'type': ['null', 'number']}},
            schema_message={'disable_column_type_check': True},
        )
        self._assert_marker_is_not_sql(queries, error, SELECT_MARKER)

    def test_number_breakout_when_type_check_omitted(self):
        queries, error = self._sync(
            {'amount': NUMBER_BREAKOUT},
            {'amount': {'type': ['null', 'number']}},
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_number_string_is_not_executed_when_type_check_enabled(self):
        queries, error = self._sync(
            {'amount': NUMBER_EXPRESSION},
            {'amount': {'type': ['null', 'number']}},
            schema_message={'disable_column_type_check': False},
        )
        self._assert_marker_is_not_sql(queries, error, SELECT_MARKER)

    def test_integer_string_is_not_executed_as_sql(self):
        queries, error = self._sync(
            {'qty': UNSIGNED_BREAKOUT},
            {'qty': {'type': ['null', 'integer']}},
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_boolean_string_is_not_executed_as_sql(self):
        queries, error = self._sync(
            {'flag': CHAR52_BREAKOUT},
            {'flag': {'type': ['null', 'boolean']}},
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_datetime_string_backslash_does_not_become_a_statement(self):
        queries, error = self._sync(
            {'event_at': CHAR52_BREAKOUT},
            {'event_at': {'type': ['null', 'string'], 'format': 'date-time'}},
            schema_message={'disable_column_type_check': False},
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_array_element_backslash_does_not_become_a_statement(self):
        queries, error = self._sync(
            {'tags': [ARRAY_BREAKOUT]},
            {'tags': {'type': ['null', 'array'], 'items': {'type': ['null', 'string']}}},
            schema_message={'disable_column_type_check': False},
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_object_string_does_not_become_a_statement(self):
        queries, error = self._sync(
            {'payload': STRING_BREAKOUT},
            {'payload': {'type': ['null', 'object']}},
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_second_record_in_batch_does_not_become_a_statement(self):
        queries, error = self._sync(
            None,
            {'note': {'type': ['null', 'string']}},
            schema_message={'disable_column_type_check': False},
            records=[{'note': 'ordinary'}, {'note': STRING_BREAKOUT}],
        )
        self._assert_marker_is_not_sql(queries, error, UPDATE_MARKER)

    def test_benign_string_and_number_still_insert(self):
        queries, error = self._sync(
            {'note': "O'Brien", 'amount': 12.5},
            {
                'note': {'type': ['null', 'string']},
                'amount': {'type': ['null', 'number']},
            },
            schema_message={'disable_column_type_check': False},
        )
        self.assertIsNone(error)
        statement_text = '\n'.join(sql for sql, _params in queries)
        bound = [params for _sql, params in queries if params is not None]
        self.assertIn('INSERT', statement_text.upper())
        self.assertTrue(
            "O'Brien" in statement_text or "O''Brien" in statement_text
            or any("O'Brien" in str(params) for params in bound),
        )
        self.assertTrue(
            '12.5' in statement_text or any('12.5' in str(params) for params in bound),
        )
        visible = mask_doris_literals_and_comments(statement_text)
        self.assertNotIn(UPDATE_MARKER, visible)
        self.assertNotIn(SELECT_MARKER, visible)


if __name__ == '__main__':
    unittest.main()
