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
            for filename in ('03-event-timestamps.sql', '03-event-timestamps.sql',
                             '04-incident-fixtures.sql', '04-incident-fixtures.sql'):
                connection.execute((root / 'sql' / filename).read_text())
        cls.config = patch.object(application, 'DATABASE_URL', cls.database_url)
        cls.config.start()
        cls.passwords = patch.dict(os.environ, {
            'LAB_ALICE_PASSWORD': 'alice-test-password',
            'LAB_BOB_PASSWORD': 'bob-test-password',
            'LAB_CAROL_PASSWORD': 'carol-test-password',
            'LAB_TOKEN_SECRET': 'test-only-signing-secret-at-least-32-bytes',
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
            row = connection.execute("SELECT count(*) FROM study_events WHERE study_id = 'LAB-001'").fetchone()
            self.assertEqual(row[0], 2)

    def test_database_error_still_503(self):
        with patch.object(application, 'DATABASE_URL', 'dbname=missing_access_test connect_timeout=2'):
            self.assertEqual(self.get('LAB-001', 'alice').status_code, 503)


    def issue(self, user='alice'):
        credentials = base64.b64encode((user + ':' + user + '-test-password').encode()).decode()
        return application.app.test_client().post(
            '/auth/token', headers={'Authorization': 'Basic ' + credentials})

    def bearer(self, token, study='LAB-001'):
        return application.app.test_client().get(
            '/studies/' + study, headers={'Authorization': 'Bearer ' + token})

    def test_token_own_and_other_clinic(self):
        response = self.issue()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['expires_in'], 900)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        token = response.json['access_token']
        self.assertEqual(self.bearer(token).status_code, 200)
        self.assertEqual(self.bearer(token, 'LAB-002').status_code, 403)

    def test_token_expiry(self):
        with patch('itsdangerous.timed.time.time', return_value=1000000):
            token = self.issue().json['access_token']
        with patch('itsdangerous.timed.time.time', return_value=1000901):
            self.assertEqual(self.bearer(token).status_code, 401)
        self.assertEqual(self.bearer(self.issue().json['access_token']).status_code, 200)

    def test_token_wrong_signature_and_malformed(self):
        token = self.issue().json['access_token']
        self.assertEqual(self.bearer(token + 'x').status_code, 401)
        self.assertEqual(self.bearer('invalid').status_code, 401)
        token = application.token_serializer().dumps(['unexpected-payload'])
        self.assertEqual(self.bearer(token).status_code, 401)

    def test_token_requires_signing_secret(self):
        with patch.dict(os.environ, {'LAB_TOKEN_SECRET': ''}):
            self.assertEqual(self.issue().status_code, 503)
            self.assertEqual(self.get('LAB-001', 'alice').status_code, 200)

    def test_token_login_requires_basic_credentials(self):
        client = application.app.test_client()
        self.assertEqual(client.post('/auth/token').status_code, 401)
        wrong = base64.b64encode(b'alice:wrong-password').decode()
        self.assertEqual(client.post('/auth/token', headers={'Authorization': 'Basic ' + wrong}).status_code, 401)
        token = self.issue().json['access_token']
        self.assertEqual(client.post('/auth/token', headers={'Authorization': 'Bearer ' + token}).status_code, 401)

    def test_token_role_is_checked(self):
        self.assertEqual(self.bearer(self.issue('carol').json['access_token']).status_code, 403)

    def test_token_rechecks_changed_role(self):
        token = self.issue().json['access_token']
        try:
            with psycopg.connect(self.database_url) as connection:
                connection.execute("UPDATE app_users SET role='restricted' WHERE username='alice'")
            self.assertEqual(self.bearer(token).status_code, 403)
        finally:
            with psycopg.connect(self.database_url) as connection:
                connection.execute("UPDATE app_users SET role='reader' WHERE username='alice'")

    def test_secret_rotation_invalidates_tokens(self):
        token = self.issue().json['access_token']
        with patch.dict(os.environ, {'LAB_TOKEN_SECRET': 'another-signing-secret-at-least-32-bytes'}):
            self.assertEqual(self.bearer(token).status_code, 401)

    def test_incident_aggregates_and_fixture_reruns(self):
        root = Path(__file__).resolve().parents[1]
        query = (root / 'sql/05-incident-investigation.sql').read_text().split(';')[0]
        query = query.replace(":'from_ts'", "'2026-11-17T00:00:00Z'")
        query = query.replace(":'to_ts'", "'2026-11-18T00:00:00Z'")
        with psycopg.connect(self.database_url) as connection:
            rows = connection.execute(query).fetchall()
            self.assertEqual([(r[0], r[1], r[2]) for r in rows], [('clinic_a', 3, 2), ('clinic_b', 1, 1)])
            self.assertEqual(connection.execute('SELECT count(*) FROM study_events WHERE occurred_at IS NULL').fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT count(*) FROM study_events WHERE study_id LIKE 'SQL-%'").fetchone()[0], 6)

    def test_incident_window_excludes_upper_boundary(self):
        root = Path(__file__).resolve().parents[1]
        query = (root / 'sql/05-incident-investigation.sql').read_text().split(';')[0]
        query = query.replace(":'from_ts'", "'2026-11-17T09:00:00Z'")
        query = query.replace(":'to_ts'", "'2026-11-17T10:00:00Z'")
        with psycopg.connect(self.database_url) as connection:
            rows = connection.execute(query).fetchall()
            self.assertEqual([(r[0], r[1], r[2]) for r in rows], [('clinic_a', 3, 2), ('clinic_b', 0, 0)])

    def test_incident_detail_and_unknown_time_reports(self):
        root = Path(__file__).resolve().parents[1]
        query = (root / 'sql/05-incident-investigation.sql').read_text()
        query = query.replace(":'from_ts'", "'2026-11-17T00:00:00Z'")
        query = query.replace(":'to_ts'", "'2026-11-18T00:00:00Z'")
        with psycopg.connect(self.database_url) as connection:
            cursor = connection.execute(query)
            cursor.fetchall()
            self.assertTrue(cursor.nextset())
            rows = cursor.fetchall()
            self.assertEqual([(r[0], r[2], r[3]) for r in rows], [
                ('SQL-A001', 'received', 2), ('SQL-A002', 'published', 1),
                ('SQL-B001', 'received', 1)])
            self.assertTrue(cursor.nextset())
            self.assertEqual(cursor.fetchone()[0], 2)


if __name__ == '__main__':
    unittest.main()
