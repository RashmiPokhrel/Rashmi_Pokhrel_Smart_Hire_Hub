const form = document.getElementById("loginForm");
const errorMsg = document.getElementById("errorMsg");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const response = await fetch("/login/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });

    const data = await response.json();

    if (response.ok) {
        // ROLE BASED REDIRECT
        if (data.role === "recruiter") {
            window.location.href = "/recruiter-dashboard/";
        } else if (data.role === "job_seeker") {
            window.location.href = "/jobseeker-dashboard/";
        } else {
            errorMsg.innerText = "Unknown user role";
        }
    } else {
        errorMsg.innerText = data.error || "Login failed";
    }
});

/* SHOW / HIDE PASSWORD */
document.querySelector(".toggle-password").addEventListener("click", function () {
    const password = document.getElementById("password");
    this.classList.toggle("fa-eye-slash");
    password.type = password.type === "password" ? "text" : "password";
});

/* CSRF TOKEN */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        document.cookie.split(";").forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}
