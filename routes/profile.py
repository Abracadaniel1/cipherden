from flask import Blueprint, render_template, request, redirect, session, flash, abort
from helpers import login_required, delete_user_data, get_db
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Blueprint for profile related routes
profile_bp = Blueprint("profile", __name__)

# USER PROFILE PAGE 
@profile_bp.route("/user/<username>")
@login_required
def user_profile(username):
    db = get_db()

    # Retrieve user data
    user = db.execute("SELECT id, username, offers_status, bio, skills FROM users WHERE username = ?", (username,)).fetchone()

    if user is None:
        abort(404)

    # Check if current user is view their own profile
    own_profile = session.get("user_id") == user["id"]
    
    # Retrieve user's ideas with vote count
    ideas = db.execute("""
        SELECT ideas.id, ideas.title, ideas.status, ideas.progress,
                COUNT(votes.id) AS votes
        FROM ideas
        LEFT JOIN votes ON votes.idea_id = ideas.id
        WHERE ideas.user_id = ?
        GROUP BY ideas.id
        ORDER BY ideas.created_at DESC
    """, (user["id"],)).fetchall()

    # Basic stats
    stats = db.execute("SELECT COUNT(*) AS total_ideas, SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS active_ideas FROM ideas WHERE user_id = ?", (user["id"],)).fetchone()

    # Extract first skill for matching (simple recommendation logic)
    user_skills = user["skills"] or ""
    first_skill = user_skills.split(",")[0].strip() if user_skills else ""

    suggested_users = []

    # Suggested users only for own profile
    if own_profile:
        # Suggested users with similar skills
        if first_skill:
            suggested_users = db.execute("""
                SELECT users.id, users.username, users.skills,
                        COUNT(ideas.id) AS active_ideas
                FROM users 
                LEFT JOIN ideas ON ideas.user_id = users.id AND ideas.status != 'completed'
                WHERE users.offers_status = 1
                    AND users.id != ?
                    AND LOWER(users.skills) LIKE LOWER(?)
                GROUP BY users.id
                ORDER BY active_ideas DESC
                LIMIT 3
            """, (user["id"], f"%{first_skill}%")).fetchall()
        else:
            # Fallback: suggest active users
            suggested_users = db.execute("""
                SELECT users.id, users.username,
                        COUNT(ideas.id) AS active_ideas
                FROM users 
                LEFT JOIN ideas ON ideas.user_id = users.id AND ideas.status != 'completed'
                WHERE users.offers_status = 1
                    AND users.id != ?
                GROUP BY users.id
                ORDER BY active_ideas DESC
                LIMIT 3
            """, (user["id"],)).fetchall()

    # Initialize session-related data
    pending_count = 0
    active_session = None
    session_id = None

    if own_profile:
        # Count pending collaboration requests
        pending_count = db.execute("SELECT COUNT(*) AS ctn FROM requests WHERE to_user_id = ? AND req_status = 'pending'", (session["user_id"],)).fetchone()["ctn"]

        # Get latest active coding session
        active_session = db.execute("""
        SELECT id FROM dev_sessions
        WHERE (user1_id = ? OR user2_id = ?)
        AND status = 'active'
        ORDER BY id DESC
        LIMIT 1
        """, (session["user_id"], session["user_id"])
        ).fetchone()

        session_id = active_session["id"] if active_session else None

    # Render profile page
    return render_template(
        "profile.html",
        user=user,
        ideas=ideas,
        stats=stats,
        own_profile=own_profile,
        suggested_users=suggested_users,
        pending_count=pending_count,
        active_session=active_session,
        session_id=session_id,
        first_skill=first_skill
        )

# CHANGE USERNAME
@profile_bp.route("/change-username", methods=["POST"])
@login_required
def change_username():
    new_username = request.form.get("username")

    if not new_username:
        flash("Username cannot be empty.")
        return redirect(request.referrer)
    
    db = get_db()

    try:
        db.execute(
            "UPDATE users SET username = ? WHERE id = ?",
            (new_username, session["user_id"])
        )

        db.commit()
        # Update session value
        session["username"] = new_username
        flash("Username updated successfully.")
    except sqlite3.IntegrityError:
        flash("Username already taken.")
    
    return redirect(f"/user/{new_username}")

# CHANGE PASSWORD
@profile_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current = request.form.get("current_password")
    new = request.form.get("new_password")
    confirm = request.form.get("confirm_password")

    if not current or not new or not confirm:
        flash("All fields are required.")
        return redirect(request.referrer)
    
    if new != confirm:
        flash("New passwords do not match.")
        return redirect(request.referrer)
    
    db = get_db()

    # Get current password hash
    user = db.execute(
        "SELECT hash FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    # Verify current password
    if not check_password_hash(user["hash"], current):
        flash("Current password is incorrect.")
        return redirect(request.referrer)
    
    # Update password securely
    new_hash = generate_password_hash(new)
    db.execute(
        "UPDATE users SET hash = ? WHERE id = ?",
        (new_hash, session["user_id"])
    )
    db.commit()

    flash("Password updated successfully.")
    return redirect(request.referrer)

# UPDATE PROFILE (BIO + SKILLS)
@profile_bp.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    bio = request.form.get("bio")
    skills = request.form.get("skills")

    db = get_db()

    db.execute("""
        UPDATE users
        SET bio = ?, skills = ?
        WHERE id = ?
    """, (bio, skills, session["user_id"]))

    db.commit()

    flash("Profile updated successfully.")
    return redirect(request.referrer)

# TOGGLE AVAILABILITY
@profile_bp.route("/toggle-offer", methods=["POST"])
@login_required
def toggle_offer():
    db = get_db()

    user = db.execute("SELECT offers_status FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    new_value = 0 if user["offers_status"] else 1

    db.execute("UPDATE users SET offers_status = ? WHERE id = ?", (new_value, session["user_id"],))
    db.commit()

    return redirect(f"/user/{session['username']}")

# DELETE ACCOUNT
@profile_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    db = get_db()
    user_id = session["user_id"]

    # Remove all user-related data
    delete_user_data(db, user_id)

    db.commit()
    # Clear session after deletion
    session.clear()

    flash("Account deleted.")
    return redirect("/register")
