document.addEventListener("DOMContentLoaded", () => {
  // Ensure Socker.IO is available
  if (typeof io === "undefined") {
    console.error("Socket.IO library not loaded");
    return;
  }

  // Values injected from the template
  const {ideaId, currentUser, currentUserId} = window;

  if (!ideaId) {
    console.error("Idea ID missing (window.ideaId)");
    return;
  }

  // Connect to WebSocket server
  const socket = io();

  //SOCKET EVENTS
  socket.on("connect", () => console.log("Socket connected:", socket.id));
  socket.on("connect_error", (err) => console.error("Socket connect_error:", err));
  socket.on("disconnect", (reason) => console.warn("Socket disconnected:", reason));

  // Join the room for this specific idea
  socket.emit("join_idea", { idea_id: ideaId });

  // Receive new comments from other users
  socket.on("receive_comment", (data) => {
    addCommentToDOM(data);
  });

  // Receive deletion events from other users
  socket.on("comment_deleted", ({ comment_id }) => {
    removeCommentFromDOM(comment_id);
  });

  // DOM ELEMENTS
  const form = document.getElementById("comment-form");
  const input = document.getElementById("comment-input");
  const commentsList = document.getElementById("comments-list");

  if (!form || !input || !commentsList) {
    console.warn("Missing comment elements");
    return;
  }

  // FORM SUBMIT
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const content = input.value.trim();
    if (!content)
      return;

    console.log("Emitting send_comment:", content);

    socket.emit("send_comment", {
      idea_id: ideaId,
      username: currentUser,
      content: content
    });

    input.value = "";
  });

  // DELETE HANDLER
  document.addEventListener("submit", (e)=> {
    if (!e.target.matches(".delete-comment-form"))
      return;
    e.preventDefault();

    const commentId = e.target.dataset.commentId;
    if (!commentId)
      return;

    socket.emit("delete_comment", {
      comment_id: commentId, idea_id: ideaId
    });
  });

  // FUNCTIONS

  // Add a new comment to the page
  function addCommentToDOM(data) {
    // Prevent adding the same comment twice
    if (document.querySelector(`[data-comment-id="[{data.id}"]`))
      return;

    const wrapper = document.createElement("div");
    wrapper.className = "comment-wrapper";
    wrapper.dataset.commentId = data.id;

    const isOwner = Number(data.user_id) === Number(currentUserId);

    wrapper.innerHTML = `
      <div class="comment" data-comment-id="${data.id}">
        <strong>${escapeHtml(data.username)}</strong>
        <p>${escapeHtml(data.content)}</p>
        ${isOwner ? renderDeleteButton(data.id) : ""}
      </div>
      `;

      commentsList.prepend(wrapper);
  }

  // Remove a comment from the page
  function removeCommentFromDOM(commentId) {
    const el = document.querySelector(`[data-comment-id="${commentId}"]`);
    if (!el)
      return;

    const wrapper = el.closest(".comment-wrapper");
    wrapper ? wrapper.remove() : el.remove();
  }

  // HTML template for the delete button
  function renderDeleteButton(id) {
    return `
      <form class="delete-comment-form" data-comment-id="${id}" action="/comments/${id}/delete" method="POST">
        <button type="submit" class="delete-btn" data-id="${id}">
          Delete
        </button>
      </form>
      `;
  }

  // Escape user content to prevent XSS
  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
