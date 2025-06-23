import {getTaskColor} from './color_utils.js';

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

function ensureTeamBoxExists() {
  let teamBox = document.getElementById("team-activity-box");

  if (!teamBox) {
    const targetParent =
      document.querySelector(".dashboard-grid") ||
      document.querySelector("#dashboard");
    if (!targetParent) return null;

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

    teamBox.style.cursor = "pointer";
    teamBox.addEventListener("click", function (event) {
      const ignoredElements = ["SPAN", "SVG", "CIRCLE", "TEXT"];
      if (ignoredElements.includes(event.target.tagName)) return;

      window.location.href = "/analysis?view=progress";
    });
  }

  return teamBox;
}

async function calculateProjectProgress(projectId) {
  try {
    const tasks = await fetchTasksByProjectId(projectId);
    const totalTasks = tasks.length;
    const doneTasks = tasks.filter((t) => t.status === "done").length;
    return totalTasks > 0 ? (doneTasks / totalTasks) * 100 : 0;
  } catch (error) {
    console.error(
      `Error calculating progress for project ${projectId}:`,
      error,
    );
    return 0; // Default to 0% on error
  }
}

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

async function loadTeamActivityBox() {
  const teamBox = ensureTeamBoxExists();
  if (!teamBox) return;

  try {
    const res = await fetch("/api/teams/full");
    const data = await res.json();

    //Fetch solo projects and prepare unifiedProjects
    const projectsRes = await fetch("/api/projects", {
      method: "GET",
      credentials: "include",
    });
    const projectsData = await projectsRes.json();
    // Fetch solo projects

    // Build unifiedProjects array (team + solo)
    const unifiedProjects = [];

    // Team projects
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

    // For now, just log the unified list
    console.log("All projects(solo + team):", unifiedProjects);

    const project = await findMostAdvancedProjectUnified(unifiedProjects);

    if (!project) {
      teamBox.innerHTML = "<p>No active or progressed projects to display.</p>";
      return;
    }

    const finalProgress = Math.round(project.calculatedProgress);

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

    document.getElementById("team-project-name").textContent = project.name;

    document.getElementById("total-time").textContent =
      project.duration_readable;

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

    drawProgressCircle("team-progress", finalProgress);
  } catch (error) {
    console.error("Error loading Team activities:", error);
    teamBox.innerHTML = "<p>Error loading team data.</p>";
  }
}

function drawProgressCircle(containerId, percent) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const size = 120;
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  const initialOffset = circumference;

  container.innerHTML = `
        <svg width="${size}" height="${size}">
            <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke="#444" stroke-width="10" fill="none"/>
            <circle class="progress-circle-fill" cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke="#00bfa5" stroke-width="10"
                    fill="none" stroke-dasharray="${circumference}"
                    stroke-dashoffset="${initialOffset}" transform="rotate(-90 ${size / 2} ${size / 2})"/>
            <text x="50%" y="50%" text-anchor="middle" dominant-baseline="central" font-size="20" fill="#fff">${percent}%</text>
        </svg>
    `;

  setTimeout(() => {
    const fillCircle = container.querySelector(".progress-circle-fill");
    if (fillCircle) {
      fillCircle.style.transition = "stroke-dashoffset 1s ease-out";
      const targetOffset = circumference * (1 - percent / 100);
      fillCircle.style.strokeDashoffset = targetOffset;
    }
  }, 50);
}

window.addEventListener("load", () => {
  setTimeout(() => {
    loadTeamActivityBox();
  }, 100);
});

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
            ticks: { color: "#fff" },
            grid: { color: "rgba(255,255,255,0.1)" },
          },
          y: {
            stacked: true,
            beginAtZero: true,
            ticks: { color: "#fff" },
            grid: { color: "rgba(255,255,255,0.1)" },
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
