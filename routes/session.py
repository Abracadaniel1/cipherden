from flask import Blueprint, render_template, request, redirect, session, flash, abort
from helpers import login_required, get_db

# Blueprint for session and matching logic
session_bp = Blueprint("session", __name__)

# SEND REQUEST
@session_bp.route("/ask/<username>", methods=["POST"])
@login_required
def ask_status(username):
    db = get_db()

    # Get target user ID
    to_user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()

    if not to_user:
        abort(404)

    # Prevent duplicate pending requests
    existing_request = db.execute("""
        SELECT id FROM requests
        WHERE from_user_id = ?
        AND to_user_id = ?
        AND req_status = 'pending'
        """, (session["user_id"], to_user["id"])).fetchone()
    
    if existing_request:
        flash("Request already sent.")
        return redirect(request.referrer or "/")
    
    # Prevent creating a session if already active
    existing_session = db.execute("""
        SELECT id FROM dev_sessions
        WHERE status = 'active'
        AND (
            (user1_id = ? AND user2_id = ?)
            OR
            (user1_id = ? AND user2_id = ?)
        )
    """, (session["user_id"], to_user["id"],
          to_user["id"], session["user_id"]
    )).fetchone()

    if existing_session:
        flash("You already have an active session with this user.")
        return redirect(request.referrer or "/")

    # Insert new request
    db.execute("INSERT INTO requests (from_user_id, to_user_id) VALUES (?, ?)", (session["user_id"], to_user["id"]))
    db.commit()

    flash(f"You asked {username} for a session.")
    return redirect(request.referrer or "/")

# RESPOND TO REQUEST
@session_bp.route("/requests/<int:request_id>/respond", methods=["POST"])
@login_required
def respond_request(request_id):

    action = request.form.get("action")
    status = "accepted" if action == "accept" else "decline"

    db = get_db()

    # Get request info first
    req = db.execute("SELECT from_user_id, to_user_id FROM requests WHERE id = ?", (request_id,)).fetchone()

    if not req:
        abort(404)

    # Check if a session already exists between these users
    existing_session = db.execute("""
        SELECT id FROM dev_sessions
        WHERE status = 'active'
        AND (
            (user1_id = ? AND user2_id = ?)
            OR
            (user1_id = ? AND user2_id = ?)
        )
    """, (
        req["from_user_id"], req["to_user_id"],
        req["to_user_id"], req["from_user_id"]
    )).fetchone()

    if existing_session:
        flash("Session already active.")
        return redirect(f"/session/{existing_session['id']}")

    #  If accepted -> create session
    if status == "accepted":
        db.execute("""
            INSERT INTO dev_sessions (user1_id, user2_id)
            VALUES (?, ?)
            """, (req["from_user_id"], req["to_user_id"]))

        # Update current request status
        db.execute("UPDATE requests SET req_status = ? WHERE id = ? AND to_user_id = ?", (status, request_id, session["user_id"]))

        # Decline all other requests between same users
        db.execute("""
            UPDATE requests
            SET req_status = 'declined'
            WHERE (
                (from_user_id = ? AND to_user_id = ?)
                OR
                (from_user_id = ? AND to_user_id = ?)
            )
            AND id != ?
        """, (req["from_user_id"], req["to_user_id"],
              req["to_user_id"], req["from_user_id"],
              request_id
        ))

        db.commit()

        # Get last inserted session ID
        session_id = db.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        return redirect(f"/session/{session_id}")

    # If declined
    flash(f"Request {status}.")
    return redirect("/inbox")

# INBOX
@session_bp.route("/inbox")
@login_required
def inbox():
    db = get_db()

    # Pending requests
    requests = db.execute("""
        SELECT requests.id, users.username AS from_username, requests.created_at
        FROM requests
        JOIN users ON requests.from_user_id = users.id
        WHERE requests.to_user_id = ?
        AND requests.req_status = 'pending'
        ORDER BY requests.created_at DESC
    """, (session["user_id"],)).fetchall()

    # Recent requests (accepted/declined)
    accepted_req = db.execute("""
        SELECT requests.id, requests.req_status,
                users.username AS from_username,
                users.email AS from_email
        FROM requests 
        JOIN users ON requests.from_user_id = users.id
        WHERE requests.to_user_id = ?
        ORDER BY requests.created_at DESC
        LIMIT 5
        """, (session["user_id"],)).fetchall()

    return render_template("inbox.html", requests=requests, accepted_req=accepted_req)

# SESSION PAGE
@session_bp.route("/session/<int:session_id>")
@login_required
def dev_session(session_id):
    db = get_db()

    # Get session data
    session_data = db.execute("SELECT * FROM dev_sessions WHERE id = ?", (session_id,)).fetchone()

    if session_data is None:
        flash("Session not found")
        return redirect("/")
    
    # Ensure user is part of the session
    if session["user_id"] not in (
        session_data["user1_id"],
        session_data["user2_id"]
    ):
        abort(403)

    return render_template(
        "session.html",
        dev_session=session_data
    )

# SAVE CODE
@session_bp.route("/session/<int:session_id>/save", methods=["POST"])
@login_required
def save_code(session_id):
    code = request.json.get("code")

    db = get_db()

    # Save code in session
    db.execute(
        "UPDATE dev_sessions SET code = ? WHERE id = ?",
        (code, session_id)
    )

    db.commit()

    return {"status": "saved"}

# Close session
@session_bp.route("/session/<int:session_id>/close", methods=["POST"])
@login_required
def close_session(session_id):

    db = get_db()

    # Mark session as closed
    db.execute("UPDATE dev_sessions SET status = 'closed', ended_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))

    db.commit()

    flash("Session closed.")
    return redirect("/")
