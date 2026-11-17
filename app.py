import hmac
import os

import psycopg
from flask import Flask, jsonify, request
from itsdangerous import BadData, URLSafeTimedSerializer

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "dbname=saas_support_lab connect_timeout=5",
)


@app.get("/studies/<study_id>")
def get_study(study_id):
    if request.authorization is None:
        return unauthorized()
    try:
        with psycopg.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                user, error = authenticate(cursor)
                if error is not None:
                    return error
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
        {"WWW-Authenticate": 'Basic realm="SaaS Support Lab", Bearer realm="SaaS Support Lab"'},
    )


TOKEN_TTL_SECONDS = 900


def token_serializer():
    secret = os.environ.get("LAB_TOKEN_SECRET", "")
    if len(secret.encode("utf-8")) < 32:
        raise ValueError("LAB_TOKEN_SECRET must contain at least 32 bytes")
    return URLSafeTimedSerializer(secret, salt="saas-support-access-v1")


def authenticate(cursor, basic_only=False):
    auth = request.authorization
    if auth is None:
        return None, unauthorized()
    if auth.type.lower() == "basic":
        username = auth.username
        if not username or not auth.password:
            return None, unauthorized()
    elif auth.type.lower() == "bearer" and not basic_only:
        try:
            payload = token_serializer().loads(auth.token or "", max_age=TOKEN_TTL_SECONDS)
        except ValueError:
            return None, (jsonify(error="Token service unavailable"), 503)
        except BadData:
            return None, unauthorized()
        if not isinstance(payload, dict) or not isinstance(payload.get("username"), str):
            return None, unauthorized()
        username = payload["username"]
    else:
        return None, unauthorized()

    cursor.execute(
        "SELECT clinic_id, role, password_env FROM app_users WHERE username = %s",
        (username,),
    )
    user = cursor.fetchone()
    expected = os.environ.get(user[2]) if user else None
    if not expected:
        return None, unauthorized()
    if auth.type.lower() == "basic" and not hmac.compare_digest(
        auth.password.encode("utf-8"), expected.encode("utf-8")
    ):
        return None, unauthorized()
    return user, None


@app.post("/auth/token")
def issue_token():
    try:
        with psycopg.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                user, error = authenticate(cursor, basic_only=True)
                if error is not None:
                    return error
    except psycopg.Error:
        app.logger.exception("Database query failed")
        return jsonify(error="Database unavailable"), 503
    try:
        token = token_serializer().dumps({"username": request.authorization.username})
    except ValueError:
        return jsonify(error="Token service unavailable"), 503
    response = jsonify(access_token=token, token_type="Bearer", expires_in=TOKEN_TTL_SECONDS)
    response.headers["Cache-Control"] = "no-store"
    return response, 200
