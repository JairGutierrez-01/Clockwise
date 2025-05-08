// static/theme.js

function toggleTheme() {
  const body = document.body;
  const sunIcon = document.getElementById('sun-icon');
  const moonIcon = document.getElementById('moon-icon');

  const isDark = body.classList.contains('dark-mode');
  body.classList.toggle('dark-mode', !isDark);
  body.classList.toggle('light-mode', isDark);

  if (sunIcon && moonIcon) {
    sunIcon.style.display = isDark ? 'inline' : 'none';
    moonIcon.style.display = isDark ? 'none' : 'inline';
  }
}

// Direkt beim Laden den korrekten Icon anzeigen
document.addEventListener('DOMContentLoaded', () => {
  const sunIcon = document.getElementById('sun-icon');
  const moonIcon = document.getElementById('moon-icon');
  const isDark = document.body.classList.contains('dark-mode');

  if (sunIcon && moonIcon) {
    sunIcon.style.display = isDark ? 'none' : 'inline';
    moonIcon.style.display = isDark ? 'inline' : 'none';
  }
});


