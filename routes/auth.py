from flask import Blueprint, render_template, request, redirect, session, flash
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import get_db

# Blueprint for authentication routes
auth_bp = Blueprint("auth", __name__)

# USER REGISTRATION
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get form data
        email = request.form.get("email")
        name = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
    
        # Validate required fields
        if not email or not name or not password or not confirmation:
            flash("All fields are required.")
            return redirect("/register")
        
        # Check password confirmation
        if password != confirmation:
            flash("Password and confirmation do not match.")
            return redirect("/register")
        
        # Enforce password security rules
        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect("/register")
        
        if not re.search(r"[A-Z]", password):
            flash("Password must contain at least one uppercase letter.")
            return redirect("/register")
        
        if not re.search(r"[a-z]", password):
            flash("Password must contain at least one lowercase letter.")
            return redirect("/register")
        
        if not re.search(r"\d", password):
            flash("Password must contain at least one number.")
            return redirect("/register")
        
        # Hash password before storing
        hashedPassword = generate_password_hash(password)

        try:
            db = get_db()
            # Insert new user into database
            db.execute("INSERT INTO users (email, username, hash) VALUES (?, ?, ?)", (email, name, hashedPassword))
            db.commit()
        except sqlite3.IntegrityError:
            # Handle duplicate username
            flash("Username already exists.")
            return redirect("/register")
        
        flash("Registered successfully. Please log in.")
        return redirect("/login")
    
    # Render registration page
    return render_template("register.html")

# USER LOGIN
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Get login data
        name = request.form.get("username")
        password = request.form.get("password")

        # Validate input
        if not name or not password:
            flash("Username and password are required.")
            return redirect(("/login"))
        
        db = get_db()

        # Retrieve user from database
        user = db.execute("SELECT * FROM users WHERE username = ?", (name,)).fetchone()

        # Check credentials
        if user is None or not check_password_hash(user["hash"], password):
            flash("Invalid username or password.")
            return redirect("/login")

        # Store user info in session
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        flash("Logged in successfully.")
        return redirect("/")
    
    # Render login page
    return render_template("login.html")

# USER LOGOUT
@auth_bp.route("/logout")
def logout():
    # Log out user by clearing session
    session.clear()
    flash("Logged out.")
    return redirect("/login")
