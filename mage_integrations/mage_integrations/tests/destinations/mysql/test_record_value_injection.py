import io
import json
import os
import unittest

import mysql.connector

from mage_integrations.destinations.mysql import MySQL

# These tests fail while record values are concatenated into MySQL statements.
# They pass once those values are sent as parameters, or rejected / escaped so
# the database does not evaluate them.

MARKER = 424242
STREAM = 'people'


def _connect(database=None):
    return mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', '127.0.0.1'),
        port=int(os.environ.get('MYSQL_PORT', '3306')),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', 'placeholder'),
        database=database,
    )


def _cells(database, table):
    connection = _connect(database)
    cursor = connection.cursor()
    try:
        cursor.execute(f'SELECT * FROM {table}')
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def _prepare_database(database):
    connection = _connect()
    cursor = connection.cursor()
    cursor.execute(f'DROP DATABASE IF EXISTS {database}')
    cursor.execute(f'CREATE DATABASE {database}')
    cursor.execute(
        f'CREATE TABLE {database}.sentinel (marker INT)'
    )
    cursor.execute(
        f'INSERT INTO {database}.sentinel (marker) VALUES ({MARKER})'
    )
    connection.commit()
    cursor.close()
    connection.close()


def _sync(database, properties, record, schema_message_extra=None):
    _prepare_database(database)
    schema_message = {
        'type': 'SCHEMA',
        'stream': STREAM,
        'schema': {
            'type': 'object',
            'properties': properties,
        },
        'key_properties': [],
        'replication_method': 'FULL_TABLE',
    }
    if schema_message_extra:
        schema_message.update(schema_message_extra)
    record_message = {
        'type': 'RECORD',
        'stream': STREAM,
        'record': record,
    }
    raw = (
        json.dumps(schema_message) + '\n' + json.dumps(record_message) + '\n'
    ).encode()
    destination = MySQL(
        config={
            'database': database,
            'host': os.environ.get('MYSQL_HOST', '127.0.0.1'),
            'password': os.environ.get('MYSQL_PASSWORD', 'placeholder'),
            'port': int(os.environ.get('MYSQL_PORT', '3306')),
            'table': 'synced',
            'username': os.environ.get('MYSQL_USER', 'root'),
        },
        batch_processing=True,
    )
    try:
        destination.process(io.BytesIO(raw))
    except Exception:
        # A fix may reject the record. The failure mode that matters is the
        # destination evaluating the record as SQL before that rejection.
        pass
    return _cells(database, 'synced')


def _assert_marker_not_loaded(test, rows):
    for row in rows:
        for value in row:
            test.assertNotEqual(value, MARKER)
            test.assertNotEqual(value, float(MARKER))
            test.assertNotEqual(str(value), str(MARKER))


class MySQLRecordValueInjectionTests(unittest.TestCase):
    def test_number_subquery_is_not_executed(self):
        rows = _sync(
            'sqli_number',
            {'amount': {'type': ['null', 'number']}},
            {'amount': '(SELECT marker FROM sentinel)'},
        )
        _assert_marker_not_loaded(self, rows)

    def test_number_subquery_is_not_executed_on_insert_ignore(self):
        rows = _sync(
            'sqli_ignore',
            {
                'id': {'type': ['null', 'string']},
                'amount': {'type': ['null', 'number']},
            },
            {
                'id': 'row-1',
                'amount': '(SELECT marker FROM sentinel)',
            },
            schema_message_extra={
                'key_properties': ['id'],
                'unique_constraints': ['id'],
                'unique_conflict_method': 'IGNORE',
            },
        )
        _assert_marker_not_loaded(self, rows)

    def test_string_backslash_quote_subquery_is_not_executed(self):
        # Quote doubling leaves the backslash in place, so the doubled quote
        # closes the CAST string and the rest of the value is SQL.
        rows = _sync(
            'sqli_string',
            {'label': {'type': ['null', 'string']}},
            {
                'label': (
                    "\\' AS CHAR(255)), (SELECT marker FROM sentinel), 1)-- "
                ),
            },
        )
        _assert_marker_not_loaded(self, rows)
