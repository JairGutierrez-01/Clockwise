//                          API CALLS

/**
 * Deletes the time entry with the given entry ID.
 * @async
 * @function deleteEntryAPI
 * @param {number|string} entryId - The ID of the time entry to delete
 * @returns {Promise<Object>} Resolves to the delete response
 * @throws {Error} If the fetch request fails
 */
async function deleteEntryAPI(entryId) {
  const res = await fetch(`/api/time_entries/${entryId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete entry");
  return res.json();
}

/**
 * Updates the time entry with the given entry ID.
 * @async
 * @function updateEntryAPI
 * @param {number|string} entryId - The ID of the time entry to update
 * @param {Object} data - Object containing fields to update:
 *   - start_time: "YYYY-MM-DDTHH:MM"
 *   - end_time: "YYYY-MM-DDTHH:MM"
 *   - duration_seconds: number
 * @returns {Promise<Object>} Resolves to the update response
 * @throws {Error} If the fetch request fails
 */
async function updateEntryAPI(entryId, data) {
  const res = await fetch(`/api/time_entries/${entryId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update entry");
  return res.json();
}

/**
 * Fetches a single time entry by its ID.
 * @async
 * @function fetchEntryAPI
 * @param {number|string} entryId - The ID of the time entry to fetch
 * @returns {Promise<Object>} Resolves to the full time entry object
 * @throws {Error} If the fetch request fails
 */
async function fetchEntryAPI(entryId) {
  const res = await fetch(`/api/time_entries/${entryId}`);
  if (!res.ok) throw new Error("Failed to fetch entry");
  return res.json();
}

//                          UTILITIES
/**
 * Formats a duration in seconds into "HH:MM:SS".
 * @function formatDuration
 * @param {number} totalSeconds - Duration in seconds
 * @returns {string} Formatted time string in HH:MM:SS
 */
function formatDuration(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
}

/**
 * Converts a Date object into a "YYYY-MM-DDTHH:MM" string
 * suitable for a <input type="datetime-local">.
 * @function toInputDateTime
 * @param {Date} dateObj
 * @returns {string} "YYYY-MM-DDTHH:MM"
 */
function toInputDateTime(dateObj) {
  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, "0");
  const day = String(dateObj.getDate()).padStart(2, "0");
  const hours = String(dateObj.getHours()).padStart(2, "0");
  const mins = String(dateObj.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${mins}`;
}

/**
 * Parses a "YYYY-MM-DDTHH:MM" string from an <input type="datetime-local">
 * into a Date object.
 * @function parseInputDateTime
 * @param {string} inputVal - "YYYY-MM-DDTHH:MM"
 * @returns {Date}
 */
function parseInputDateTime(inputVal) {
  return new Date(inputVal);
}

//                          MAIN LOGIC
document.addEventListener("DOMContentLoaded", () => {
  // DOM references
  const table = document.getElementById("entries-table");
  const editModal = document.getElementById("edit-modal");
  const editForm = document.getElementById("edit-form");
  const startInput = document.getElementById("edit-start-time");
  const endInput = document.getElementById("edit-end-time");
  const durationDiv = document.getElementById("edit-duration");
  const saveBtn = document.getElementById("save-edit-btn");
  const cancelBtn = document.getElementById("cancel-edit-btn");

  let currentEditId = null;

  /**
   * Closes the edit modal and clears state.
   * @function closeEditModal
   */
  function closeEditModal() {
    editModal.classList.add("hidden");
    currentEditId = null;
    startInput.value = "";
    endInput.value = "";
    durationDiv.textContent = "00:00:00";
  }

  /**
   * Opens the edit modal, fetches the entry data, and populates the form.
   * @async
   * @function openEditModal
   * @param {number|string} entryId
   */
  async function openEditModal(entryId) {
    try {
      const entry = await fetchEntryAPI(entryId);
      currentEditId = entryId;

      const startDate = new Date(entry.start_time);
      const endDate = new Date(entry.end_time);

      startInput.value = toInputDateTime(startDate);
      endInput.value = toInputDateTime(endDate);

      const diffSeconds = Math.floor((endDate - startDate) / 1000);
      durationDiv.textContent = formatDuration(diffSeconds);

      editModal.classList.remove("hidden");
    } catch (err) {
      console.error("Failed to load entry for editing:", err);
    }
  }

  /**
   * Attaches table-level click handlers for delete/edit buttons.
   * @listens #entries-table click
   * @param {MouseEvent} e
   * @async
   */
  table.addEventListener("click", async (e) => {
    const row = e.target.closest("tr[data-entry-id]");
    if (!row) return;
    const entryId = row.dataset.entryId;

    if (e.target.classList.contains("delete-btn")) {
      try {
        await deleteEntryAPI(entryId);
        row.remove();
      } catch (err) {
        console.error("Error deleting entry:", err);
      }
    } else if (e.target.classList.contains("edit-btn")) {
      await openEditModal(entryId);
    }
  });

  /**
   * Recalculates and displays duration when start or end inputs change.
   * @listens #edit-start-time and #edit-end-time input
   */
  function recalcDuration() {
    if (!startInput.value || !endInput.value) {
      durationDiv.textContent = "00:00:00";
      return;
    }
    const startDate = parseInputDateTime(startInput.value);
    const endDate = parseInputDateTime(endInput.value);
    const diffMs = endDate - startDate;
    const diffSec = diffMs > 0 ? Math.floor(diffMs / 1000) : 0;
    durationDiv.textContent = formatDuration(diffSec);
  }

  startInput.addEventListener("input", recalcDuration);
  endInput.addEventListener("input", recalcDuration);

  /**
   * Handles "Cancel" button in edit modal.
   * @listens #cancel-edit-btn click
   */
  cancelBtn.addEventListener("click", () => {
    closeEditModal();
  });

  /**
   * Handles form submission: sends updated data to the API,
   * updates the table row on success, and closes the modal.
   * @listens #edit-form submit
   * @param {SubmitEvent} e
   * @async
   */
  editForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentEditId) return;

    const startDate = parseInputDateTime(startInput.value);
    const endDate = parseInputDateTime(endInput.value);
    const durationSeconds = Math.floor((endDate - startDate) / 1000);

    const payload = {
      start_time: startInput.value.replace("T", " "),
      end_time: endInput.value.replace("T", " "),
      duration_seconds: durationSeconds,
    };

    try {
      await updateEntryAPI(currentEditId, payload);

      const row = document.querySelector(
        `tr[data-entry-id="${currentEditId}"]`,
      );
      if (row) {
        const yyyy = startDate.getFullYear();
        const mm = String(startDate.getMonth() + 1).padStart(2, "0");
        const dd = String(startDate.getDate()).padStart(2, "0");
        row.querySelector(".entry-date").textContent = `${yyyy}-${mm}-${dd}`;

        const sh = String(startDate.getHours()).padStart(2, "0");
        const sm = String(startDate.getMinutes()).padStart(2, "0");
        row.querySelector(".entry-start").textContent = `${sh}:${sm}`;

        const eh = String(endDate.getHours()).padStart(2, "0");
        const em = String(endDate.getMinutes()).padStart(2, "0");
        row.querySelector(".entry-end").textContent = `${eh}:${em}`;

        const hours = Math.floor(durationSeconds / 3600);
        const minutes = Math.floor((durationSeconds % 3600) / 60);
        const seconds = durationSeconds % 60;
        row.querySelector(".entry-duration").textContent =
          `${hours}h ${minutes}m ${seconds}s`;
      }
      closeEditModal();
    } catch (err) {
      console.error("Error updating entry:", err);
    }
  });

  closeEditModal();
});
/**
 * time_entries.js
 * Front-end logic for the Time Entries page of ClockWise.
 * - Deletes time entries
 * - Edits start/end times (including seconds) and recalculates duration
 * - Persists updates via API
 */

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("entries-table");
  if (!table) return;

  const editModal = document.getElementById("edit-modal");
  const editForm = document.getElementById("edit-form");
  const startInput = document.getElementById("edit-start-time");
  const endInput = document.getElementById("edit-end-time");
  const durationDiv = document.getElementById("edit-duration");
  const cancelBtn = document.getElementById("cancel-edit-btn");

  /** @type {string|null} */
  let currentEditId = null;

  // API CALLS

  async function deleteEntryAPI(entryId) {
    const res = await fetch(`/api/time_entries/${entryId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete entry");
    return res.json();
  }

  async function fetchEntryAPI(entryId) {
    const res = await fetch(`/api/time_entries/${entryId}`);
    if (!res.ok) throw new Error("Failed to fetch entry");
    return res.json();
  }

  async function updateEntryAPI(entryId, data) {
    const res = await fetch(`/api/time_entries/${entryId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update entry");
    return res.json();
  }

  /**
   * Formats a duration in seconds into "HH:MM:SS".
   */
  function formatDuration(totalSeconds) {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
  }

  /**
   * Converts a Date object into a "YYYY-MM-DDTHH:MM:SS" string
   * suitable for a <input type="datetime-local" step="1">.
   */
  function toInputDateTime(dateObj) {
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, "0");
    const day = String(dateObj.getDate()).padStart(2, "0");
    const hours = String(dateObj.getHours()).padStart(2, "0");
    const mins = String(dateObj.getMinutes()).padStart(2, "0");
    const secs = String(dateObj.getSeconds()).padStart(2, "0");
    return `${year}-${month}-${day}T${hours}:${mins}:${secs}`;
  }

  /**
   * Parses a "YYYY-MM-DDTHH:MM:SS" string from an <input type="datetime-local" step="1">
   * into a Date object.
   */
  function parseInputDateTime(inputVal) {
    return new Date(inputVal);
  }

  function closeEditModal() {
    editModal.classList.add("hidden");
    currentEditId = null;
    startInput.value = "";
    endInput.value = "";
    durationDiv.textContent = "00:00:00";
  }

  async function openEditModal(entryId) {
    try {
      const entry = await fetchEntryAPI(entryId);
      currentEditId = entryId;

      const startDate = new Date(entry.start_time);
      const endDate = new Date(entry.end_time);

      startInput.value = toInputDateTime(startDate);
      endInput.value = toInputDateTime(endDate);

      const diffSeconds = Math.floor((endDate - startDate) / 1000);
      durationDiv.textContent = formatDuration(diffSeconds);

      editModal.classList.remove("hidden");
    } catch (err) {
      console.error("Failed to load entry for editing:", err);
    }
  }

  table.addEventListener("click", async (e) => {
    const row = e.target.closest("tr[data-entry-id]");
    if (!row) return;
    const entryId = row.dataset.entryId;
    if (!entryId) return;

    if (e.target.classList.contains("delete-btn")) {
      try {
        await deleteEntryAPI(entryId);
        row.remove();
      } catch (err) {
        console.error("Error deleting entry:", err);
      }
    } else if (e.target.classList.contains("edit-btn")) {
      await openEditModal(entryId);
    }
  });

  function recalcDuration() {
    if (!startInput.value || !endInput.value) {
      durationDiv.textContent = "00:00:00";
      return;
    }
    const startDate = parseInputDateTime(startInput.value);
    const endDate = parseInputDateTime(endInput.value);
    const diffMs = endDate - startDate;
    const diffSec = diffMs > 0 ? Math.floor(diffMs / 1000) : 0;
    durationDiv.textContent = formatDuration(diffSec);
  }

  startInput.addEventListener("input", recalcDuration);
  endInput.addEventListener("input", recalcDuration);

  cancelBtn.addEventListener("click", () => {
    closeEditModal();
  });

  editForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentEditId) return;

    const startDate = parseInputDateTime(startInput.value);
    const endDate = parseInputDateTime(endInput.value);
    const durationSeconds = Math.floor((endDate - startDate) / 1000);

    const payload = {
      start_time: startInput.value.replace("T", " "),
      end_time: endInput.value.replace("T", " "),
      duration_seconds: durationSeconds,
    };

    try {
      await updateEntryAPI(currentEditId, payload);

      const row = document.querySelector(
        `tr[data-entry-id="${currentEditId}"]`,
      );
      if (row) {
        const yyyy = startDate.getFullYear();
        const mm = String(startDate.getMonth() + 1).padStart(2, "0");
        const dd = String(startDate.getDate()).padStart(2, "0");
        row.querySelector(".entry-date").textContent = `${yyyy}-${mm}-${dd}`;

        const sh = String(startDate.getHours()).padStart(2, "0");
        const sm = String(startDate.getMinutes()).padStart(2, "0");
        const ss = String(startDate.getSeconds()).padStart(2, "0");
        row.querySelector(".entry-start").textContent = `${sh}:${sm}:${ss}`;

        const eh = String(endDate.getHours()).padStart(2, "0");
        const em = String(endDate.getMinutes()).padStart(2, "0");
        const es = String(endDate.getSeconds()).padStart(2, "0");
        row.querySelector(".entry-end").textContent = `${eh}:${em}:${es}`;

        const hours = Math.floor(durationSeconds / 3600);
        const minutes = Math.floor((durationSeconds % 3600) / 60);
        const seconds = durationSeconds % 60;
        row.querySelector(".entry-duration").textContent =
          `${hours}h ${minutes}m ${seconds}s`;
      }

      closeEditModal();
    } catch (err) {
      console.error("Error updating entry:", err);
    }
  });

  closeEditModal();
});
