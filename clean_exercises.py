import sqlite3

connection = sqlite3.connect("gym.db")

connection.execute("""
    DELETE FROM exercises
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM exercises
        GROUP BY category_id, name
    )
""")

connection.commit()

connection.close()

print("Duplicate exercises deleted successfully!")