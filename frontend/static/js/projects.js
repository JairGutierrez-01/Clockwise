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
  const taskCategorySelect = document.getElementById("task-category");
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
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create project");
    return res.json();
  }

  async function updateProject(id, data) {
    const res = await fetch(`/api/projects/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update project");
    return res.json();
  }

  async function deleteProject(id) {
    const res = await fetch(`/api/projects/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete project");
  }

  //API Calls Tasks
  async function createTask(data) {
    const res = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
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
 async function fetchTasks(projectId) {
    const res = await fetch(`/api/tasks?project_id=${projectId}`);
    if (!res.ok) throw new Error("Fehler beim Laden der Tasks");
    return res.json();
  }
  /**
   * Displays the details of a selected project.
   *
   * @param {number} id - The unique identifier of the project to display.
   */
  async function showProjectDetail(id) {
  try {
    // 1. Projekt aus local state holen
    const proj = projects.find((p) => p.project_id === id);
    if (!proj) {
      console.error("Projekt nicht gefunden für ID:", id);
      return;
    }

    // 2. Projektdetails ins UI einfügen
    detailName.textContent = proj.name;
    detailDesc.textContent = proj.description || "-";
    detailType.textContent = proj.type;
    detailTimeLimit.textContent = `${proj.time_limit_hours} h`;
    detailCurrentHours.textContent = `${proj.current_hours || 0} h`;
    detailDueDate.textContent = proj.due_date
      ? new Date(proj.due_date).toLocaleDateString()
      : "-";

    // 3. Detailbereich anzeigen
    detailSection.classList.remove("hidden");
    editingProjectId = id;

    // 4. Tasks vom Backend laden
    const tasks = await fetchTasks(id);

    // 5. UI aktualisieren
    renderTaskList(tasks);
  } catch (error) {
    console.error("Fehler beim Laden der Projektdetails:", error);
  }
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
  delete taskForm.dataset.editingTaskId;
  document.getElementById("task-form-title").textContent = "New Task";
});

  taskListEl.addEventListener("click", (event) => {
  const li = event.target.closest(".task-item");
  if (!li) return;

  const taskId = parseInt(li.dataset.id, 10);
  openTaskEditModal(taskId);
});

  taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const taskPayload = {
    title: taskNameInput.value.trim(),
    description: taskDescInput.value.trim(),
    category_id: parseInt(taskCategorySelect.value, 10) || null,
    due_date: taskDueDateInput.value || null,
    project_id: editingProjectId,
    created_from_tracking: false,
  };

  const editingTaskId = taskForm.dataset.editingTaskId;

  try {
    if (editingTaskId) {
      await fetch(`/api/tasks/${editingTaskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(taskPayload),
      });
      delete taskForm.dataset.editingTaskId;
    } else {
      await createTask(taskPayload);
    }

    taskModal.classList.add("hidden");
    const tasks = await fetchTasks(editingProjectId);
    renderTaskList(tasks);
  } catch (error) {
    console.error("Fehler beim Speichern der Task:", error);
  }
});

  // --- Initialization ---
  /**
   * Loads projects from the backend and renders them.
   *
   */
  async function openTaskEditModal(taskId) {
  try {
    const res = await fetch(`/api/tasks/${taskId}`);
    if (!res.ok) throw new Error("Task konnte nicht geladen werden");

    const task = await res.json();
    document.getElementById("task-form-title").textContent = "Edit Task";
    taskNameInput.value = task.title;
    taskDescInput.value = task.description || "";
    taskCategorySelect.value = task.category_id || "";
    taskDueDateInput.value = task.due_date || "";

    taskModal.classList.remove("hidden");

    // Vorübergehend Task-ID speichern
    taskForm.dataset.editingTaskId = taskId;

  } catch (error) {
    console.error("Fehler beim Laden der Task:", error);
  }
}

  async function loadProjects() {
    projects = await fetchProjects();
    renderProjectList();
    detailSection.classList.add("hidden");

    // Richtig: Nach dem Laden & Rendern prüfen, ob URL eine project_id enthält
    const urlParams = new URLSearchParams(window.location.search);
    const selectedId = parseInt(urlParams.get("project_id"), 10);
    if (selectedId) {
      showProjectDetail(selectedId);
    }
  }

  function renderTaskList(tasks) {
  taskListEl.innerHTML = "";
  tasks.forEach((task) => {
    const li = document.createElement("li");
    li.className = "task-item";

    const formattedDate = task.due_date
      ? new Date(task.due_date).toLocaleDateString("de-DE")
      : "kein Datum";

    // Linker Textteil (Taskname + Datum)
    const textSpan = document.createElement("span");
    textSpan.textContent = `${task.title} – Due Date: ${formattedDate}`;

    // Delete-Button
    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "Delete";
    deleteBtn.className = "task-delete-btn";
    deleteBtn.addEventListener("click", async () => {
      if (!confirm("Möchtest du diese Aufgabe wirklich löschen?")) return;

      try {
        const res = await fetch(`/api/tasks/${task.task_id}`, {
          method: "DELETE",
        });
        if (!res.ok) throw new Error("Löschen fehlgeschlagen");
        const updatedTasks = await fetchTasks(editingProjectId);
        renderTaskList(updatedTasks);
      } catch (err) {
        console.error("Fehler beim Löschen:", err);
      }
    });

    // Zusammenfügen
    li.appendChild(textSpan);
    li.appendChild(deleteBtn);
    taskListEl.appendChild(li);
  });
}
  loadProjects();
});
