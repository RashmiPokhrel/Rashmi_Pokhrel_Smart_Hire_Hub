const profileIcon = document.getElementById("profileIcon");
const dropdown = document.getElementById("profileDropdown");

profileIcon.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.style.display =
        dropdown.style.display === "block" ? "none" : "block";
});

document.addEventListener("click", () => {
    dropdown.style.display = "none";
});





document.getElementById("logoutBtn").addEventListener("click", async () => {
    const response = await fetch("/logout/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        }
    });

    if (response.ok) {
        window.location.href = "/login/";
    }
});
