import hmac
import os

import psycopg
from flask import Flask, jsonify, request

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "dbname=saas_support_lab connect_timeout=5",
)


@app.get("/studies/<study_id>")
def get_study(study_id):
    auth = request.authorization
    if auth is None or auth.type.lower() != "basic" or not auth.username or not auth.password:
        return unauthorized()

    try:
        with psycopg.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT clinic_id, role, password_env FROM app_users WHERE username = %s",
                    (auth.username,),
                )
                user = cursor.fetchone()
                expected_password = os.environ.get(user[2]) if user else None
                if not expected_password or not hmac.compare_digest(
                    auth.password.encode("utf-8"), expected_password.encode("utf-8")
                ):
                    return unauthorized()
                if user[1] != "reader":
                    return jsonify(error="Access denied"), 403

                cursor.execute(
                    "SELECT study_id, status, clinic_id FROM studies WHERE study_id = %s",
                    (study_id,),
                )
                study = cursor.fetchone()
    except psycopg.Error:
        app.logger.exception("Database query failed")
        return jsonify(error="Database unavailable"), 503

    if study is None:
        return jsonify(error="Study not found", study_id=study_id), 404

    if study[2] != user[0]:
        return jsonify(error="Access denied"), 403

    return jsonify(study_id=study[0], status=study[1]), 200


def unauthorized():
    return (
        jsonify(error="Authentication required"),
        401,
        {"WWW-Authenticate": 'Basic realm="SaaS Support Lab"'},
    )
