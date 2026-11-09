import os
import sqlite3
from pathlib import Path
from tempfile import gettempdir
from time import perf_counter

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Histogram, generate_latest

app = Flask(__name__)
app.config["DATABASE"] = os.getenv("TASKFLOW_DB", str(Path(gettempdir()) / "taskflow.db"))
duration = Histogram(
    "http_request_duration_seconds", "Durée des requêtes HTTP",
    ["route", "status"], buckets=(0.01, 0.05, 0.1, 0.3, 0.5, 1, 5),
)


@app.before_request
def start_timer():
    g.started = perf_counter()


@app.after_request
def measure(response):
    if request.path != "/metrics":
        route = request.url_rule.rule if request.url_rule else "unmatched"
        duration.labels(route, str(response.status_code)).observe(perf_counter() - g.started)
    return response


@app.get("/health")
def health():
    return jsonify(status="ok", version=os.getenv("APP_VERSION", "v1"))


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)


@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    database = sqlite3.connect(Path(app.config["DATABASE"]))
    try:
        with database:
            database.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
            if request.method == "GET":
                rows = database.execute("SELECT id, title FROM tasks ORDER BY id")
                return jsonify([{"id": key, "title": title} for key, title in rows])
            data = request.get_json(silent=True)
            title = data.get("title") if isinstance(data, dict) else None
            if not isinstance(title, str) or not title.strip():
                return jsonify(error="Le champ title doit contenir du texte."), 400
            result = database.execute("INSERT INTO tasks(title) VALUES (?)", (title.strip(),))
            return jsonify(id=result.lastrowid, title=title.strip()), 201
    finally:
        database.close()
