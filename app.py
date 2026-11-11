import os

import psycopg
from flask import Flask, jsonify

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "dbname=saas_support_lab connect_timeout=5",
)


@app.get("/studies/<study_id>")
def get_study(study_id):
    try:
        with psycopg.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT study_id, status FROM studies WHERE study_id = %s",
                    (study_id,),
                )
                study = cursor.fetchone()
    except psycopg.Error:
        app.logger.exception("Database query failed")
        return jsonify(error="Database unavailable"), 503

    if study is None:
        return jsonify(error="Study not found", study_id=study_id), 404

    return jsonify(study_id=study[0], status=study[1]), 200
