import sqlite3

def init_db():
    with open("schema.sql", "r") as f:
        schema = f.read()

    conn = sqlite3.connect("database.db")
    conn.executescript(schema)
    conn.close()

    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()