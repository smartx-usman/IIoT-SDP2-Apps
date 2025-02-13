document.addEventListener("DOMContentLoaded", function () {
    var actionDropdown = document.getElementById("actionDropdown");
    var dropdownMenu = document.querySelector(".dropdown-menu");

    // Keep dropdown expanded by default
    actionDropdown.setAttribute("aria-expanded", "true");
    dropdownMenu.classList.add("show");

    // Toggle dropdown behavior
    actionDropdown.addEventListener("click", function (event) {
        dropdownMenu.classList.toggle("show");
        this.setAttribute("aria-expanded", dropdownMenu.classList.contains("show"));
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function (event) {
        if (!event.target.closest(".dropdown")) {
            dropdownMenu.classList.remove("show");
            actionDropdown.setAttribute("aria-expanded", "false");
        }
    });
});
