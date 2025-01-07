from __future__ import annotations
from flask import Flask, request, Response
import datetime
import logging
import os
import sqlalchemy

from connect_connector_auto_iam_authn import connect_with_connector_auto_iam_authn
from connect_unix import connect_unix_socket

app = Flask(__name__)

logger = logging.getLogger()


def init_connection_pool() -> sqlalchemy.engine.base.Engine:
    """Sets up connection pool for the app."""
    # use a Unix socket when INSTANCE_UNIX_SOCKET (e.g. /cloudsql/project:region:instance) is defined
    if os.environ.get("INSTANCE_UNIX_SOCKET"):
        return connect_unix_socket()

    # use the connector when INSTANCE_CONNECTION_NAME (e.g. project:region:instance) is defined
    if os.environ.get("INSTANCE_CONNECTION_NAME"):
        # Either a DB_USER or a DB_IAM_USER should be defined. If both are
        # defined, DB_IAM_USER takes precedence.
        return (
            connect_with_connector_auto_iam_authn()
        )

    raise ValueError(
        "Missing database connection type. Please define one of INSTANCE_HOST, INSTANCE_UNIX_SOCKET, or INSTANCE_CONNECTION_NAME"
    )


# create 'quiz_questions' table in database if it does not already exist
def migrate_db(db: sqlalchemy.engine.base.Engine) -> None:
    """Creates the `quiz_questions` table if it doesn't exist."""
    with db.connect() as conn:
        conn.execute(
            sqlalchemy.text(
                "CREATE TABLE IF NOT EXISTS quiz_questions "
                "( id INT AUTO_INCREMENT PRIMARY KEY, question TEXT NOT NULL, answer1 TEXT NOT NULL, answer2 TEXT NOT NULL, answer3 TEXT NOT NULL, answer4 TEXT NOT NULL, correct_answer INT, time_cast timestamp NOT NULL );"
            )
        )
        conn.commit()


# This global variable is declared with a value of `None`, instead of calling
# `init_db()` immediately, to simplify testing. In general, it
# is safe to initialize your database connection pool when your script starts
# -- there is no need to wait for the first request.
db = None


# init_db lazily instantiates a database connection pool. Users of Cloud Run or
# App Engine may wish to skip this lazy instantiation and connect as soon
# as the function is loaded. This is primarily to help testing.
@app.before_request
def init_db() -> sqlalchemy.engine.base.Engine:
    """Initiates connection to database and its' structure."""
    global db
    if db is None:
        db = init_connection_pool()
        migrate_db(db)


@app.route("/questions", methods=["POST"])
def add_question() -> Response:
    """Saves a new question to the database."""
    # question = request.form["question"]
    # answer1 = request.form["answer1"]
    # answer2 = request.form["answer2"]
    # answer3 = request.form["answer3"]
    # answer4 = request.form["answer4"]
    # correct_answer = request.form["correct_answer"]
    
    data = request.get_json()
    return save_question(db, data["question"], data["answer1"], data["answer2"], data["answer3"], data["answer4"], data["correct_answer"])
    # return save_question(db, question, answer1, answer2, answer3, answer4, correct_answer)

@app.route("/questions", methods=["GET"])
def get_questions() -> Response:
    """Returns all questions from the database."""
    questions = []
    with db.connect() as conn:
        # Execute the query and fetch all results
        question_rows = conn.execute(
            sqlalchemy.text(
                "SELECT * from quiz_questions"
            )
        ).fetchall()
        for row in question_rows:
            questions.append({"id": row[0], "question": row[1], "answer1": row[2], "answer2": row[3], "answer3": row[4], "answer4": row[5], "correct_answer": row[6], "time_cast": row[7]})
        return questions


def save_question(db: sqlalchemy.engine.base.Engine, question: str, answer1: str, answer2: str, answer3: str, answer4: str, correct_answer: int) -> Response:
    """Saves a single question into the database.

    Args:
        db: Connection to the database.
        question: The question to be saved.
        answer1: The first answer to the question.
        answer2: The second answer to the question.
        answer3: The third answer to the question.
        answer4: The fourth answer to the question.
        correct_answer: The index of the correct answer.

    Returns:
        A HTTP response that can be sent to the client.
    """
    time_cast = datetime.datetime.now(tz=datetime.timezone.utc)

    # [START cloud_sql_mysql_sqlalchemy_connection]
    # Preparing a statement before hand can help protect against injections.
    stmt = sqlalchemy.text(
        "INSERT INTO quiz_questions (question, answer1, answer2, answer3, answer4, correct_answer, time_cast) VALUES (:question, :answer1, :answer2, :answer3, :answer4, :correct_answer, :time_cast)"
    )
    try:
        # Using a with statement ensures that the connection is always released
        # back into the pool at the end of statement (even if an error occurs)
        with db.connect() as conn:
            conn.execute(stmt, parameters={"question": question, "answer1": answer1, "answer2": answer2, "answer3": answer3, "answer4": answer4, "correct_answer": correct_answer, "time_cast": time_cast})
            conn.commit()
    except Exception as e:
        # If something goes wrong, handle the error in this section. This might
        # involve retrying or adjusting parameters depending on the situation.
        # [START_EXCLUDE]
        logger.exception(e)
        return Response(
            status=500,
            response="Unable to successfully save question! Please check the "
            "application logs for more details.",
        )
        # [END_EXCLUDE]
    # [END cloud_sql_mysql_sqlalchemy_connection]

    return Response(
        status=200,
        response=f"Question successfully saved at time {time_cast}!",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
