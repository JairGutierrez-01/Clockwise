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

async function fetchTasks(projectId) {
  try {
    const response = await fetch(`/api/tasks?project_id=${projectId}`);
    if (!response.ok) {
      throw new Error("Fehler beim Laden der Aufgaben");
    }
    const tasks = await response.json();
    return tasks;
  } catch (error) {
    console.error("fetchTasks Fehler:", error);
    return [];
  }
}

async function fetchTeamTasks(teamId) {
  try {
    const response = await fetch(`/api/teams/${teamId}/tasks`);
    if (!response.ok) throw new Error("Fehler beim Laden der Team-Aufgaben");
    const tasks = await response.json();
    return tasks;
  } catch (err) {
    console.error("fetchTeamTasks Fehler:", err);
    return [];
  }
}

async function loadCategories() {
  try {
    const res = await fetch("/api/categories");
    if (!res.ok) throw new Error("Fehler beim Laden der Kategorien");
    const data = await res.json();

    const datalist = document.getElementById("category-suggestions");
    datalist.innerHTML = "";

    data.categories.forEach((cat) => {
      const option = document.createElement("option");
      option.value = cat.name;
      datalist.appendChild(option);
    });

    window.ALL_CATEGORIES = data.categories;
  } catch (err) {
    console.error("Kategorie-Ladevorgang fehlgeschlagen:", err);
  }
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
  const projectSelect = document.getElementById("task-project");
  const taskStatusSelect = document.getElementById("task-status");
  let projects = [];
  let allTeamsData = [];
  const typeSelect = document.getElementById("project-type");
  const statusSelect = document.getElementById("project-status");

  //when selecting TeamProject
  const teamSelectLabel = document.getElementById("team-select-label");
  const teamSelect = document.getElementById("project-team");

  function populateTeamOptions() {
    const adminTeams = allTeamsData.filter((t) => t.role === "admin");
    teamSelect.innerHTML = '<option value="">Select Team</option>';
    adminTeams.forEach((t) => {
      const opt = document.createElement("option");
      opt.value = t.team_id;
      opt.textContent = t.team_name;
      teamSelect.appendChild(opt);
    });
  }

  function toggleTeamPicker() {
    if (typeSelect.value === "TeamProject") {
      teamSelect.classList.remove("hidden");
      teamSelectLabel.classList.remove("hidden");
      populateTeamOptions();
    } else {
      teamSelect.classList.add("hidden");
      teamSelectLabel.classList.add("hidden");
      teamSelect.value = "";
    }
  }

  typeSelect.addEventListener("change", toggleTeamPicker);
  toggleTeamPicker();
  // Check if user has admin rights for a project
  function userHasProjectAdminRights(project) {
    // damit Admins unabhängig vom Task-Owner Bearbeitungsrechte haben
    if (project.type === "SoloProject") return true;
    if (project.type === "TeamProject" && project.team_id) {
      const team = allTeamsData.find((t) => t.team_id === project.team_id);
      return team && team.role === "admin";
    }
    return false;
  }

  // Load user's teams and roles
  async function loadUserTeams() {
    const res = await fetch("/api/teams");
    if (!res.ok) throw new Error("Failed to fetch teams");
    const data = await res.json();
    allTeamsData = data.teams;
  }
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
  const timeLimitInput = document.getElementById("project-time-limit");
  const dueDateInput = document.getElementById("project-due-date");
  const detailSection = document.getElementById("project-detail");
  const detailName = document.getElementById("detail-name");
  const detailDesc = document.getElementById("detail-description");
  const detailType = document.getElementById("detail-type");
  const detailStatus = document.getElementById("detail-status");
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

  async function loadProjects() {
    try {
      projects = await fetchProjects();
      renderProjectList();
    } catch (err) {
      console.error("Fehler beim Laden der Projekte:", err);
    }
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

  /**
   * Update a task's status.
   */
  async function updateTaskStatus(taskId, status) {
    await fetch(`/api/tasks/${taskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
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
      statusSelect.value = proj.status;
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
    detailSection.classList.add("hidden");
    projectListEl.style.display = "grid";

    if (activeFilter === "alltasks") {
      projectListEl.style.display = "none";
      detailSection.classList.remove("hidden");
      renderAllTasks();
      return;
    }
    if (activeFilter === "unassigned") {
      renderUnassignedTasks();
      return;
    }

    projects.forEach((proj) => {
      if (activeFilter !== "all" && proj.type !== activeFilter) return;

      const card = document.createElement("div");
      card.className = "project-card";
      card.dataset.id = String(proj.project_id);
      card.dataset.type = proj.type;
      card.innerHTML = `
      <h2 class="project-card__name">${proj.name}</h2>
      <div class="project-card__meta">
        <p>Type: ${proj.type}</p>
        <p>Limit: ${proj.time_limit_hours} h</p>
        <p>Spent Time: ${proj.duration_readable || "0h 0min 0s"}</p>
      </div>
      <button class="project-card__view">View</button>
    `;
      projectListEl.appendChild(card);
    });

    // Detail-Panel schließen, wenn außerhalb geklickt wird
    document.addEventListener("click", (event) => {
      const detailPanel = document.getElementById("project-detail");

      // Falls Panel nicht existiert oder nicht sichtbar ist, abbrechen
      if (!detailPanel || detailPanel.classList.contains("hidden")) return;

      const isInsideDetail = detailPanel.contains(event.target);
      const clickedViewButton =
        event.target.classList.contains("project-card__view");

      // Wenn außerhalb geklickt und nicht auf View-Button → Panel schließen
      if (!isInsideDetail && !clickedViewButton) {
        detailPanel.classList.add("hidden");
      }
    });
  }

  async function renderUnassignedTasks() {
    projectListEl.innerHTML = "";
    try {
      const res = await fetch("/api/tasks?unassigned=true");
      if (!res.ok) throw new Error("Failed to fetch unassigned tasks");
      const tasks = await res.json();

      if (tasks.length === 0) {
        projectListEl.innerHTML = "<p>No unassigned tasks found.</p>";
        return;
      }

      tasks.forEach((task) => {
        const card = document.createElement("div");
        card.className = "project-card unassigned-task-card";
        card.innerHTML = `
        <h2 class="project-card__name">${task.title}</h2>
        <div class="project-card__meta">
          <p>Description: ${task.description || "-"}</p>
          <p>Due: ${task.due_date || "N/A"}</p>
        </div>
      `;

        card.addEventListener("click", () => {
          openTaskEditModal(task.task_id);
        });

        projectListEl.appendChild(card);
      });
    } catch (err) {
      console.error("Error loading unassigned tasks:", err);
      projectListEl.innerHTML = "<p>Error loading unassigned tasks.</p>";
    }
  }

  /**
   * Fetch and display all tasks across all projects and unassigned.
   */
  async function renderAllTasks() {
    projectListEl.innerHTML = "";
    projectListEl.style.display = "grid";
    detailSection.classList.add("hidden");

    //Fetch only tasks assigned to current user
    const res = await fetch(`/api/users/${window.CURRENT_USER_ID}/tasks`);
    if (!res.ok) {
      console.error("Failed to fetch user-specific tasks");
      return;
    }

    const allTasks = await res.json();

    allTasks.forEach((task) => {
      const card = document.createElement("div");
      card.className = "project-card";
      card.dataset.id = String(task.task_id);
      card.innerHTML = `
      <h2 class="project-card__name">${task.title}</h2>
      <div class="project-card__meta">
        <p>Project: ${task.project_name || "Unassigned"}</p>
        <p>Due: ${task.due_date || "–"}</p>
        <p>Duration: ${task.total_duration || "0h 0min 0s"}</p>
      </div>
      <button class="project-card__view">View</button>
    `;
      card.addEventListener("click", () => openTaskEditModal(task.task_id));
      projectListEl.appendChild(card);
    });
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
      detailStatus.textContent = proj.status;
      detailTimeLimit.textContent = `${proj.time_limit_hours} h`;
      detailCurrentHours.textContent = proj.duration_readable || "0h 0min 0s";
      detailDueDate.textContent = proj.due_date
        ? new Date(proj.due_date).toLocaleDateString()
        : "-";

      // 3. Detailbereich anzeigen
      detailSection.classList.remove("hidden");
      editingProjectId = id;

      // 3.1. Show/hide admin controls based on user rights
      const isAdmin = userHasProjectAdminRights(proj);
      editProjBtn.style.display = isAdmin ? "inline-block" : "none";
      deleteProjBtn.style.display = isAdmin ? "inline-block" : "none";
      createTaskBtn.style.display = isAdmin ? "inline-block" : "none";

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
      status: statusSelect.value,
      time_limit_hours: parseInt(timeLimitInput.value, 10),
      due_date: formatDateForBackend(dueDateInput.value),
      ...(typeSelect.value === "TeamProject" && teamSelect.value
        ? { team_id: parseInt(teamSelect.value, 10) }
        : {}),
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
    openTaskModal(null, editingProjectId);
  });

  cancelTaskBtn.addEventListener("click", () => {
    taskModal.classList.add("hidden");
    delete taskForm.dataset.editingTaskId;
    document.getElementById("task-form-title").textContent = "New Task";
    projectSelect.disabled = false;
  });

  taskListEl.addEventListener("click", (event) => {
    const li = event.target.closest(".task-item");
    if (!li) return;

    const taskId = parseInt(li.dataset.taskId, 10);
    if (isNaN(taskId)) {
      console.error("Invalid task ID (NaN)", li.dataset);
      return;
    }
    openTaskEditModal(taskId);
  });
  taskForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    // Kategorie-ID bestimmen
    const catInputEl = document.getElementById("task-category");
    let enteredCatName = catInputEl.value.trim();

    enteredCatName = enteredCatName.replace("ß", "ss");

    enteredCatName = enteredCatName.replace(/[^\p{L}\s]/gu, "").trim();

    enteredCatName = enteredCatName
      .split(/\s+/)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");

    let categoryId = null;

    if (enteredCatName) {
      const existing = window.ALL_CATEGORIES?.find(
        (c) => c.name.toLowerCase() === enteredCatName.toLowerCase(),
      );
      if (existing) {
        categoryId = existing.category_id;
      } else {
        try {
          const res = await fetch("/api/categories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: enteredCatName }),
            credentials: "include",
          });
          if (!res.ok) throw new Error("Fehler beim Erstellen der Kategorie");
          const newCat = await res.json();
          categoryId = newCat.category_id;
          await loadCategories(); // neue Kategorie direkt laden
        } catch (err) {
          console.error("Kategorie konnte nicht erstellt werden:", err);
        }
      }
    }

    const taskPayload = {
      title: taskNameInput.value.trim(),
      description: taskDescInput.value.trim(),
      category_id: categoryId, // <-- Jetzt korrekt gesetzt!
      category_name: enteredCatName,
      due_date: taskDueDateInput.value || null,
      status: taskStatusSelect.value,
      project_id: parseInt(projectSelect.value, 10) || null,
      created_from_tracking: false,
    };

    const projectEntryId = taskPayload.project_id;
    if (projectEntryId) {
      const proj = projects.find((p) => p.project_id === projectEntryId);
      if (proj && proj.type === "SoloProject") {
        taskPayload.user_id = window.CURRENT_USER_ID;
      }
    }

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

      if (activeFilter === "unassigned") {
        await renderUnassignedTasks();
      } else if (editingProjectId) {
        const tasks = await fetchTasks(editingProjectId);
        renderTaskList(tasks);
      }
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
      const catInput = document.getElementById("task-category");
      catInput.value = task.category_name || "";
      taskDueDateInput.value = task.due_date || "";
      taskStatusSelect.value = task.status;

      const projectSelect = document.getElementById("task-project");
      projectSelect.innerHTML =
        '<option value="">-- Select Project --</option>';
      projects.forEach((proj) => {
        const option = document.createElement("option");
        option.value = proj.project_id;
        option.textContent = proj.name;
        projectSelect.appendChild(option);
      });
      projectSelect.value = task.project_id || "";

      // Rechte prüfen
      const currentProject = projects.find(
        (p) => p.project_id === task.project_id,
      );
      const isAdmin =
        !task.project_id || userHasProjectAdminRights(currentProject);

      const titleInput = document.getElementById("task-name");
      const descInput = document.getElementById("task-description");
      const deadlineInput = document.getElementById("task-due-date");
      const deleteBtn = document.querySelector(".task-delete-btn");
      const categoryInput = document.getElementById("task-category");

      if (!isAdmin) {
        [
          titleInput,
          descInput,
          deadlineInput,
          categoryInput,
          projectSelect,
        ].forEach((el) => {
          el.disabled = true;
          el.style.opacity = "0.6";
          el.style.cursor = "not-allowed";
        });
        if (deleteBtn) deleteBtn.style.display = "none";
      } else {
        [
          titleInput,
          descInput,
          deadlineInput,
          categoryInput,
          projectSelect,
        ].forEach((el) => {
          el.disabled = false;
          el.style.opacity = "1";
          el.style.cursor = "auto";
        });
        if (deleteBtn) deleteBtn.style.display = "inline-block";
      }

      taskModal.classList.remove("hidden");
      taskForm.dataset.editingTaskId = taskId;
    } catch (error) {
      console.error("Fehler beim Laden der Task:", error);
    }
  }

  function renderTaskList(tasks) {
    taskListEl.innerHTML = "";
    tasks.forEach((task) => {
      const li = document.createElement("li");
      li.className = "task-item";
      li.dataset.taskId = task.task_id;

      const formattedDate = task.due_date
        ? new Date(task.due_date).toLocaleDateString("de-DE")
        : "kein Datum";

      const textSpan = document.createElement("span");
      const durationText = task.total_duration || "0h 0min 0s";

      textSpan.innerHTML = `
        <span class="task-title">${task.title}</span>
        <span class="task-duration">${durationText}</span>
        <span class="task-date">Due: ${formattedDate}</span>
      `;
      textSpan.classList.add("task-meta-row");

      // Delete-Button
      li.appendChild(textSpan);
      // Adminrechte prüfen
      const projectOfTask = projects.find(
        (p) => p.project_id === task.project_id,
      );
      const isAdminOrOwner =
        userHasProjectAdminRights(projectOfTask) ||
        (projectOfTask?.type === "SoloProject" &&
          task.user_id === window.CURRENT_USER_ID);
      if (isAdminOrOwner) {
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
        li.appendChild(deleteBtn);
      }
      taskListEl.appendChild(li);
    });
  }

  function openTaskModal(task = null, defaultProjectId = null) {
    // Reset
    taskForm.reset();
    document.getElementById("task-form-title").textContent = task
      ? "Edit Task"
      : "New Task";

    const projectSelect = document.getElementById("task-project");

    // Projektliste neu befüllen (falls sie dynamisch ist)
    projectSelect.innerHTML = '<option value="">-- Select Project --</option>';
    projects.forEach((proj) => {
      const option = document.createElement("option");
      option.value = proj.project_id;
      option.textContent = proj.name;
      projectSelect.appendChild(option);
    });

    if (task) {
      // Bearbeiten: Werte setzen
      taskNameInput.value = task.title;
      taskDescInput.value = task.description || "";
      taskCategorySelect.value = task.category_id || "";
      taskDueDateInput.value = task.due_date || "";
      projectSelect.value = task.project_id;
      projectSelect.disabled = false;
      taskForm.dataset.editingTaskId = task.task_id;
    } else {
      // Neu: Projekt vorbelegen, Dropdown deaktivieren
      if (defaultProjectId) {
        projectSelect.value = defaultProjectId;
        projectSelect.disabled = true;
      } else {
        projectSelect.disabled = false;
      }
      delete taskForm.dataset.editingTaskId;
    }

    taskModal.classList.remove("hidden");
  }

  (async () => {
    await loadUserTeams();
    await loadProjects();
  })();

  // EXPORT Dropdown-Logik
  const projectExportBtn = document.getElementById("project-download-button");
  const projectDropdown = document.getElementById("project-download-dropdown");

  projectExportBtn.addEventListener("click", () => {
    projectDropdown.classList.toggle("hidden");
  });

  document.addEventListener("click", (e) => {
    if (
      !projectExportBtn.contains(e.target) &&
      !projectDropdown.contains(e.target)
    ) {
      projectDropdown.classList.add("hidden");
    }
  });

  projectDropdown.addEventListener("click", (e) => {
    if (e.target.tagName !== "BUTTON") return;
    const format = e.target.dataset.format;
    if (!format) return;

    const url =
      format === "pdf"
        ? "/api/projects/export/projects/pdf"
        : "/api/projects/export/projects/csv";

    window.open(url, "_blank");
  });
});
