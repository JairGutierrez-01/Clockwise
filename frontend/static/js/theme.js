// static/js/theme.js

/**
 * Toggles between light and dark mode by modifying body classes.
 * Switches the visibility of the sun and moon icon accordingly.
 */
function toggleTheme() {
  const body = document.body;
  const sunIcon = document.getElementById("sun-icon");
  const moonIcon = document.getElementById("moon-icon");

  const isDark = body.classList.contains("dark-mode");
  body.classList.toggle("dark-mode", !isDark);
  body.classList.toggle("light-mode", isDark);

  if (sunIcon && moonIcon) {
    sunIcon.style.display = isDark ? "inline" : "none";
    moonIcon.style.display = isDark ? "none" : "inline";
  }
}

/**
 * Sets the initial state of the sun/moon icon when the page loads,
 * based on whether dark mode is activated.
 */
document.addEventListener("DOMContentLoaded", () => {
  const sunIcon = document.getElementById("sun-icon");
  const moonIcon = document.getElementById("moon-icon");
  const isDark = document.body.classList.contains("dark-mode");

  if (sunIcon && moonIcon) {
    sunIcon.style.display = isDark ? "none" : "inline";
    moonIcon.style.display = isDark ? "inline" : "none";
  }
});
