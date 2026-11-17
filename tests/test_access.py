import base64
import os
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

import psycopg
from psycopg.conninfo import make_conninfo

import app as application


class AccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = os.environ['TEST_DATABASE_URL']
        cls.schema = 'access_test_' + uuid.uuid4().hex
        with psycopg.connect(cls.base) as connection:
            connection.execute('CREATE SCHEMA ' + cls.schema)
        cls.database_url = make_conninfo(cls.base, options='-c search_path=' + cls.schema)
        root = Path(__file__).resolve().parents[1]
        with psycopg.connect(cls.database_url) as connection:
            connection.execute((root / 'sql/01-setup.sql').read_text())
            connection.execute("UPDATE studies SET status = 'published' WHERE study_id = 'LAB-001'")
            connection.commit()
            migration = (root / 'sql/02-access-control.sql').read_text()
            connection.execute(migration)
            connection.execute(migration)
        cls.config = patch.object(application, 'DATABASE_URL', cls.database_url)
        cls.config.start()
        cls.passwords = patch.dict(os.environ, {
            'LAB_ALICE_PASSWORD': 'alice-test-password',
            'LAB_BOB_PASSWORD': 'bob-test-password',
            'LAB_CAROL_PASSWORD': 'carol-test-password',
        })
        cls.passwords.start()

    @classmethod
    def tearDownClass(cls):
        cls.passwords.stop()
        cls.config.stop()
        with psycopg.connect(cls.base) as connection:
            connection.execute('DROP SCHEMA ' + cls.schema + ' CASCADE')

    def get(self, study, user=None, password=None):
        headers = {}
        if user:
            password = password or user + '-test-password'
            token = base64.b64encode((user + ':' + password).encode()).decode()
            headers['Authorization'] = 'Basic ' + token
        return application.app.test_client().get('/studies/' + study, headers=headers)

    def test_own_clinic(self):
        response = self.get('LAB-001', 'alice')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'study_id': 'LAB-001', 'status': 'published'})
        self.assertEqual(self.get('LAB-002', 'bob').status_code, 200)

    def test_cross_clinic_both_directions(self):
        for user, study in (('alice', 'LAB-002'), ('bob', 'LAB-001')):
            response = self.get(study, user)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json, {'error': 'Access denied'})

    def test_role_denied_even_own_clinic(self):
        self.assertEqual(self.get('LAB-001', 'carol').status_code, 403)

    def test_missing_credentials(self):
        response = self.get('LAB-001')
        self.assertEqual(response.status_code, 401)
        self.assertIn('Basic', response.headers['WWW-Authenticate'])

    def test_invalid_or_unknown_user(self):
        self.assertEqual(self.get('LAB-001', 'alice', 'wrong').status_code, 401)
        self.assertEqual(self.get('LAB-001', 'unknown').status_code, 401)

    def test_missing_password_configuration(self):
        with patch.dict(os.environ, {'LAB_ALICE_PASSWORD': ''}):
            self.assertEqual(self.get('LAB-001', 'alice').status_code, 401)

    def test_missing_study(self):
        self.assertEqual(self.get('LAB-999', 'alice').status_code, 404)

    def test_identifier_is_parameterized(self):
        self.assertEqual(self.get("LAB-001' OR '1'='1", 'alice').status_code, 404)

    def test_migration_preserves_history(self):
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute('SELECT count(*) FROM study_events').fetchone()
            self.assertEqual(row[0], 2)

    def test_database_error_still_503(self):
        with patch.object(application, 'DATABASE_URL', 'dbname=missing_access_test connect_timeout=2'):
            self.assertEqual(self.get('LAB-001', 'alice').status_code, 503)


if __name__ == '__main__':
    unittest.main()
