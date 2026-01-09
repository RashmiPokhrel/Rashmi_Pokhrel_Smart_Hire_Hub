console.log("register.js loaded");

document.addEventListener("DOMContentLoaded", () => {

    const roleInput = document.getElementById("role");
    const jobBtn = document.getElementById("jobBtn");
    const recBtn = document.getElementById("recBtn");

    const jobFields = document.getElementById("jobSeekerFields");
    const recruiterFields = document.getElementById("recruiterFields");

    /* ================= ROLE SWITCH ================= */

    function selectRole(role) {
        roleInput.value = role;

        jobBtn.classList.remove("active");
        recBtn.classList.remove("active");

        if (role === "job_seeker") {
            jobBtn.classList.add("active");
            jobFields.classList.remove("hidden");
            recruiterFields.classList.add("hidden");
        } else {
            recBtn.classList.add("active");
            recruiterFields.classList.remove("hidden");
            jobFields.classList.add("hidden");
        }
    }

    jobBtn.addEventListener("click", () => selectRole("job_seeker"));
    recBtn.addEventListener("click", () => selectRole("recruiter"));

    /* ================= FORM SUBMIT ================= */

    const form = document.getElementById("registerForm");

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirm_password").value;

        if (password !== confirmPassword) {
            alert("Passwords do not match");
            return;
        }

        const data = {
            role: roleInput.value,
            password: password,
            confirm_password: confirmPassword,

            username: document.getElementById("username")?.value,
            email: document.getElementById("email")?.value,

            company_name: document.getElementById("company_name")?.value,
            company_email: document.getElementById("company_email")?.value,
            company_phone: document.getElementById("company_phone")?.value,
            company_address: document.getElementById("company_address")?.value
        };

        fetch("/register/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(response => {
            if (response.message) {
                alert("Registration successful!");
                window.location.href = LOGIN_URL;
            } else {
                alert(response.error || "Registration failed");
            }
        })
        .catch(() => alert("Server error"));
    });
});
