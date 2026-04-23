from flask import Blueprint, render_template, request, redirect, session, flash, abort
import sqlite3
from helpers import login_required, get_db

# Blueprint for ideas-related routes
ideas_bp = Blueprint("ideas", __name__)

# HOME PAGE
@ideas_bp.route("/")
@login_required
def index():
    db = get_db()

    # Get sorting option from query params
    sort = request.args.get("sort", "recent")
    order = "ideas.created_at DESC"

    # If "top" selected, sort by votes instead
    if sort == "top":
        order = "votes DESC"

    # Fetch ideas with author username and vote count
    ideas = db.execute(f"""
        SELECT ideas.*, users.username, COUNT(votes.id) AS votes
        FROM ideas JOIN users ON ideas.user_id = users.id
        LEFT JOIN votes ON ideas.id = votes.idea_id
        GROUP BY ideas.id ORDER BY {order}
    """).fetchall()
    
    # Current logged-in user
    current_username = session.get("username")

    # List of users  available for collaboration
    available_users = db.execute("SELECT username, offers_status FROM users WHERE username != ? ORDER BY offers_status DESC, username", (current_username,)).fetchall()

    return render_template("index.html", ideas=ideas, available_users=available_users)

# CREATE NEW IDEA
@ideas_bp.route("/ideas/new", methods=["GET", "POST"])
@login_required
def new_idea():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")
        status = request.form.get("status")

        # Validate required fields
        if not title or not description or not category or not status:
            flash("All fields are required.")
            print("Missing fields")
            return redirect("/ideas/new")
        
        # Set progress based on status
        if status == "idea":
            progress = 0
        elif status == "completed":
            progress = 100
        else:
            progress = 50

        try:
            db = get_db()
            # Insert new idea into database
            db.execute("INSERT INTO ideas (user_id, title, description, category, status, progress) VALUES (?, ?, ?, ?, ?, ?)", (session["user_id"], title, description, category, status, progress))
            db.commit()
        except Exception as e:
            flash("An error occurred while creating the idea.")
            return redirect("/ideas/new")

        flash("Idea created successfully.")
        return redirect("/")
    
    return render_template("new_idea.html")

# IDEA DETAIL PAGE
@ideas_bp.route("/ideas/<int:idea_id>")
@login_required
def idea_detail(idea_id):
    db = get_db()

    # Fetch idea with author and vote count
    idea = db.execute("""
        SELECT ideas.*, users.username, COUNT(votes.id) AS votes
        FROM ideas JOIN users ON ideas.user_id = users.id
        LEFT JOIN votes ON ideas.id = votes.idea_id
        WHERE ideas.id = ? GROUP BY ideas.id
    """, (idea_id,)).fetchone()
    
    # Check if current user already voted
    user_vote = db.execute("SELECT 1 FROM votes WHERE user_id = ? AND idea_id = ?", (session["user_id"], idea_id)).fetchone()

    if idea is None:
        flash("Idea not found.")
        return redirect("/")
    
    # Fetch comments (excluding deleted ones)
    comments = db.execute("""
        SELECT comments.*, users.username
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.idea_id = ?
        AND comments.deleted = 0
        ORDER BY comments.created_at DESC
    """, (idea_id,)).fetchall()

    return render_template("idea_detail.html", idea=idea, comments=comments, user_vote=user_vote)

# VOTE IDEA
@ideas_bp.route("/ideas/<int:idea_id>/vote", methods=["POST"])
@login_required
def vote_idea(idea_id):
    db = get_db()

    try:
        # Insert vote
        db.execute("INSERT INTO votes (user_id, idea_id) VALUES (?, ?)", (session["user_id"], idea_id))
        db.commit()
    except sqlite3.IntegrityError:
        flash("You have already voted for this idea.")

    return redirect(f"/ideas/{idea_id}")

# ADD COMMENT
@ideas_bp.route("/ideas/<int:idea_id>/comment", methods=["POST"])
@login_required
def add_comment(idea_id):
    content = request.form.get("content")

    # Prevent empty comments
    if not content:
        flash("Comment cannot be empty.")
        return redirect(f"/ideas/{idea_id}")
    
    db = get_db()

    # Insert commnet into database
    db.execute("INSERT INTO comments (idea_id, user_id, content) VALUES (?, ?, ?)", (idea_id, session["user_id"], content))
    db.commit()

    flash("Comment added successfully.")
    return redirect(f"/ideas/{idea_id}")

# UPDATE IDEA PROGRESS
@ideas_bp.route("/ideas/<int:idea_id>/edit", methods=["GET", "POST"])
@login_required
def edit_idea(idea_id):
    progress = request.form.get("progress")
    
    # Validate progress value
    if not progress or not progress.isdigit():
        flash("Invalid progress value.")
        return redirect(f"/ideas/{idea_id}")
    
    progress = int(progress)

    # Update status based on progress
    if progress == 0:
        status = "idea"
    elif progress == 100:
        status = "completed"
    else:
        status = "in_progress"
    
    db = get_db()

    # Update only if the idea belongs to the user
    db.execute("UPDATE ideas SET progress = ?, status = ? WHERE id = ? AND user_id = ?", (progress, status, idea_id, session["user_id"]))
    db.commit()

    return redirect(f"/ideas/{idea_id}")

# DELETE IDEA
@ideas_bp.route("/ideas/<int:idea_id>/delete", methods=["POST"])
@login_required
def delete_idea(idea_id):
    db = get_db()

    # Ensure the idea belongs to the user
    idea = db.execute(
        "SELECT progress FROM ideas WHERE id = ? AND user_id = ?",
        (idea_id, session["user_id"])
    ).fetchone()

    if not idea:
        abort(403)

    # Allow deletion only if completed
    if idea["progress"] != 100:
        flash("You can delete only completed ideas.")
        return redirect(f"/ideas/{idea_id}")
    
    db.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
    db.commit()

    flash("Idea deleted.")
    return redirect("/")

# DELETE COMMENT (SOFT DELETE)
@ideas_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    db = get_db()
    # Mark comment as deleted instead of removing it
    db.execute("UPDATE comments set deleted = 1 WHERE id = ? AND user_id = ?", (comment_id, session["user_id"]))
    db.commit()

    idea = db.execute("SELECT idea_id FROM comments WHERE id = ?", (comment_id,)).fetchone()
    if idea:
        from app import socketio
        socketio.emit("comment_deleted", {"comment_id": comment_id}, to=f"idea_{idea['idea_id']}")

    return redirect(request.referrer)
