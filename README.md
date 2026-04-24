# CipherDen - Community Idea Hub

**CipherDen** is a lightweight community idea hub where developers share proposals, vote, comment and collaborate in real time via paired coding sessions with live chat and shared code execution.

CipherDen aims to evolve into a collaborative coding arena where developers not only share ideas, but actively solve problems together in real-time.

### Features
- **User authentication** with session-based login and password hashing
- **Create and manage ideas** with status badges and progress tracking
- **Voting and commenting** on ideas
- **User profiles** with bio and skills tags
- **Dev session matching** and session offers
- **Real-time collaborative coding** using Socket.IO
- **Live chat and typing indicator** inside sessions
- **Transient flash messages**  and UI feedback

----

### Tech Stack
**Backend**: Flask (Python)
**Database**: SQLite (schema in `schema.sql`)
**Frontend**: HTML, CSS, JavaScript; CodeMirror for the editor
**Real-Time**: Flask-SocketIO

----

### Project Structure
```
/CipherDen_Project
    |---- app.py
    |---- helpers.py
    |---- init_db.py
    |---- socket_events.py
    |---- schema.sql
    |---- README.md
    |---- requirements.txt
    |
    |---- routes/
    |       |---- auth.py
    |       |---- ideas.py
    |       |---- profile.py
    |       |---- session.py
    |       |---- init.py
    |
    |---- templates/
    |       |---- idea_detail.html
    |       |---- inbox.html
    |       |---- index.html
    |       |---- layout.html
    |       |---- login.html
    |       |---- new_idea.html
    |       |---- profile.html
    |       |---- register.html
    |       |---- session.html
    |
    |---- static/
            |---- css
            |      |---- base.css
            |      |---- components.css
            |      |---- layout.css
            |      |---- profile.css
            |      |---- session.css
            |      |---- theme.css
            |
            |---- script.js
            |---- session.js
```

### Installation
1. Clone the repository

```bash
git clone https://github.com/Abracadaniel1/cipherden.git
cd cipherden
```

2. Create virtual environment and install dependencies
```bash
python -m venv venv

source venv/bin/activate # macOS Linux
venv\Scripts\activate # Windows

pip install -r requirements.txt
```

3. Initialize the database (only first time)

```bash
python init_db.py
```

4. Run the app for development

```bash
flask run
```

or

```bash
python app.py
```

### Default Behavior

- A new SQLite database is created locally
- No users are preloaded
- You must register a new account to start using the app

### Authentication & Security

- Passwords are hashed using Werkzeug
- Session-based authentication
- Protected routes via login_required decorator
- Users can only modify their own content
- Code execution is limited with a timeout(prevents infinite loops)

Note: In a production environment, code execution should be sandboxed for security

### Real-Time Features

- Live code synchronization between users
- Shared Python code execution
- Live chat inside sessions
- Typing indicator
- Cursor tracking

### Configuration

Make sure to set a secret key for sessions:
    export SECRET_KEY=your_secret_key
(or configure it directly in app.py for development)

### Production Notes

- Disable Flask debug mode
- Use a production server (e.g. gunicorn)
- Replace SQLite with PostgresSQL or MySQL
- Secure cookies and environment variables
- Sandbox code execution for safety

### Future Improvements

- Improved skill-based matching algorithm
- Persistent chat history
- Notification system
- UI/UX enhancements
- Docker support
- Interactive coding challenges:
    - 1v1 debugging sessions (solve real or predefined bugs in real-time)
    - User-submitted debugging requests (community driven problem solving)
    - Collaborative coding challenges and team-based sessions

### Notes

This project was built as learning project and focuses on:

- Full-Stack development with Flask
- Real-Time features using WebSockets
- Clean Modular structure
- Practical collaboration tools for developers