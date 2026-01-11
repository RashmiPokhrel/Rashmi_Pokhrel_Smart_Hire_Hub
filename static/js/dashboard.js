const profileIcon = document.getElementById("profileIcon");
const dropdown = document.getElementById("profileDropdown");

if (profileIcon) {
    profileIcon.addEventListener("click", (e) => {
        e.stopPropagation();
        dropdown.style.display =
            dropdown.style.display === "block" ? "none" : "block";
    });
}

document.addEventListener("click", () => {
    if (dropdown) dropdown.style.display = "none";
});
