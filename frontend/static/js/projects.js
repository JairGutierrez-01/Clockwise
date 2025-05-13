// static/projects.js

// ============================================================================
//                          API Calls Section
// Defines functions to interact with the backend
// ============================================================================
/* === Comment for taking API calls out ===
// --- API Calls ---
async function fetchProjects() {
  const res = await fetch("/projects");
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

async function createProject(data) {
  const res = await fetch("/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

async function updateProject(id, data) {
  const res = await fetch(`/projects/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to update project");
  return res.json();
}

async function deleteProject(id) {
  const res = await fetch(`/projects/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete project");
}
// === End API block === */

// ============================================================================
// Sets up event listeners, state management, and UI update routines after DOM load.
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
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

  // === Mock Backend Implementation ===
  const mockProjects = [];
  let nextProjectId = 1;

  /**
   * Fetches all projects from the backend.
   *
   * @returns {Promise<Array>} A promise that resolves with an array of project objects.
   */
  async function fetchProjects() {
    // Return a shallow copy to avoid mutation
    return Promise.resolve(mockProjects.map((p) => ({ ...p })));
  }

  /**
   * Creates a new project in the backend.
   *
   * @param {Object} data - The project data including name, description, type, time_limit_hours, and due_date.
   * @returns {Promise<Object>} A promise that resolves with the created project object.
   */
  async function createProject(data) {
    const project = {
      project_id: nextProjectId++,
      name: data.name,
      description: data.description || "",
      type: data.type,
      time_limit_hours: data.time_limit_hours,
      current_hours: 0,
      due_date: data.due_date,
    };
    mockProjects.push(project);
    return Promise.resolve({ ...project });
  }

  /**
   * Updates an existing project by its ID in the backend.
   *
   * @param {number} id - The unique identifier of the project to update.
   * @param {Object} data - The updated project data.
   * @returns {Promise<Object>} A promise that resolves with the updated project object.
   */
  async function updateProject(id, data) {
    const idx = mockProjects.findIndex((p) => p.project_id === id);
    if (idx > -1) {
      mockProjects[idx] = { ...mockProjects[idx], ...data };
      return Promise.resolve({ ...mockProjects[idx] });
    }
    return Promise.reject(new Error("Not found"));
  }

  /**
   * Deletes a project by its unique identifier from the Projects array.
   *
   * @param {number} id - The unique identifier of the project to delete.
   * @returns {Promise<void>} A promise that resolves once the deletion is complete.
   */
  async function deleteProject(id) {
    const idx = mockProjects.findIndex((p) => p.project_id === id);
    if (idx > -1) mockProjects.splice(idx, 1);
    return Promise.resolve();
  }

  let projects = [];
  let editingProjectId = null;

  /**
   * Opens the project form modal.
   *
   * @param {boolean} isEdit - Whether the modal is for editing an existing project.
   */
  function openModal(isEdit = false) {
    form.reset();
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
    modal.classList.remove("hidden");
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
      const card = document.createElement("div");
      card.className = "project-card";
      card.dataset.id = proj.project_id;
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

  // --- Event Listeners ---
  createBtn.addEventListener("click", () => openModal(false));
  cancelBtn.addEventListener("click", closeModal);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      name: nameInput.value.trim(),
      description: descInput.value.trim(),
      type: typeSelect.value,
      time_limit_hours: parseInt(timeLimitInput.value, 10),
      due_date: dueDateInput.value || null,
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
    const id = parseInt(card.dataset.id, 10);
    if (event.target.classList.contains("project-card__view")) {
      showProjectDetail(id);
    }
  });

  editProjBtn.addEventListener("click", () => openModal(true));
  deleteProjBtn.addEventListener("click", async () => {
    if (!editingProjectId) return;
    await deleteProject(editingProjectId);
    detailSection.classList.add("hidden");
    await loadProjects();
  });

  // Placeholder for task creation inside project detail
  createTaskBtn.addEventListener("click", () => {
    // TODO: task creation
    alert("Task creation not implemented yet.");
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
