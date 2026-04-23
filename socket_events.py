from flask_socketio import join_room, emit
from flask import session
from helpers import execute_python, get_db, save_comment

# Initialize all socket events
def init_socket(socketio):
    # JOIN SESSION ROOM
    @socketio.on("join_session")
    def join_session(data):
        # User joins a specific session room.
        join_room(str(data["session_id"]))

    # LIVE CODE SYNC
    @socketio.on("code_update")
    def code_update(data):
        # Broadcast code changes to other users in the same session.
        emit(
            "code_update",
            {"code": data["code"]},
            to=str(data["session_id"]),
            include_self=False
        )

    # RUN CODE
    @socketio.on("run_code")
    def run_code(data):
        # Execute Python code on the server and returns output/error
        output, error = execute_python(data["code"])

        emit(
            "console_output",
            {
                "output": output,
                "error": error
            },
            to=str(data["session_id"])
        )

    # CHAT MESSAGES
    @socketio.on("send_message")
    def handle_message(data):
        # Sends a chat message to the user in the seme session.
        emit(
            "receive_message",
            {
                "username": session.get("username"),
                "message": data["message"]
            },
            to=str(data["session_id"])
        )

    # TYPING INDICATOR
    @socketio.on("typing")
    def typing(data):
        # Notify other that a user is typing.
        session_id = data["session_id"]
        username = session.get("username")
        if not username:
            return

        emit(
            "user_typing",
            {"username": username},
            to=str(session_id),
            include_self=False
        )

    # STOP TYPING
    @socketio.on("stop_typing")
    def stop_typing(data):
        # Notify other that the user stopped typing.
        session_id = data["session_id"]

        emit(
            "user_stop_typing",
            to=str(session_id),
            include_self=False
        )

    # CURSOR SHARING
    @socketio.on("cursor_move")
    def handle_cursor(data):
        # Share cursor position with other user
        emit(
            "cursor_move",
            {
                "username": data["username"],
                "cursor": data["cursor"]
            },
            to=str(data["session_id"]),
            include_self=False
        )

    @socketio.on("join_idea")
    def join_idea(data):
        join_room(f"idea_{data['idea_id']}")

    @socketio.on("broadcast_comment")
    def broadcast_comment(data):
        emit(
            "receive_comment",
            data,
            to=f"idea_{data['idea_id']}",
            include_self=False
        )

    @socketio.on("send_comment")
    def handle_comment(data):
        idea_id = data.get("idea_id")
        content = data.get("content")
        username = data.get("username")

        if not idea_id or not content:
            return
        
        try:
            if 'save_comment' in globals():
                comment = save_comment(idea_id, session.get("user_id"), content)
            else:
                db = get_db()
                db.execute("INSERT INTO comments(idea_id, user_id, content) VALUES (?, ?, ?)", (idea_id, session.get("user_id"), content))
                db.commit()
                comment = db.execute("SELECT id, idea_id, user_id, content,created_at FROM comments WHERE rowid = last_insert_rowid()").fetchone()
        except Exception as e:
            print("Error saving comment: ", e)
            return
        
        payload = {
            "id": comment["id"] if comment else None,
            "idea_id": idea_id,
            "user_id": session.get("user_id"),
            "username": username,
            "content": comment["content"],
            "created_at": comment["created_at"] if comment and "created_at" in comment.keys() else None
        }
        emit(
            "receive_comment",
            payload,
            to=f"idea_{idea_id}",
            include_self=True
        )

    @socketio.on("delete_comment")
    def handle_delete_comment(data):
        comment_id = data.get("comment_id")
        idea_id = data.get("idea_id")
        
        if not comment_id or not idea_id:
            return
        
        db = get_db()

        db.execute("UPDATE comments SET deleted = 1 WHERE id = ? AND user_id = ?", (comment_id, session.get("user_id")))

        db.commit()

        emit(
            "comment_deleted",
            {"comment_id":comment_id},
            to=f"idea_{idea_id}",
            include_self=True
        )