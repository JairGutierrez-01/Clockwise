/**
 * timeTracking.js
 * Front-end logic for ClockWise time tracking page.
 * - Suggests available tasks
 * - Starts, pauses, resumes, and stops timers
 * - Persists sessions in localStorage
 * - Hydrates previous sessions on load
 */
// static/timeTracking.js

// ============================================================================
//                          API CALLS
// Functions to interact with backend endpoints for tasks and time entries
// ============================================================================

/**
 * Fetches tasks that do not have a time entry yet.
 * @async
 * @function fetchTasks
 * @returns {Promise<Array>} Resolves to an array of tasks [{ task_id, title, … }, …]
 * @throws {Error} If the fetch request fails
 */
async function fetchTasks() {
  const res = await fetch("/api/time_entries/available-tasks");
  if (!res.ok) throw new Error("Failed to fetch tasks");
  return res.json(); // [{ task_id, title, … }, …]
}

/**
 * Creates a new task with the given title.
 * @async
 * @function createTaskAPI
 * @param {string} title - The title of the new task
 * @returns {Promise<Object>} Resolves to the created task info { success, message, task_id }
 * @throws {Error} If the fetch request fails
 */
async function createTaskAPI(title) {
  const res = await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, created_from_tracking: true }),
  });
  if (!res.ok) throw new Error("Failed to create task");
  return res.json(); // { success, message, task_id }
}

/**
 * Starts a time entry for the given task ID.
 * @async
 * @function startEntryAPI
 * @param {number} taskId - The ID of the task to start timing
 * @returns {Promise<Object>} Resolves to the started entry info { success, message, time_entry_id }
 * @throws {Error} If the fetch request fails
 */
async function startEntryAPI(taskId) {
  const res = await fetch("/api/time_entries/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_id: taskId }),
  });
  if (!res.ok) throw new Error("Failed to start entry");
  return res.json(); // { success, message, time_entry_id }
}

/**
 * Pauses the time entry with the given entry ID.
 * @async
 * @function pauseEntryAPI
 * @param {number|string} entryId - The ID of the time entry to pause
 * @returns {Promise<Object>} Resolves to the pause response
 * @throws {Error} If the fetch request fails
 */
async function pauseEntryAPI(entryId) {
  const res = await fetch(`/api/time_entries/pause/${entryId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to pause entry");
  return res.json();
}

/**
 * Resumes the time entry with the given entry ID.
 * @async
 * @function resumeEntryAPI
 * @param {number|string} entryId - The ID of the time entry to resume
 * @returns {Promise<Object>} Resolves to the resume response
 * @throws {Error} If the fetch request fails
 */
async function resumeEntryAPI(entryId) {
  const res = await fetch(`/api/time_entries/resume/${entryId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to resume entry");
  return res.json();
}

/**
 * Stops the time entry with the given entry ID.
 * @async
 * @function stopEntryAPI
 * @param {number|string} entryId - The ID of the time entry to stop
 * @returns {Promise<Object>} Resolves to the stop response { success, message, duration_minutes }
 * @throws {Error} If the fetch request fails
 */
async function stopEntryAPI(entryId) {
  const res = await fetch(`/api/time_entries/stop/${entryId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to stop entry");
  return res.json(); // { success, message, duration_minutes }
}

/**
 * Fetches the full time entry data for the given entry ID.
 * @async
 * @function fetchEntryAPI
 * @param {number|string} entryId - The ID of the time entry to fetch
 * @returns {Promise<Object>} Resolves to the full time entry object
 * @throws {Error} If the fetch request fails
 */
async function fetchEntryAPI(entryId) {
  const res = await fetch(`/api/time_entries/${entryId}`);
  if (!res.ok) throw new Error("Failed to fetch entry");
  return res.json(); // the full { time_entry_id, start_time, end_time, duration_minutes, … }
}

/**
 * Fetch tasks that have at least one time entry (latest sessions).
 * @returns {Promise<Array>} Array of tasks
 */
async function fetchLatestSessions() {
  const res = await fetch("/api/time_entries/latest_sessions");
  if (!res.ok) throw new Error("Failed to fetch latest sessions");
  return res.json(); // Array of task objects
}

/**
 * Deletes the time entry with the given entry ID.
 * @async
 * @function deleteEntryAPI
 * @param {number|string} entryId - The ID of the time entry to delete
 * @returns {Promise<Object>} Resolves to the delete response
 * @throws {Error} If the fetch request fails
 */
async function deleteEntryAPI(entryId) {
  const res = await fetch(`/api/time_entries/${entryId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete entry");
  return res.json();
}

// ============================================================================
//                          UTILITIES
// Helper functions for formatting and storage operations
// ============================================================================

/**
 * Formats milliseconds into a HH:MM:SS string.
 * @function formatTime
 * @param {number} ms - Duration in milliseconds
 * @returns {string} Formatted time string in HH:MM:SS
 */
function formatTime(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
}

// --- persistent entry ID storage ---
const ENTRY_IDS_KEY = "clockwise_entry_ids";

/**
 * Loads persisted entry IDs from localStorage.
 * @function loadEntryIds
 * @returns {Array<string|number>} Array of stored entry IDs
 */
function loadEntryIds() {
  try {
    return JSON.parse(localStorage.getItem(ENTRY_IDS_KEY)) || [];
  } catch {
    return [];
  }
}

/**
 * Saves the given array of entry IDs to localStorage.
 * @function saveEntryIds
 * @param {Array<string|number>} ids - Array of entry IDs to save
 */
function saveEntryIds(ids) {
  localStorage.setItem(ENTRY_IDS_KEY, JSON.stringify(ids));
}

/**
 * Adds a new entry ID to persistent storage if not already present.
 * @function addEntryId
 * @param {string|number} id - Entry ID to add
 */
function addEntryId(id) {
  const ids = loadEntryIds();
  if (!ids.includes(id)) {
    ids.push(id);
    saveEntryIds(ids);
  }
}

/**
 * Removes an entry ID from persistent storage.
 * @function removeEntryId
 * @param {string|number} id - Entry ID to remove
 */
function removeEntryId(id) {
  const ids = loadEntryIds().filter((x) => x !== id);
  saveEntryIds(ids);
}

// ============================================================================
//                          MAIN LOGIC
// Sets up event listeners, state variables, and UI rendering on page load
// ============================================================================

/**
 * Initializes the time tracking page on DOMContentLoaded.
 * Hydrates persisted entries, sets up UI and event handlers.
 */
document.addEventListener("DOMContentLoaded", () => {
  // DOM refs
  /** @type {HTMLElement} */
  const trackerEl = document.querySelector(".tracker");
  /** @type {HTMLElement} */
  const display = document.getElementById("tracker-time");
  /** @type {HTMLButtonElement} */
  const startBtn = document.getElementById("tracker-start");
  /** @type {HTMLButtonElement} */
  const pauseBtn = document.getElementById("tracker-pause");
  /** @type {HTMLButtonElement} */
  const resumeBtn = document.getElementById("tracker-resume");
  /** @type {HTMLButtonElement} */
  const stopBtn = document.getElementById("tracker-stop");
  /** @type {HTMLInputElement} */
  const input = document.getElementById("project-name-input");
  /** @type {HTMLElement} */
  const suggList = document.getElementById("task-suggestions");
  /** @type {HTMLElement} */
  const list = document.getElementById("project-list");
  /** @type {HTMLElement} */
  const emptyMessage = document.getElementById("empty-message");
  /** @type {HTMLTemplateElement} */
  const tpl = document.getElementById("entry-template");

  (async () => {
    try {
      const latestSessions = await fetchLatestSessions();
      if (latestSessions.length > 0) {
        emptyMessage.style.display = "none";
        latestSessions.forEach((session) => {
          let formattedDuration = "00:00:00";
          if (session.start_time && session.end_time) {
            const startMs = new Date(session.start_time).getTime();
            const endMs = new Date(session.end_time).getTime();
            formattedDuration = formatTime(endMs - startMs);
          } else if (session.duration_seconds != null) {
            formattedDuration = formatTime(session.duration_seconds * 1000);
          }
          renderEntry({
            time_entry_id: session.time_entry_id,
            task_id: session.task_id,
            name: session.title,
            duration: formattedDuration,
          });
        });
      }
    } catch (err) {
      console.error("Error loading latest sessions:", err);
    }
  })();

  // state
  /** @type {Array<Object>} */
  let allTasks = [];
  /** @type {number|null} */
  let timerInterval = null;
  /** @type {number|null} */
  let startTime = null;
  /** @type {number} */
  let elapsedTime = 0;
  /** @type {number|null} */
  let currentEntryId = null;
  /** @type {string} */
  let startDisplay = "";

  async function startTrackingForTask(taskId, title) {
    // UI vorbereiten
    input.value = title;
    input.dataset.taskId = taskId;
    input.disabled = true;
    startBtn.hidden = true;
    pauseBtn.hidden = false;
    stopBtn.hidden = false;
    resumeBtn.hidden = true;
    trackerEl.classList.add("animate-controls");

    // Timer starten
    startTime = Date.now();
    elapsedTime = 0;
    display.textContent = "00:00:00";
    timerInterval = setInterval(() => {
      elapsedTime = Date.now() - startTime;
      display.textContent = formatTime(elapsedTime);
    }, 1000);

    // Backend start
    const { time_entry_id } = await startEntryAPI(parseInt(taskId));
    currentEntryId = time_entry_id;
    startDisplay = new Date().toLocaleTimeString();
  }

  // load tasks for suggestions
  fetchTasks().then((tasks) => (allTasks = tasks));

  /**
   * Shows or hides the "no sessions" hint based on presence of entries.
   * @function updateEmptyState
   */
  function updateEmptyState() {
    emptyMessage.style.display = list.children.length ? "none" : "block";
  }

  // --- after loadEntries() and updateEmptyState() ---
  const container = document.querySelector(".time-tracking");
  requestAnimationFrame(() => {
    container.classList.add("page-loaded");
  });

  /**
   * Renders a single time entry in the UI.
   * Removes duplicates and stale entries before adding.
   * @function renderEntry
   * @param {Object} e - The entry object with properties including time_entry_id, name, duration
   */
  function renderEntry(e) {
    // remove any existing entry cards for this ID
    const existingCards = list.querySelectorAll(
      `.project-wrapper[data-id="${e.time_entry_id}"]`,
    );
    existingCards.forEach((card) => card.remove());
    // also remove from storage to prevent stale duplicates
    removeEntryId(e.time_entry_id);

    const clone = tpl.content.cloneNode(true);
    const w = clone.querySelector(".project-wrapper");
    w.dataset.id = e.time_entry_id;
    clone.querySelector(".project-name").textContent = e.name;
    // Removed time-range population
    clone.querySelector(".duration").textContent = e.duration;
    const resumeBtn = clone.querySelector(".resume-btn");
    const deleteBtn = clone.querySelector(".delete-btn");
    if (resumeBtn) resumeBtn.remove();
    if (deleteBtn) deleteBtn.remove();

    // Setze Edit-Button
    const editBtn = clone.querySelector(".edit-btn");
    if (editBtn) {
      editBtn.setAttribute("data-task-id", e.task_id);
    }

    // Füge neuen Track-Button hinzu
    const trackBtn = document.createElement("button");
    trackBtn.textContent = "Track";
    trackBtn.className = "track-btn";
    trackBtn.addEventListener("click", async () => {
      // Beende ggf. vorherige Sessions (Timer stoppen und ID löschen)
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }

      currentEntryId = null;
      elapsedTime = 0;
      display.textContent = "00:00:00";

      await startTrackingForTask(e.task_id, e.name);
    });

    clone.querySelector(".project").appendChild(trackBtn);

    list.appendChild(clone);
    w.classList.add("new-entry");
    w.addEventListener("animationend", () => w.classList.remove("new-entry"));
    updateEmptyState();
  }

  /**
   * Filters and shows task suggestions based on input.
   * @listens input#project-name-input input
   */
  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    suggList.innerHTML = "";
    if (!q) return;
    allTasks
      .filter((t) => t.title.toLowerCase().includes(q))
      .forEach((t) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <span class="suggestion-task">${t.title}</span>
          <span class="suggestion-project">(${t.project_name})</span>
        `;
        li.dataset.taskId = t.task_id;
        suggList.appendChild(li);
      });
  });

  /**
   * Handles click on a task suggestion to fill input.
   * @listens ul#task-suggestions click
   * @param {MouseEvent} e - Click event
   */
  suggList.addEventListener("click", (e) => {
    const li = e.target.closest("li");
    if (!li) return;
    input.value = li.querySelector(".suggestion-task").textContent;
    input.dataset.taskId = li.dataset.taskId;
    suggList.innerHTML = "";
  });

  /**
   * Starts the timer and backend time entry for the selected or new task.
   * @listens button#tracker-start click
   * @async
   */
  startBtn.addEventListener("click", async () => {
    let taskId = input.dataset.taskId;
    const title = input.value.trim();

    if (!taskId && title) {
      const { task_id } = await createTaskAPI(title);
      taskId = task_id;
    }

    if (!taskId && !title) {
      taskId = null;
    }

    await startTrackingForTask(taskId, title);
  });

  /**
   * Pauses the current timer and backend time entry.
   * @listens button#tracker-pause click
   * @async
   */
  pauseBtn.addEventListener("click", async () => {
    clearInterval(timerInterval);
    timerInterval = null;
    await pauseEntryAPI(currentEntryId);
    pauseBtn.hidden = true;
    resumeBtn.hidden = false;
  });

  /**
   * Resumes the paused timer and backend time entry.
   * @listens button#tracker-resume click
   * @async
   */
  resumeBtn.addEventListener("click", async () => {
    await resumeEntryAPI(currentEntryId);
    startTime = Date.now() - elapsedTime;
    timerInterval = setInterval(() => {
      elapsedTime = Date.now() - startTime;
      display.textContent = formatTime(elapsedTime);
    }, 1000);
    resumeBtn.hidden = true;
    pauseBtn.hidden = false;
  });

  /**
   * Stops the timer and backend time entry, fetches full entry data,
   * renders the entry, and resets UI.
   * @listens button#tracker-stop click
   * @async
   */
  stopBtn.addEventListener("click", async () => {
    clearInterval(timerInterval);
    timerInterval = null;

    if (!currentEntryId) {
      console.warn("No currentEntryId – stopping without entry");
      return;
    }

    try {
      await stopEntryAPI(currentEntryId);
      const e = await fetchEntryAPI(currentEntryId);
      const task = await fetch(`/api/tasks/${e.task_id}`).then((r) => r.json());

      e.name = task.title;
      e.start_time = startDisplay;
      e.end_time = new Date(e.end_time).toLocaleTimeString();
      e.duration = formatTime(elapsedTime);

      renderEntry(e);
      addEntryId(currentEntryId);
    } catch (err) {
      console.error("Failed to stop or fetch entry:", err);
    }

    // Reset UI
    trackerEl.classList.remove("animate-controls");
    stopBtn.hidden = true;
    pauseBtn.hidden = true;
    resumeBtn.hidden = true;
    startBtn.hidden = false;
    input.disabled = false;
    input.value = "";
    delete input.dataset.taskId;
    currentEntryId = null;
    elapsedTime = 0;
    display.textContent = "00:00:00";
  });

  /**
   * Handles click events on the project list for delete, resume, and edit actions.
   * @listens #project-list click
   * @param {MouseEvent} e - Click event
   * @async
   */
  list.addEventListener("click", async (e) => {
    const w = e.target.closest(".project-wrapper");
    if (!w) return;
    const id = w.dataset.id;

    if (e.target.classList.contains("delete-btn")) {
      await deleteEntryAPI(id);
      w.remove();
      removeEntryId(id);
      updateEmptyState();
    } else if (e.target.classList.contains("resume-btn")) {
      // NEW: resume an existing session
      const entryId = w.dataset.id;
      const entry = await fetchEntryAPI(entryId);
      // fetch task title
      const task = await fetch(`/api/tasks/${entry.task_id}`).then((r) =>
        r.json(),
      );
      const title = task.title;
      // remove from UI and storage
      w.remove();
      removeEntryId(entryId);
      updateEmptyState();
      // prepare tracker
      input.value = title;
      input.dataset.taskId = entry.task_id;
      input.disabled = true;
      startBtn.hidden = true;
      pauseBtn.hidden = false;
      resumeBtn.hidden = true;
      stopBtn.hidden = false;
      // resume timing
      elapsedTime = (entry.duration_minutes || 0) * 60 * 1000;
      display.textContent = formatTime(elapsedTime);
      startTime = Date.now() - elapsedTime;
      timerInterval = setInterval(() => {
        elapsedTime = Date.now() - startTime;
        display.textContent = formatTime(elapsedTime);
      }, 1000);
      currentEntryId = entryId;
    } else if (e.target.classList.contains("edit-btn")) {
      const taskId = e.target.dataset.taskId;
      if (taskId) {
        window.location.href = `/time_entries?id=${taskId}`;
      } else {
        console.log("Task-ID nicht gefunden!");
      }
    }
  });

  // done
  updateEmptyState();
});
