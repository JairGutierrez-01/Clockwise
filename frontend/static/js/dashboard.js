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
    // Verhindert Weiterleitung, wenn in die Scrollbar geklickt wurde
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
