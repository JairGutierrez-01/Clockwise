// static/timeTracking.js
document.addEventListener('DOMContentLoaded', () => {
  const display = document.getElementById('tracker-time');
  const btn     = document.getElementById('tracker-btn');
  let startTime    = null;
  let timerInterval = null;

  function formatTime(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const hours   = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return (
      String(hours).padStart(2,'0') + ':' +
      String(minutes).padStart(2,'0') + ':' +
      String(seconds).padStart(2,'0')
    );
  }

  btn.addEventListener('click', () => {
    if (timerInterval === null) {
      // start
      startTime = Date.now();
      btn.textContent = 'Stop Tracking';
      timerInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        display.textContent = formatTime(elapsed);
      }, 1000);
    } else {
      // stop
      clearInterval(timerInterval);
      timerInterval = null;
      btn.textContent = 'Start Tracking';
    }
  });
});