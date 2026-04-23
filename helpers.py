import sqlite3
import subprocess
import tempfile
import os
import re

from flask import session, redirect
from functools import wraps

# Human friendly messages for common Python errors
error_map = {
    "NameError": "Variable not defined",
    "SyntaxError": "Invalid syntax",
    "TypeError": "Wrong data type",
    "IndexError": "Index out of range",
    "ZeroDivisionError": "Division by zero"
}

# DATABASE CONNECTION
def get_db():
    # Create and returns a connection to the SQLite database
    db = sqlite3.connect("database.db")
    db.row_factory = sqlite3.Row
    return db

# AUTH DECORATOR
def login_required(f):
    # Decorator that protects routes
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapped

# CODE EXECUTION SERVICE
def execute_python(code):
    # Executes Python code in a temporary file and returns output/errors.
    temp_path = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            f.write(code.encode())
            temp_path = f.name

        # Execute Python file safely with timeout
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=5 # Prevent infinite loops
        )

        if result.stderr:
            match = re.search(r"(\w+Error)", result.stderr)

            if match:
                error_type = match.group(1)
            else:
                error_type = "Error"

            msg = error_map.get(error_type, "Unknown error")
            
            return result.stdout, f"{error_type}: {msg}"
        
        return result.stdout, ""
    
    except Exception as e:
        # Return error message if execution fails
        return "", "Execution error"
    finally:
        # Always remove temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# DELETE USER DATA
def delete_user_data(db, user_id):
    # Delete all data related to a user.
    db.execute("DELETE FROM ideas WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM comments WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM votes WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM requests WHERE from_user_id = ? OR to_user_id = ?", (user_id, user_id))
    db.execute("DELETE FROM dev_sessions WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))

def save_comment(idea_id, user_id, content):
    db = get_db()
    db.execute(
        "INSERT INTO comments(idea_id, user_id, content) VALUES (?, ?, ?)", (idea_id, user_id, content)
    )

    db.commit()
    return db.execute("SELECT id, idea_id, user_id, content,created_at FROM comments WHERE rowid = last_insert_rowid()").fetchone()