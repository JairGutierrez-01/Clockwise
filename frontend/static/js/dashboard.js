import { getTaskColor } from "./color_utils.js";

/**
 * Initialisiert die Projektübersicht in der Dashboard-Tabelle.
 * Lädt alle Projekte des aktuellen Nutzers asynchron über die API (/api/projects)
 * und rendert sie als einfache Liste mit Name und bereits investierter Zeit.
 */
document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("dashboard-project-list");
  if (!container) return;

  try {
    const res = await fetch("/api/projects");
    const json = await res.json();
    const projects = json.projects || [];

    container.innerHTML = "";

    projects.forEach((proj) => {
      const card = document.createElement("div");
      card.className = "project-dashboard-card";
      card.innerHTML = `
        <div class="project-name">${proj.name}</div>
        <div class="project-time">${proj.duration_readable || "0h 0min 0s"}</div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error occured while loading projects:", err);
    container.innerHTML = "<p>Error loading projects.</p>";
  }
});

/**
 * Aktiviert die Klick-Weiterleitung auf die Projektübersicht innerhalb der Dashboard-Kachel.
 * Leitet zur Seite /projects weiter, wenn der Benutzer innerhalb der Projects-Kachel (außerhalb der Scrollbar) klickt.
 */
document.addEventListener("DOMContentLoaded", () => {
  const projectsCard = document.querySelector(".projects-table");

  if (!projectsCard) return;

  projectsCard.addEventListener("click", function (e) {
    const bounding = this.getBoundingClientRect();
    const scrollbarThreshold = 20; // Reservebereich für Scrollbar

    // Prüfe, ob der Klick weit genug links von der Scrollbar war
    if (e.clientX < bounding.right - scrollbarThreshold) {
      window.location.href = "/projects";
    }
  });
});

/**
 * Initialisiert den Mini-Kalender auf der Dashboard-Seite.
 * Lädt Due Dates (rote Balken) und Time Entries (blaue Balken) (max. 1 pro Tag für Übersichtlichkeit) asynchron
 * und rendert diese im eingebetteten Monatskalender.
 */
document.addEventListener("DOMContentLoaded", async function () {
  const calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  try {
    // Lade Due Dates und Time Entries parallel
    const [dueRes, workedRes] = await Promise.all([
      fetch("/calendar-due-dates").then((res) => res.json()),
      fetch("/calendar-worked-time").then((res) => res.json()),
    ]);

    const events = [];

    // Falls Due Date vorhanden → roten Balken setzen
    dueRes.forEach((entry) => {
      if (!entry.start) return;
      events.push({
        title: "",
        start: entry.start,
        allDay: true,
        className: "bg-red",
      });
    });

    // Falls Time Entry vorhanden → blauen Balken setzen
    workedRes.forEach((entry) => {
      if (!entry.start) return;
      events.push({
        title: "",
        start: entry.start,
        allDay: true,
        className: "bg-blue",
      });
    });

    // Kalender initialisieren
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "dayGridMonth",
      height: 300,
      headerToolbar: {
        start: "title",
        center: "",
        end: "",
      },
      navLinks: false,
      editable: false,
      fixedWeekCount: false,
      showNonCurrentDates: false,
      events: events,
    });

    calendar.render();
  } catch (err) {
    console.error("Error occured while initializing calendar:", err);
  }
});

/**
 * Aktiviert die Klick-Weiterleitung auf die Kalenderansicht innerhalb der Dashboard-Kachel.
 * Leitet zur Analysis-Seite mit aktivierter Kalender-Ansicht weiter.
 */
document.addEventListener("DOMContentLoaded", function () {
  const calendarCard = document.querySelector(".calendar");

  if (calendarCard) {
    calendarCard.style.cursor = "pointer";

    // Weiterleitung zur Kalenderansicht auf der Analysis-Seite
    calendarCard.addEventListener("click", function () {
      window.location.href = "/analysis?view=calendar";
    });
  }
});

/**
 * Ensures the presence of the team activity box in the dashboard.
 * If it doesn't exist, it creates and appends one dynamically.
 * @returns {HTMLElement|null}
 * Returns:
 *   - The DOM element for the team box (new or existing)
 *   - null if no valid parent container is found
 */
function ensureTeamBoxExists() {
  let teamBox = document.getElementById("team-activity-box");

  if (!teamBox) {
    // Look for the main dashboard container to attach the box
    const targetParent =
      document.querySelector(".dashboard-grid") ||
      document.querySelector("#dashboard");
    if (!targetParent) return null; // No valid container found

    // Create the container box dynamically
    teamBox = document.createElement("div");
    teamBox.className = "card project-details";
    teamBox.id = "team-activity-box";
    teamBox.innerHTML = `
      <h3 id="team-project-name">...</h3>
      <p>Total Time: <span id="total-time">--:--:--</span></p>
      <p>Team Members:</p>
      <div id="team-member-list" class="team-members"></div>
      <div id="team-progress" class="progress-chart"></div>
    `;
    targetParent.appendChild(teamBox);

    // Allow redirect to analysis view when the box is clicked,
    // but ignore inner elements like charts or spans
    teamBox.style.cursor = "pointer";
    teamBox.addEventListener("click", function (event) {
      const ignoredElements = ["SPAN", "SVG", "CIRCLE", "TEXT"];
      if (ignoredElements.includes(event.target.tagName)) return;

      window.location.href = "/analysis?view=progress";
    });
  }

  return teamBox;
}

/**
 * Calculates the completion percentage of a project based on task statuses.
 *
 * Params:
 *   - projectId: ID of the project whose progress is being calculated
 *
 * Returns:
 *   - Number between 0 and 100 representing the percentage of completed tasks
 *   - Returns 0 if the project has no tasks or an error occurs
 */
/**
 * Berechnet den Fortschritt eines Projekts anhand erledigter Aufgaben.
 * @param {number} projectId - ID des Projekts
 * @returns {Promise<number>} - Fortschritt in Prozent (0–100)
 */
async function calculateProjectProgress(projectId) {
  try {
    const tasks = await fetchTasksByProjectId(projectId);
    const totalTasks = tasks.length;
    const doneTasks = tasks.filter((t) => t.status === "done").length;

    // Avoid division by zero and return percentage
    return totalTasks > 0 ? (doneTasks / totalTasks) * 100 : 0;
  } catch (error) {
    console.error(
      `Error calculating progress for project ${projectId}:`,
      error,
    );

    // On error, treat progress as 0%
    return 0;
  }
}

/**
 * Finds the project with the highest progress value from a list of unified projects.
 *
 * Params:
 *   - unifiedProjects: Array of objects containing `project` keys (e.g. { project, team })
 *
 * Returns:
 *   - The project object with the highest calculatedProgress value
 *   - Returns null if the list is empty
 *
 * Note:
 *   - Each project's progress is calculated via `calculateProjectProgress`
 *   - Adds a `calculatedProgress` field to the returned project for downstream use
 */
async function findMostAdvancedProjectUnified(unifiedProjects) {
  let mostAdvancedProject = null;
  let maxProgress = -1;

  for (const entry of unifiedProjects) {
    const { project } = entry;
    const currentProgress = await calculateProjectProgress(project.project_id);

    if (currentProgress > maxProgress) {
      maxProgress = currentProgress;
      mostAdvancedProject = { ...project, calculatedProgress: currentProgress };
    }
  }

  return mostAdvancedProject;
}

/**
 * Loads and renders the Team Activity Box on the dashboard.
 * Merges team and solo projects into a unified list, selects the most advanced project,
 * and displays its progress, duration, and assigned members in the UI.
 */
async function loadTeamActivityBox() {
  const teamBox = ensureTeamBoxExists();
  if (!teamBox) return; // Exit if container is missing

  try {
    // Fetch full team data including associated projects and members
    const res = await fetch("/api/teams/full");
    const data = await res.json();

    // Fetch all projects including solo (non-team) projects
    const projectsRes = await fetch("/api/projects", {
      method: "GET",
      credentials: "include",
    });
    const projectsData = await projectsRes.json();

    // Build unifiedProjects array containing both team and solo projects
    const unifiedProjects = [];

    // Team projects (with team context and members)
    for (const team of data) {
      if (team.projects && Array.isArray(team.projects)) {
        for (const project of team.projects) {
          unifiedProjects.push({
            project: project,
            members: team.members,
            isSolo: false,
          });
        }
      }
    }

    // Solo projects (team_id === null)
    const soloProjects =
      projectsData.projects && Array.isArray(projectsData.projects)
        ? projectsData.projects.filter((p) => p.team_id === null)
        : [];

    // Current user info used as pseudo-member for solo projects
    const currentUser = {
      username: projectsData.username || "You",
      initials: projectsData.initials || "Me",
    };

    for (const project of soloProjects) {
      unifiedProjects.push({
        project: project,
        members: [currentUser],
        isSolo: true,
      });
    }

    // [DEV DEBUG] Full unified project list for inspection
    console.log("All projects(solo + team):", unifiedProjects);

    // Select project with highest task progress
    const project = await findMostAdvancedProjectUnified(unifiedProjects);

    if (!project) {
      teamBox.innerHTML = "<p>No active or progressed projects to display.</p>";
      return;
    }

    const finalProgress = Math.round(project.calculatedProgress);

    // Find the matching unified entry (to get member list)
    const matchingEntry = unifiedProjects.find(
      (entry) => entry.project.project_id === project.project_id,
    );

    if (!matchingEntry) {
      console.error(
        "Error: Project found, but no matching entry in unifiedProjects.",
      );
      teamBox.innerHTML = "<p>Error displaying project details.</p>";
      return;
    }

    const members = matchingEntry.members;

    // Update UI elements with project details
    document.getElementById("team-project-name").textContent = project.name;
    document.getElementById("total-time").textContent =
      project.duration_readable;

    // Display team members (or solo user) as styled initials
    const memberList = document.getElementById("team-member-list");
    memberList.innerHTML = "";
    members.forEach((member) => {
      const span = document.createElement("span");
      span.className = "member";
      span.textContent =
        member.initials || member.username.substring(0, 2).toUpperCase();
      span.style.backgroundColor = "#888";
      memberList.appendChild(span);
    });

    // Draw circular progress based on % of completed tasks
    drawProgressCircle("team-progress", finalProgress);
  } catch (error) {
    console.error("Error loading Team activities:", error);
    teamBox.innerHTML = "<p>Error loading team data.</p>";
  }
}

/**
 * Draws an animated circular progress indicator using SVG.
 *
 * Params:
 *   - containerId: ID of the DOM element where the SVG should be rendered
 *   - percent: number (0–100) representing completion percentage
 *
 * Renders:
 *   - A static background circle
 *   - A second circle whose stroke animates to represent progress
 *   - A text label showing the percentage
 */
function drawProgressCircle(containerId, percent) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const size = 120;
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  const initialOffset = circumference;

  container.innerHTML = `
        <svg width="${size}" height="${size}">
            <circle class="progress-circle-track" cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke-width="10" fill="none"/>
            <circle class="progress-circle-fill" cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke-width="10"
                    fill="none" stroke-dasharray="${circumference}"
                    stroke-dashoffset="${initialOffset}" transform="rotate(-90 ${size / 2} ${size / 2})"/>
            <text x="50%" y="50%" text-anchor="middle" dominant-baseline="central" font-size="20">${percent}%</text>
        </svg>
    `;

  const fillCircle = container.querySelector(".progress-circle-fill");
  if (fillCircle) {
    const progressColor = getComputedStyle(document.documentElement).getPropertyValue('--progress-color').trim();
    fillCircle.setAttribute("stroke", progressColor);
  }

  setTimeout(() => {
    if (fillCircle) {
      fillCircle.style.transition = "stroke-dashoffset 1s ease-out";
      const targetOffset = circumference * (1 - percent / 100);
      fillCircle.style.strokeDashoffset = targetOffset;
    }
  }, 50);
}

/**
 * Load the team activity box with a slight delay after page load.
 * This ensures layout and DOM are ready before execution.
 */
window.addEventListener("load", () => {
  setTimeout(() => {
    loadTeamActivityBox();
  }, 100);
});

/**
 * Fetches all tasks associated with a specific project ID.
 *
 * Params:
 *   - projectId: numeric ID of the project
 *
 * Returns:
 *   - Array of task objects if successful
 *   - Empty array on error
 */
async function fetchTasksByProjectId(projectId) {
  try {
    const res = await fetch(`/api/tasks?project_id=${projectId}`, {
      method: "GET",
      credentials: "include",
    });

    if (!res.ok) {
      console.error("Error fetching tasks for project", projectId);
      return [];
    }

    return await res.json();
  } catch (err) {
    console.error("Network error while fetching tasks:", err);
    return [];
  }
}

/**
 * Initialisiert das gestapelte Balkendiagramm in der Reports-Kachel des Dashboards.
 * Lädt wöchentliche Zeitdaten je Task asynchron über die API (/api/analysis/weekly-time-stacked),
 * gruppiert diese nach Projekt und Task, und rendert ein farblich sortiertes, gestapeltes Chart.
 * Die Farben pro Projekt stimmen mit denen aus der Analysis-Seite überein,
 * und innerhalb eines Projekts werden Tasks per Helligkeit differenziert dargestellt.
 */
document.addEventListener("DOMContentLoaded", async () => {
  const canvas = document.getElementById("dashboardReportsChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");

  // Feste Farben für Chart-Text und Grid für gute Sichtbarkeit in allen Modi
  const chartTextColor = "#1e4f85";
  const chartGridColor = "rgba(30, 79, 133, 0.15)";

  try {
    const res = await fetch("/api/analysis/weekly-time-stacked");
    const { labels, datasets } = await res.json();

    // Gruppiere nach Projektname
    const grouped = {};
    datasets.forEach((d) => {
      const [project, task] = d.label.split(":").map((s) => s.trim());
      if (!grouped[project]) grouped[project] = [];
      grouped[project].push({ ...d, project, task });
    });

    // Sortiere Tasks pro Projekt und weise abgestufte Farben zu
    const finalDatasets = Object.values(grouped).flatMap((entries) => {
      entries.sort((a, b) => a.task.localeCompare(b.task));
      const total = entries.length;
      return entries.map((entry, i) => ({
        ...entry,
        backgroundColor: getTaskColor(entry.project, entry.task, i, total),
      }));
    });

    new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: finalDatasets,
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const sec = context.raw * 3600;
                const h = Math.floor(sec / 3600);
                const m = Math.floor((sec % 3600) / 60);
                const s = Math.floor(sec % 60);
                return `${context.dataset.label}: ${h}h ${m}min ${s}s`;
              },
            },
          },
        },
        scales: {
          x: {
            stacked: true,
            ticks: { color: chartTextColor },
            grid: { color: chartGridColor },
          },
          y: {
            stacked: true,
            beginAtZero: true,
            ticks: { color: chartTextColor },
            grid: { color: chartGridColor },
          },
        },
      },
    });
  } catch (err) {
    console.error(
      "Error occured while loading data for the weekly report:",
      err,
    );
  }
});

/**
 * Aktiviert die Klick-Weiterleitung auf die Reports-Kachel im Dashboard.
 * Leitet zur Analysis-Seite weiter, wenn innerhalb der Reports-Kachel (außerhalb der Scrollbar) geklickt wird.
 */
document.addEventListener("DOMContentLoaded", () => {
  const reportsCard = document.querySelector(".reports");
  if (!reportsCard) return;

  reportsCard.style.cursor = "pointer";

  reportsCard.addEventListener("click", function (e) {
    const bounding = this.getBoundingClientRect();
    const scrollbarThreshold = 20;

    // Nur wenn Klick nicht auf Scrollbar war (sicher ist sicher)
    if (e.clientX < bounding.right - scrollbarThreshold) {
      window.location.href = "/analysis";
    }
  });
});

/**
 * Aktiviert die Klick-Weiterleitung auf die Fortschritts-Kachel im Dashboard.
 * Leitet zur Analysis-Seite mit aktivierter Progress-Ansicht weiter,
 * wenn innerhalb der Kachel (außerhalb von dekorativen Elementen) geklickt wird.
 */
document.addEventListener("DOMContentLoaded", () => {
  const teamCard = document.getElementById("team-activity-box");

  if (!teamCard) return;

  teamCard.style.cursor = "pointer";

  teamCard.addEventListener("click", function (e) {
    const ignoredElements = ["SPAN", "SVG", "CIRCLE", "TEXT"];
    if (ignoredElements.includes(e.target.tagName)) return;

    window.location.href = "/analysis?view=progress";
  });
});
