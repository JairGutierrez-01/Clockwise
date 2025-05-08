// static/theme.js

function toggleTheme() {
  const body = document.body;
  const sunIcon = document.getElementById('sun-icon');
  const moonIcon = document.getElementById('moon-icon');

  if (body.classList.contains('dark-mode')) {
    body.classList.remove('dark-mode');
    body.classList.add('light-mode');
    if (sunIcon && moonIcon) {
      sunIcon.style.display = 'inline';
      moonIcon.style.display = 'none';
    }
  } else {
    body.classList.remove('light-mode');
    body.classList.add('dark-mode');
    if (sunIcon && moonIcon) {
      sunIcon.style.display = 'none';
      moonIcon.style.display = 'inline';
    }
  }
}

