document.addEventListener("DOMContentLoaded", () => {
    const textarea = document.getElementById("editor");
    if (!textarea)
        return;

    const sessionId = textarea.dataset.session;
    if (!sessionId) {
        console.error("Session ID missing");
        return;
    }

    const socket = io();

    // Initialize all session features
    const editor = initEditor(textarea);
    initRealTimeSync(editor, socket, sessionId);
    initConsole(editor, socket, sessionId);
    initChat(socket, sessionId);
    initDownload(editor);
    initAutoSave(editor, sessionId);
});

// Code Editor Initialization
function initEditor(textarea) {
    return CodeMirror.fromTextArea(textarea, {
        lineNumbers: true,
        mode: "python",
        theme: "default"
    });
}

// Real-Time Code Sync
function initRealTimeSync(editor,socket,sessionId) {
    let isRemoteUpdating = false;

    socket.emit("join_session", { session_id: sessionId });

    let timeout;

    // Send code updates
    editor.on("change", () => {
        if (isRemoteUpdating)
            return;

        clearTimeout(timeout);

        timeout = setTimeout(() => {
            socket.emit("code_update", {
                session_id: sessionId,
                code: editor.getValue()
            });
        }, 150);
    });

    // Apply remote code updates
    socket.on("code_update", data => {
        if (data.code === editor.getValue())
            return;

        const cursor = editor.getCursor();

        isRemoteUpdating = true;

        editor.operation(() => {
            editor.setValue(data.code);
            editor.setCursor(cursor);
        });

        isRemoteUpdating = false;
    });

    // Cursor broadcasting
    let lastEmit = 0;
    editor.on("cursorActivity", () => {
        const now = Date.now();
        if (now - lastEmit < 50)
            return;

        lastEmit = now;

        const cursor = editor.getCursor();

        requestAnimationFrame(() => {
            socket.emit("cursor_move", {
                session_id: sessionId,
                cursor: cursor,
                username: CURRENT_USERNAME
            });
        });
    });

    // Display remote cursors
    let remoteCursors = {};

    socket.on("cursor_move", (data) => {
        const { cursor, username } = data;

        if (!username)
            return;

        if (remoteCursors[username]) {
            remoteCursors[username].clear();
        }

        remoteCursors[username] = editor.setBookmark(cursor, {
            widget: createCursorElement(username)
        });
    });
}

// Console 
function initConsole(editor, socket, sessionId) {
    const runBtn = document.getElementById("run-btn");
    const consoleBox = document.getElementById("console");

    if (!runBtn || !consoleBox)
        return;

    runBtn.onclick = () => {
        runBtn.disabled = true;

        consoleBox.textContent += "\n> Running code...\n";
        
        // Slight delay for smoother UX
        setTimeout(() => {
            socket.emit("run_code", {
                session_id: sessionId,
                code: editor.getValue()
            });
        }, 300);

        setTimeout(() => {
            runBtn.disabled = false;
        }, 1000);
    };

    // Append output from server
    socket.on("console_output", data => {
        consoleBox.textContent +=
            (data.output || "") +
            (data.error || "") + "\n";
        
        consoleBox.scrollTop = consoleBox.scrollHeight;
    });
}

// Real Time Chat
function initChat(socket, sessionId) {
    const chatBox = document.getElementById("chat-box");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const typingIndicator = document.getElementById("typing-indicator");

    if (!chatBox || !chatInput || !sendBtn)
        return;
    
    // Add message to chat UI
    const addMessage = (user, text) => {
        const msg = document.createElement("div");
        msg.innerHTML = `<strong>${user}:</strong> ${text}`;
        chatBox.appendChild(msg);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    // Enter key sends message
    chatInput.addEventListener("keydown", e => {
        if (e.key === "Enter")
            sendBtn.click();
    });

    // Send message
    sendBtn.onclick = () => {
        const text = chatInput.value.trim();
        if (!text)
            return;

        socket.emit("send_message", {
            session_id: sessionId,
            message: text
        });
        chatInput.value = "";
    };

    // Receive Message
    socket.on("receive_message", data => {
        addMessage(data.username, data.message);
    });

    // Typing indicator logic
    let typingTimeout;
    let typingInterval;
    let isTyping = false;

    chatInput.addEventListener("input", () => {
        if(!isTyping) {
            socket.emit("typing", { session_id: sessionId });
            isTyping = true;

            typingInterval = setInterval(() => {
                socket.emit("typing", { session_id: sessionId });
            }, 1000);
        }

        clearTimeout(typingTimeout);

        typingTimeout = setTimeout(() => {
            socket.emit("stop_typing", { session_id: sessionId });
            isTyping = false;

            clearTimeout(typingInterval);
        }, 1500);
    });

    // Show typing indicator
    let typingTimeoutUI;

    socket.on("user_typing", (data) => {
        if (!typingIndicator)
            return;

        typingIndicator.textContent = `${data.username} is typing...`;

        clearTimeout(typingTimeoutUI);
        typingTimeoutUI = setTimeout(() => {
            typingIndicator.textContent = "";
        }, 2000);
    });

    socket.on("user_stop_typing", () => {
        if (!typingIndicator)
            return;

        typingIndicator.textContent = "";
    });
}

// Download Code as File
function initDownload(editor) {
    const downloadBtn = document.getElementById("download-btn");
    if (!downloadBtn)
        return;

    downloadBtn.onclick = () => {
        const blob = new Blob([editor.getValue()], { type: "text/plain" });

        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "code.py";
        link.click();
    };
}

// Auto-Save (every 3 seconds)
function initAutoSave(editor, sessionId) {
    let lastCode = "";
    setInterval(() => {
        const current = editor.getValue();
        if (current === lastCode)
            return;

        lastCode = current;

        fetch(`/session/${sessionId}/save`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: current })
        });
    }, 3000);
}

// Remote Cursor Rendering
function createCursorElement(username) {
    const color = getUserColor(username);

    const wrapper = document.createElement("span");

    wrapper.style.display = "inline-block";
    wrapper.style.width = "0";
    wrapper.style.position = "relative";

    const cursor = document.createElement("span");
    cursor.style.display = "inline-block";
    cursor.style.width = "2px";
    cursor.style.height = "1em";
    cursor.style.background = color;
    cursor.style.boxShadow = `0 0 6px ${color}`;
    cursor.style.animation = "blink 1s infinite";
    cursor.style.position = "relative";
    cursor.style.top = "3px";

    const label = document.createElement("span");

    label.textContent = username;
    label.style.position = "absolute";
    label.style.top = "-1.6em";
    label.style.left = "50%";
    label.style.transform = "translateX(-50%)";
    label.style.background = color;
    label.style.color = "white";
    label.style.fontSize = "9px";
    label.style.padding = "1px 4px";
    label.style.borderRadius = "6px";
    label.style.whiteSpace = "nowrap";
    label.style.pointerEvents = "none";
    label.style.boxShadow = `0 2px 6px ${color}55`;

    // Fade out label after a moment
    setTimeout(() => {
        label.style.opacity = "0";
        setTimeout(() => label.remove(), 1000);
    }, 2000);

    wrapper.appendChild(cursor);
    wrapper.appendChild(label);
    return wrapper; 
}

// Deterministic Color Generator
function getUserColor(username) {
    let hash = 0;

    for (let i = 0; i < username.length; i++) {
        hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = (Math.abs(hash) * 137) % 360;
    return `hsl(${hue}, 70%, 50%)`;
}