document.addEventListener('DOMContentLoaded', function() {
    initProgressBar();
    initThemeToggle();
    initEditProfile();
    initFlashMessages();
    initPasswordValidation();
});

// Set the width of the progress bar based on the data-progress attribute
function initProgressBar() {
    const fills = document.querySelectorAll('.progress-fill');
    fills.forEach(fill => {
        fill.style.width = fill.dataset.progress + '%';
    });
}

// Toggle between light and fluo mode, and save the preference in localStorage
function initThemeToggle() {
    const toggle = document.getElementById('theme-toggle');

    // Apply the saved theme on page load
    if (localStorage.getItem('theme') === 'fluo-mode') {
        document.body.classList.add('fluo-mode');
    }

    if (toggle) {
        toggle.addEventListener('click', () => {
            document.body.classList.toggle('fluo-mode');
            
            // Save the preference in localStorage
            if (document.body.classList.contains('fluo-mode')) {
                localStorage.setItem('theme', 'fluo-mode');
            } else {
                localStorage.removeItem('theme');
            }
        });
    }
}

// Open the edit profile panel when the edit button is clicked, and close it when clicking outside or on the close button
function initEditProfile() {
    const editBtn = document.getElementById("edit-profile-btn");
    const panel = document.getElementById("edit-profile-panel");
    const closeBtn = document.getElementById("close-profile-panel");

    if (!editBtn || !panel)
        return;

    // Open the panel when the edit button is clicked
    editBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        panel.classList.add("open");
    });

    // Close the panel when the close button is clicked
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            panel.classList.remove("open");
        });
    }

    // Close the panel when clicking outside of it
    document.addEventListener("click", () => {
        panel.classList.remove("open");
    });

    // Prevent clicks inside the panel from closing it
    panel.addEventListener("click", (e) => {
        e.stopPropagation();
    });
}

// Automatically hide flash messages after 3 seconds, with a fade-out effect before removing them from the DOM
function initFlashMessages() {
    const flashes = document.querySelectorAll(".flash-messages li");

    flashes.forEach(flash => {
        setTimeout(() => {
            flash.classList.add("hide");

            setTimeout(() => {
                flash.remove();
            }, 400);
        }, 3000);
    });
}

// Validate the password input in real-time and show/hide the corresponding rules based on the current value
function initPasswordValidation() {
    const password = document.getElementById("password");

    if (!password)
        return;

    password.addEventListener("input", () => {
        const value = password.value;
        toggleRule("rule-length", value.length >= 8);
        toggleRule("rule-upper", /[A-Z]/.test(value));
        toggleRule("rule-lower", /[a-z]/.test(value));
        toggleRule("rule-number", /[0-9]/.test(value))
    });
}

// Show or hide a password rule element based on whether the rule is valid or not
function toggleRule(id, valid) {
    const el = document.getElementById(id);
    if (!el)
        return;

    if (valid) {
        el.style.opacity = "0";
        el.style.maxHeight = "0";
    } else {
        el.style.opacity = "1";
        el.style.maxHeight = "20px"
    }
}