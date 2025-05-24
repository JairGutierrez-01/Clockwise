// static/projects.js

// Convert Date to match Frontend input with backend expectations*/
function formatDateForBackend(isoDateStr) {
  if (!isoDateStr) return null;
  const [year, month, day] = isoDateStr.split("-");
  return `${day}.${month}.${year}`;
}

function formatDateForInputField(dateString) {
  const date = new Date(dateString);
  return date.toISOString().split("T")[0]; // yyyy-mm-dd
}

// ============================================================================
// Sets up event listeners, state management, and UI update routines after DOM load.
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
  const taskModal = document.getElementById("task-form-modal");
  const taskForm = document.getElementById("task-form");
  const taskNameInput = document.getElementById("task-name");
  const taskDescInput = document.getElementById("task-description");
  const taskTypeSelect = document.getElementById("task-type");
  const taskDueDateInput = document.getElementById("task-due-date");
  const cancelTaskBtn = document.getElementById("cancel-task-btn");
  let projects = [];
  let editingProjectId = null;
  let activeFilter = "all";
  const projectListEl = document.getElementById("project-list");
  const createBtn = document.getElementById("create-project-btn");
  const modal = document.getElementById("project-form-modal");
  const form = document.getElementById("project-form");
  const cancelBtn = document.getElementById("cancel-project-btn");
  const formTitle = document.getElementById("form-title");
  const nameInput = document.getElementById("project-name");
  const descInput = document.getElementById("project-description");
  const typeSelect = document.getElementById("project-type");
  const timeLimitInput = document.getElementById("project-time-limit");
  const dueDateInput = document.getElementById("project-due-date");
  const detailSection = document.getElementById("project-detail");
  const detailName = document.getElementById("detail-name");
  const detailDesc = document.getElementById("detail-description");
  const detailType = document.getElementById("detail-type");
  const detailTimeLimit = document.getElementById("detail-time-limit");
  const detailCurrentHours = document.getElementById("detail-current-hours");
  const detailDueDate = document.getElementById("detail-due-date");
  const editProjBtn = document.getElementById("edit-project-btn");
  const deleteProjBtn = document.getElementById("delete-project-btn");
  const createTaskBtn = document.getElementById("create-task-btn");
  const taskListEl = document.getElementById("task-list");
  const filterBtns = document.querySelectorAll("#filter-controls button");

// ============================================================================
//                          API Calls Section
// Defines functions to interact with the backend
// ============================================================================

//API Calls Projects
async function fetchProjects() {
  const res = await fetch("/api/projects");
  if (!res.ok) throw new Error("Failed to fetch projects");
  const json = await res.json();
  return json.projects;
}

async function createProject(data) {
  const res = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

async function updateProject(id, data) {
  const res = await fetch(`/api/projects/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to update project");
  return res.json();
}

async function deleteProject(id) {
  const res = await fetch(`/api/projects/${id}`, {
    method: "DELETE"
  });
  if (!res.ok) throw new Error("Failed to delete project");
}

//API Calls Tasks
  async function createTask(data) {
  const res = await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to create task");
  return res.json();
}

  /**
   * Opens the project form modal.
   *
   * @param {boolean} isEdit - Whether the modal is for editing an existing project.
   */
  function openModal(isEdit = false) {
    form.reset();
    modal.classList.remove("hidden");
    if (isEdit) {
      formTitle.textContent = "Edit Project";
      const proj = projects.find((p) => p.project_id === editingProjectId);
      nameInput.value = proj.name;
      descInput.value = proj.description || "";
      typeSelect.value = proj.type;
      timeLimitInput.value = proj.time_limit_hours;
      dueDateInput.value = proj.due_date ? proj.due_date.slice(0, 10) : "";
    } else {
      formTitle.textContent = "New Project";
      editingProjectId = null;
    }
  }

  /**
   * Closes the project form modal.
   */
  function closeModal() {
    modal.classList.add("hidden");
  }

  /**
   * Renders the list of project cards in the UI.
   */
  function renderProjectList() {
    projectListEl.innerHTML = "";
    projects.forEach((proj) => {
      if (activeFilter !== "all" && proj.type !== activeFilter) return;

      const card = document.createElement("div");
      card.className = "project-card";
      card.dataset.id = proj.project_id;
      card.dataset.type = proj.type;
      card.innerHTML = `
        <h2 class="project-card__name">${proj.name}</h2>
        <div class="project-card__meta">
    <p>Type: ${proj.type}</p>
    <p>Limit: ${proj.time_limit_hours} h</p>
    <p>Spent: ${proj.current_hours || 0} h</p>
  </div>
        <button class="project-card__view">View</button>
      `;
      projectListEl.appendChild(card);
    });
  }

  /**
   * Displays the details of a selected project.
   *
   * @param {number} id - The unique identifier of the project to display.
   */
  function showProjectDetail(id) {
    const proj = projects.find((p) => p.project_id === id);
    detailName.textContent = proj.name;
    detailDesc.textContent = proj.description || "-";
    detailType.textContent = proj.type;
    detailTimeLimit.textContent = `${proj.time_limit_hours} h`;
    detailCurrentHours.textContent = `${proj.current_hours || 0} h`;
    detailDueDate.textContent = proj.due_date
      ? new Date(proj.due_date).toLocaleDateString()
      : "-";
    detailSection.classList.remove("hidden");
    editingProjectId = id;
  }

  /* ───────────── Filter logic ───────────── */
  function setActiveFilter(filter) {
    activeFilter = filter;
    document
      .querySelector("#filter-controls .active")
      ?.classList.remove("active");
    [...filterBtns]
      .find((b) => b.dataset.filter === filter)
      ?.classList.add("active");
    renderProjectList();
  }
  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => setActiveFilter(btn.dataset.filter));
  });

  /* ───────────── Event listeners Projects ───────────── */
  createBtn.addEventListener("click", () => openModal(false));
  cancelBtn.addEventListener("click", closeModal);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      name: nameInput.value.trim(),
      description: descInput.value.trim(),
      type: typeSelect.value,
      time_limit_hours: parseInt(timeLimitInput.value, 10),
      due_date: formatDateForBackend(dueDateInput.value),
    };

    if (editingProjectId) {
      await updateProject(editingProjectId, payload);
    } else {
      await createProject(payload);
    }

    await loadProjects();
    closeModal();
  });

  projectListEl.addEventListener("click", (event) => {
  const card = event.target.closest(".project-card");
  if (!card) return;

  const viewBtn = event.target.closest(".project-card__view");
  if (viewBtn) {
    const id = parseInt(card.dataset.id, 10);
    showProjectDetail(id);
  }
});

  editProjBtn.addEventListener("click", () => openModal(true));
  deleteProjBtn.addEventListener("click", async () => {
  console.log("Deleting project:", editingProjectId); // Debug
  if (!editingProjectId) return;

  await deleteProject(editingProjectId);
  detailSection.classList.add("hidden");
  await loadProjects();
});

/* ───────────── Event listeners Tasks ───────────── */
createTaskBtn.addEventListener("click", () => {
  taskForm.reset();
  taskModal.classList.remove("hidden");
});

cancelTaskBtn.addEventListener("click", () => {
  taskModal.classList.add("hidden");
});

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const taskPayload = {
    name: taskNameInput.value.trim(),
    description: taskDescInput.value.trim(),
    type: taskTypeSelect.value, // "ActiveTask" | "InactiveTask"
    due_date: taskDueDateInput.value || null,
    project_id: editingProjectId,
  };

  try {
    await createTask(taskPayload);
    console.log("Task gespeichert:", taskPayload);
    taskModal.classList.add("hidden");
    // Optional: Reload or render tasks here
  } catch (error) {
    console.error("Fehler beim Speichern des Tasks:", error);
  }
});



  // --- Initialization ---
  /**
   * Loads projects from the backend and renders them.
   *
   */
  async function loadProjects() {
    projects = await fetchProjects();
    renderProjectList();
    detailSection.classList.add("hidden");
  }

  loadProjects();
});
