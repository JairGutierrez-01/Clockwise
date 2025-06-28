/**
 * Toggles between light and dark mode by modifying body classes.
 * Switches the visibility of the sun and moon icon accordingly.
 * Saves the user's choice in localStorage.
 *
 * Wechselt zwischen hellem und dunklem Modus durch Klassenänderung am <body>.
 * Zeigt passend dazu die Sonne- bzw. Mond-Icons an.
 * Speichert die gewählte Einstellung im localStorage.
 */
function toggleTheme() {
  const body = document.body;
  const sunIcon = document.getElementById("sun-icon");
  const moonIcon = document.getElementById("moon-icon");

  const isDark = body.classList.contains("dark-mode");
  body.classList.toggle("dark-mode", !isDark);
  body.classList.toggle("light-mode", isDark);

  // Save chosen theme
  const newTheme = isDark ? "light" : "dark";
  localStorage.setItem("theme", newTheme);

  if (sunIcon && moonIcon) {
    sunIcon.style.display = isDark ? "inline" : "none";
    moonIcon.style.display = isDark ? "none" : "inline";
  }
}

/**
 * Sets the initial state of the sun/moon icon when the page loads,
 * based on whether dark mode is activated.
 *
 * Setzt beim Laden der Seite den korrekten Initialzustand des Icons,
 * basierend auf gespeichertem Theme oder Systempräferenz.
 */
document.addEventListener("DOMContentLoaded", () => {
  const sunIcon = document.getElementById("sun-icon");
  const moonIcon = document.getElementById("moon-icon");

  const savedTheme = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

  if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
    document.body.classList.add("dark-mode");
    document.body.classList.remove("light-mode");
  } else {
    document.body.classList.add("light-mode");
    document.body.classList.remove("dark-mode");
  }

  const isDark = document.body.classList.contains("dark-mode");

  if (sunIcon && moonIcon) {
    sunIcon.style.display = isDark ? "none" : "inline";
    moonIcon.style.display = isDark ? "inline" : "none";
  }
});
