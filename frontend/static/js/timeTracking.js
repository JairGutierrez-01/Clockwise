// static/timeTracking.js

// ============================================================================
//                          API Calls Section
// Defines functions to interact with the backend
// ============================================================================
/* === comment out API calls ===

async function fetchTimeEntries() {
  const res = await fetch('/time_entries');
  if (!res.ok) throw new Error('Failed to fetch time entries');
  return res.json();
}


async function createTimeEntry(data) {
  const res = await fetch('/time_entries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_id: data.project_id,
      start_time: data.start_time
    })
  });
  if (!res.ok) throw new Error('Failed to create time entry');
  return res.json();
}


async function updateTimeEntry(id, data) {
  const res = await fetch(`/time_entries/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to update time entry');
  return res.json();
}


async function deleteTimeEntry(id) {
  const res = await fetch(`/time_entries/${id}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete time entry');
}
=== End real API block === */
// ============================================================================
// Mock Backend Implementation
// Provides temporary in-memory functions to simulate backend behavior.
// ============================================================================
const mockEntries = [];

async function fetchTimeEntries() {
  return Promise.resolve(mockEntries.map(e => ({ ...e })));
}

async function createTimeEntry(data) {
  const id = Date.now();
  const entry = {
    time_entry_id: id,
    project_id:    data.project_id,
    name:          data.name || "",
    start_time:    data.start_time,
    end_time:      null,
    duration:      "00:00:00"
  };
  mockEntries.push(entry);
  return Promise.resolve({ ...entry });
}

async function updateTimeEntry(id, data) {
  const idx = mockEntries.findIndex(e => e.time_entry_id === id);
  if (idx > -1) {
    mockEntries[idx] = { ...mockEntries[idx], ...data };
    return Promise.resolve({ ...mockEntries[idx] });
  }
  return Promise.reject(new Error("Not found"));
}

async function deleteTimeEntry(id) {
  const idx = mockEntries.findIndex(e => e.time_entry_id === id);
  if (idx > -1) mockEntries.splice(idx, 1);
  return Promise.resolve();
}

/**
 * Formats a duration in milliseconds to a HH:MM:SS string.
 * @function formatTime
 * @param {number} ms - Duration in milliseconds.
 * @returns {string} Formatted time string.
 */
function formatTime(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return (
    String(hours).padStart(2, "0") +
    ":" +
    String(minutes).padStart(2, "0") +
    ":" +
    String(seconds).padStart(2, "0")
  );
}

// ============================================================================
// Main Application Logic
// Sets up event listeners, state management, and UI update routines after DOM load.
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  // --- Cache DOM Elements ---
  const trackerEl = document.querySelector('.tracker');

  const display = document.getElementById("tracker-time");
  const startBtn = document.getElementById("tracker-start");
  const stopBtn = document.getElementById("tracker-stop");
  const pauseBtn = document.getElementById("tracker-pause");
  const resumeBtn = document.getElementById("tracker-resume");
  const input = document.getElementById("project-name-input");
  const list = document.getElementById("project-list");
  const emptyMessage = document.getElementById("empty-message");
  const template = document.getElementById("project-template");

  // --- State Variables ---
  // elapsedTime: milliseconds counted
  // currentEntryId: ID of the active time entry
  // startDisplay: formatted start time string for UI
  // timerInterval: reference to the interval timer
  // startTime: Date when the timer started
  let elapsedTime = 0;
  let currentEntryId = null;
  let startDisplay = "";
  let timerInterval = null;
  let startTime = null;

  // --- Handle Empty State Display ---
  // Show or hide the 'no projects' message based on list content.
  /**
   * Shows or hides the empty state message based on project list content.
   * @function updateEmptyState
   * @returns {void}
   */
  function updateEmptyState() {
    emptyMessage.style.display = list.children.length === 0 ? "block" : "none";
  }

  // --- Render a Single Time Entry in the UI ---
  // Clones the project template, populates data, and appends to project list.
  /**
   * Renders a single time entry in the project list UI.
   * @function renderEntry
   * @param {Object} entry - Time entry data.
   * @param {number} entry.time_entry_id - Unique identifier.
   * @param {string} entry.name - Project name.
   * @param {string} entry.start_time - Start time string.
   * @param {?string} entry.end_time - End time string or null.
   * @param {string} entry.duration - Duration string in HH:MM:SS.
   * @returns {void}
   */
  function renderEntry(entry) {
    const clone = template.content.cloneNode(true);
    const wrapper = clone.querySelector(".project-wrapper");
    wrapper.dataset.id = entry.time_entry_id || entry.id;
    clone.querySelector(".project-name").textContent = entry.name;
    clone.querySelector(".time-range").textContent = entry.start_time + " - " + (entry.end_time || "");
    clone.querySelector(".duration").textContent = entry.duration;
    list.appendChild(clone);
    // Animate new entry
    wrapper.classList.add('new-entry');
    wrapper.addEventListener('animationend', () => {
      wrapper.classList.remove('new-entry');
    });
    updateEmptyState();
  }

  // --- Load and Render All Entries on Page Load ---
  // Fetches existing entries and invokes renderEntry for each.
  /**
   * Fetches and renders all existing time entries on page load.
   * @async
   * @function loadEntries
   * @returns {Promise<void>}
   */
  async function loadEntries() {
    const entries = await fetchTimeEntries();
    entries.forEach(renderEntry);
  }

  // --- Start Button: Create and Start Timer for a New Entry ---
  startBtn.addEventListener("click", async () => {
    const name = input.value.trim();
    if (!name) return;
    input.disabled = true;
    startBtn.hidden = true;
    pauseBtn.hidden = false;
    stopBtn.hidden = false;
    resumeBtn.hidden = true;

    // Trigger slide-in animation for controls
    trackerEl.classList.add('animate-controls');

    const now = new Date();
    startTime = now;
    elapsedTime = 0;
    display.textContent = "00:00:00";
    timerInterval = setInterval(() => {
      elapsedTime = Date.now() - startTime;
      display.textContent = formatTime(elapsedTime);
    }, 1000);
    // Create entry in backend
    const entry = {
      project_id: parseInt(input.dataset.projectId),
      start_time: now.toISOString(),
      name: name
    };
    const newEntry = await createTimeEntry(entry);
    currentEntryId = newEntry.time_entry_id || newEntry.id;
    startDisplay = new Date(newEntry.start_time).toLocaleTimeString();
  });

  // --- Pause Button: Pause Active Timer ---
  pauseBtn.addEventListener("click", () => {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
      pauseBtn.hidden = true;
      resumeBtn.hidden = false;
    }
  });

  // --- Resume Button: Continue Paused Timer ---
  resumeBtn.addEventListener("click", () => {
    startTime = Date.now() - elapsedTime;
    timerInterval = setInterval(() => {
      elapsedTime = Date.now() - startTime;
      display.textContent = formatTime(elapsedTime);
    }, 1000);
    resumeBtn.hidden = true;
    pauseBtn.hidden = false;
  });

  // --- Stop Button: Stop Timer, Update Entry, and Reset UI ---
  stopBtn.addEventListener("click", async () => {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    const endTime = new Date();
    const durationStr = formatTime(elapsedTime);
    // Update backend
    const updatedEntry = await updateTimeEntry(currentEntryId, {
      end_time: endTime.toISOString(),
      duration: durationStr
    });
    // Prepare display values
    updatedEntry.start_time = startDisplay;
    updatedEntry.end_time = new Date(updatedEntry.end_time).toLocaleTimeString();
    updatedEntry.duration = durationStr;
    renderEntry(updatedEntry);
    // Reset controls and input
    stopBtn.hidden = true;
    pauseBtn.hidden = true;
    resumeBtn.hidden = true;
    startBtn.hidden = false;
    input.disabled = false;
    input.value = "";
    currentEntryId = null;
    startDisplay = "";
    elapsedTime = 0;
    display.textContent = "00:00:00";

    // Remove animation class so controls reset next time
    trackerEl.classList.remove('animate-controls');
  });

  // --- Click Handler for Project List Actions (Delete/Edit) ---
  list.addEventListener("click", async (e) => {
    const wrapper = e.target.closest(".project-wrapper");
    if (!wrapper) return;
    const id = wrapper.dataset.id;
    if (e.target.classList.contains("delete-btn")) {
      await deleteTimeEntry(id);
      wrapper.remove();
      updateEmptyState();
    } else if (e.target.classList.contains("edit-btn")) {
      // TODO: I still need to check the backend to implement this part
    }
  });

  // --- Initialize Page ---
  // Load initial entries, set empty state, and trigger page load animation
  loadEntries();
  updateEmptyState();
  // Trigger page-load animation
  const container = document.querySelector('.time-tracking');
  requestAnimationFrame(() => {
    container.classList.add('page-loaded');
  });
});
