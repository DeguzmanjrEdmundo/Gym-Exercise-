from multiprocessing import connection

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, request
import sqlite3
import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

app.secret_key = "gym-exercise-guide-secret"
scheduler = BackgroundScheduler()

reminder_hour = 18
reminder_minute = 0

scheduler.start()

DATABASE = "gym.db"



def create_reminder_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS reminder_settings (
            id INTEGER PRIMARY KEY,
            reminder_hour INTEGER NOT NULL DEFAULT 18,
            reminder_minute INTEGER NOT NULL DEFAULT 0,
            reminder_enabled INTEGER NOT NULL DEFAULT 1
        )
    """)

    connection.execute("""
        INSERT OR IGNORE INTO reminder_settings
        (id, reminder_hour, reminder_minute, reminder_enabled)
        VALUES (1, 18, 0, 1)
    """)

    columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(reminder_settings)"
        ).fetchall()
    ]

    if "reminder_enabled" not in columns:
        connection.execute("""
            ALTER TABLE reminder_settings
            ADD COLUMN reminder_enabled INTEGER NOT NULL DEFAULT 1
        """)

    connection.commit()
    connection.close()



def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/")
def home():

    connection = get_db_connection()

    categories = connection.execute(
        "SELECT * FROM categories"
    ).fetchall()

    connection.close()

    return render_template(
        "index.html",
        categories=categories
    )


@app.route("/category/<int:category_id>")
def category_exercises(category_id):

    connection = get_db_connection()

    category = connection.execute(
        "SELECT * FROM categories WHERE id = ?",
        (category_id,)
    ).fetchone()

    exercises = connection.execute(
        "SELECT * FROM exercises WHERE category_id = ?",
        (category_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "exercises.html",
        category=category,
        exercises=exercises
    )


@app.route("/exercise/<int:exercise_id>")
def exercise_detail(exercise_id):

    connection = get_db_connection()

    exercise = connection.execute(
        "SELECT * FROM exercises WHERE id = ?",
        (exercise_id,)
    ).fetchone()

    connection.close()

    return render_template(
        "exercise_detail.html",
        exercise=exercise
    )


@app.route("/workout")
def workout():

    connection = get_db_connection()

    exercises = connection.execute(
        "SELECT * FROM exercises"
    ).fetchall()

    connection.close()

    return render_template(
        "workout.html",
        exercises=exercises
    )


@app.route("/add-to-workout/<int:exercise_id>", methods=["POST"])
def add_to_workout(exercise_id):

    if "workout" not in session:
        session["workout"] = []

    if exercise_id not in session["workout"]:
        session["workout"].append(exercise_id)
        session.modified = True

    return redirect(url_for("my_workout"))


@app.route("/my-workout")
def my_workout():

    connection = get_db_connection()

    workout_ids = session.get("workout", [])

    exercises = []

    for exercise_id in workout_ids:

        exercise = connection.execute(
            "SELECT * FROM exercises WHERE id = ?",
            (exercise_id,)
        ).fetchone()

        if exercise:
            exercises.append(exercise)

    sets_reps = session.get("sets_reps", {})

    connection.close()

    return render_template(
        "my_workout.html",
        exercises=exercises,
        sets_reps=sets_reps
    )


@app.route("/remove-from-workout/<int:exercise_id>", methods=["POST"])
def remove_from_workout(exercise_id):

    if "workout" in session and exercise_id in session["workout"]:

        session["workout"].remove(exercise_id)
        session.modified = True

    return redirect(url_for("my_workout"))


@app.route("/save-workout", methods=["POST"])
def save_workout():

    if "sets_reps" not in session:
        session["sets_reps"] = {}

    for exercise_id in session.get("workout", []):

        sets = request.form.get(f"sets_{exercise_id}")
        reps = request.form.get(f"reps_{exercise_id}")

        session["sets_reps"][str(exercise_id)] = {
            "sets": sets,
            "reps": reps
        }

    session.modified = True

    return redirect(url_for("my_workout"))

@app.route("/send-workout-email", methods=["POST"])
def send_workout_email():

    recipient = request.form.get("email")

    workout_ids = session.get("workout", [])
    sets_reps = session.get("sets_reps", {})

    connection = get_db_connection()

    message = "Your GymBuhdy Workout\n\n"

    for exercise_id in workout_ids:

        exercise = connection.execute(
            "SELECT * FROM exercises WHERE id = ?",
            (exercise_id,)
        ).fetchone()

        if exercise:

            data = sets_reps.get(str(exercise_id), {})

            sets = data.get("sets", 3)
            reps = data.get("reps", 10)

            message += (
                f"{exercise['name']} - "
                f"{sets} sets x {reps} reps\n"
            )

    connection.close()

    email = EmailMessage()

    email["Subject"] = "Your GymBuhdy Workout"
    email["From"] = os.getenv("GMAIL_ADDRESS")
    email["To"] = recipient

    email.set_content(message)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

        server.login(
            os.getenv("GMAIL_ADDRESS"),
            os.getenv("GMAIL_APP_PASSWORD")
        )

        server.send_message(email)

    return redirect(url_for("my_workout"))


def send_daily_reminder():

    
    connection = get_db_connection()
    setting = connection.execute(
        "SELECT reminder_enabled FROM reminder_settings WHERE id = 1"
    ).fetchone()
    connection.close()

    if not setting or not setting["reminder_enabled"]:
        print("Daily reminder is disabled.")
        return


    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender or not password:
        print("Gmail settings are missing.")
        return

    message = EmailMessage()
    message["Subject"] = "GymBuhdy - Workout Reminder"
    message["From"] = sender
    message["To"] = sender

    message.set_content(
        "It's workout time!\n\n"
        "Open GymBuh-dy to view your selected exercises, "
        "sets, and reps.\n\n"
        "Stay consistent and keep going!"
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(message)

        print("Daily workout reminder sent.")

    except Exception as error:
        print("Could not send workout reminder:", error)

    
scheduler.add_job(
    send_daily_reminder,
    trigger="cron",
    hour=reminder_hour,
    minute=reminder_minute,
    id="daily_workout_reminder",
    replace_existing=True
)




@app.route("/reminder-settings", methods=["GET", "POST"])
def reminder_settings():
    global reminder_hour, reminder_minute

    connection = get_db_connection()
    saved_reminder = connection.execute(
        """
        SELECT reminder_hour, reminder_minute, reminder_enabled
        FROM reminder_settings
        WHERE id = 1
        """
    ).fetchone()
    connection.close()

    if saved_reminder:
        reminder_hour = saved_reminder["reminder_hour"]
        reminder_minute = saved_reminder["reminder_minute"]
        reminder_enabled = bool(saved_reminder["reminder_enabled"])
    else:
        reminder_hour = 18
        reminder_minute = 0
        reminder_enabled = True

    if request.method == "POST":
        reminder_time = request.form.get("reminder_time", "")
        reminder_enabled = (
            request.form.get("reminder_enabled") == "1"
        )

        try:
            hour, minute = map(int, reminder_time.split(":"))

            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError

            connection = get_db_connection()
            connection.execute(
                """
                UPDATE reminder_settings
                SET reminder_hour = ?,
                    reminder_minute = ?,
                    reminder_enabled = ?
                WHERE id = 1
                """,
                (hour, minute, int(reminder_enabled))
            )
            connection.commit()
            connection.close()

            reminder_hour = hour
            reminder_minute = minute

            job = scheduler.get_job("daily_workout_reminder")

            if reminder_enabled:
                if job:
                    scheduler.reschedule_job(
                        "daily_workout_reminder",
                        trigger="cron",
                        hour=hour,
                        minute=minute
                    )
                else:
                    scheduler.add_job(
                        send_daily_reminder,
                        trigger="cron",
                        hour=hour,
                        minute=minute,
                        id="daily_workout_reminder",
                        replace_existing=True
                    )
            else:
                if job:
                    scheduler.remove_job("daily_workout_reminder")

            return render_template(
                "reminder_settings.html",
                message="Reminder settings saved successfully!",
                reminder_time=f"{hour:02d}:{minute:02d}",
                reminder_enabled=reminder_enabled
            )

        except (ValueError, AttributeError):
            return render_template(
                "reminder_settings.html",
                message="Please choose a valid reminder time.",
                reminder_time=f"{reminder_hour:02d}:{reminder_minute:02d}",
                reminder_enabled=reminder_enabled
            )

    return render_template(
        "reminder_settings.html",
        message="",
        reminder_time=f"{reminder_hour:02d}:{reminder_minute:02d}",
        reminder_enabled=reminder_enabled
    )


def create_reminder_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS reminder_settings (
            id INTEGER PRIMARY KEY,
            reminder_hour INTEGER NOT NULL DEFAULT 18,
            reminder_minute INTEGER NOT NULL DEFAULT 0,
            reminder_enabled INTEGER NOT NULL DEFAULT 1
        )
    """)

    columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(reminder_settings)"
        ).fetchall()
    ]

    if "reminder_enabled" not in columns:
        connection.execute("""
            ALTER TABLE reminder_settings
            ADD COLUMN reminder_enabled INTEGER NOT NULL DEFAULT 1
        """)

    connection.execute("""
        INSERT OR IGNORE INTO reminder_settings
        (id, reminder_hour, reminder_minute, reminder_enabled)
        VALUES (1, 18, 0, 1)
    """)

    connection.commit()
    connection.close()





if __name__ == "__main__":
    create_reminder_table()
    app.run(debug=True, use_reloader=False)