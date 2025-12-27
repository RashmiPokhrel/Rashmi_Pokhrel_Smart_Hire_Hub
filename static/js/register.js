document.addEventListener("DOMContentLoaded", () => {
    console.log("register.js loaded");

    const form = document.getElementById("registerForm");

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        console.log("Form submit intercepted");

        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirm_password").value;

        if (password !== confirmPassword) {
            alert("Passwords do not match");
            return;
        }

        const data = {
            role: document.getElementById("role").value,
            password: password,
            confirm_password: confirmPassword,

            username: document.getElementById("username")?.value,
            email: document.getElementById("email")?.value,

            company_name: document.getElementById("company_name")?.value,
            company_email: document.getElementById("company_email")?.value,
            company_phone: document.getElementById("company_phone")?.value,
            company_address: document.getElementById("company_address")?.value
        };

        console.log("📦 Sending data:", data);

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
                alert(response.error);
            }
        })
        .catch(err => {
            console.error(err);
            alert("Server error");
        });
    });
});
