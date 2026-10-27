import sqlite3

DATABASE = "gym.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            primary_muscle TEXT,
            secondary_muscles TEXT,
            equipment TEXT,
            difficulty TEXT,
            instructions TEXT,
            image TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    connection.commit()
    connection.close()


def add_categories():
    connection = get_db_connection()

    categories = [
        ("Chest", "chest.jpg"),
        ("Back", "back.jpg"),
        ("Legs", "legs.jpg"),
        ("Shoulders", "shoulders.jpg"),
        ("Arms", "arms.jpg"),
        ("Core", "core.jpg")
    ]

    connection.executemany(
        "INSERT INTO categories (name, image) VALUES (?, ?)",
        categories
    )

    connection.commit()
    connection.close()


def add_exercises():
    connection = get_db_connection()

    exercises = [
        (
            1,
            "Bench Press",
            "Chest",
            "Triceps, Shoulders",
            "Barbell",
            "Intermediate",
            "Lie on the bench, lower the bar toward your chest, then press it upward.",
            "bench_press.jpg"
        ),
        (
            1,
            "Push Up",
            "Chest",
            "Triceps, Shoulders",
            "Bodyweight",
            "Beginner",
            "Start in a plank position, lower your body toward the floor, then push yourself back up.",
            "push_up.jpg"
        ),
        (
            2,
            "Lat Pulldown",
            "Back",
            "Biceps",
            "Cable Machine",
            "Beginner",
            "Pull the bar toward your upper chest while keeping your back controlled.",
            "lat_pulldown.jpg"
        ),
        (
            2,
            "Barbell Row",
            "Back",
            "Biceps",
            "Barbell",
            "Intermediate",
            "Bend forward while keeping your back controlled and pull the bar toward your torso.",
            "barbell_row.jpg"
        ),
        (
            3,
            "Squat",
            "Legs",
            "Glutes, Hamstrings",
            "Bodyweight",
            "Beginner",
            "Lower your body by bending your knees and hips, then return to a standing position.",
            "squat.jpg"
        ),
        (
            3,
            "Leg Press",
            "Legs",
            "Glutes, Hamstrings",
            "Leg Press Machine",
            "Intermediate",
            "Push the platform away using your legs while keeping your movement controlled.",
            "leg_press.jpg"
        ),
        (
            4,
            "Shoulder Press",
            "Shoulders",
            "Triceps",
            "Dumbbells",
            "Intermediate",
            "Press the dumbbells upward from shoulder height and slowly lower them.",
            "shoulder_press.jpg"
        ),
        (
            4,
            "Lateral Raise",
            "Shoulders",
            "Traps",
            "Dumbbells",
            "Beginner",
            "Raise the dumbbells to the sides until your arms are approximately parallel with the floor.",
            "lateral_raise.jpg"
        ),
        (
            5,
            "Bicep Curl",
            "Arms",
            "Forearms",
            "Dumbbells",
            "Beginner",
            "Curl the dumbbells upward while keeping your elbows close to your body.",
            "bicep_curl.jpg"
        ),
        (
            5,
            "Tricep Pushdown",
            "Arms",
            "Forearms",
            "Cable Machine",
            "Beginner",
            "Push the cable handle downward while keeping your elbows close to your sides.",
            "tricep_pushdown.jpg"
        ),
        (
            6,
            "Plank",
            "Core",
            "Shoulders",
            "Bodyweight",
            "Beginner",
            "Hold a straight body position while supporting yourself on your forearms and toes.",
            "plank.jpg"
        ),
        (
            6,
            "Crunch",
            "Core",
            "Hip Flexors",
            "Bodyweight",
            "Beginner",
            "Lie on your back, bend your knees, and lift your upper body toward your knees.",
            "crunch.jpg"
        )
    ]

connection.executemany("""
    INSERT INTO exercises (
        category_id,
        name,
        primary_muscle,
        secondary_muscles,
        equipment,
        difficulty,
        instructions,
        image
    )
    SELECT ?, ?, ?, ?, ?, ?, ?, ?
    WHERE NOT EXISTS (
        SELECT 1
        FROM exercises
        WHERE category_id = ? AND name = ?
    )
""", [
    exercise + (exercise[0], exercise[1])
    for exercise in exercises
])

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")