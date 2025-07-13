import { getTaskColor } from "./color_utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("#analysis-controls button");
  const views = {
    weekly: document.getElementById("view-weekly"),
    calendar: document.getElementById("view-calendar"),
    progress: document.getElementById("view-progress"),
  };

  let chartInstance = null;
  let calendarInstance = null;
  let chartActual = null;
  let chartCompletion = [];
  let currentWeekOffset = 0;

  // Theme colors from CSS variables
  const themeStyles = getComputedStyle(document.documentElement);
  const isDarkMode = document.body.classList.contains('dark-mode');

  /**
   * Rendert das Wochen-Diagramm mit gestapelten Balken pro Projekt/Task.
   * @param {string|null} [weekStart=null] - ISO-Datum (YYYY-MM-DD) des Wochenanfangs oder null für aktuelle Woche.
   * @returns {Promise<void>}
   */
  async function renderChart(weekStart = null) {
    const isDarkMode = document.body.classList.contains("dark-mode");
    const gridColor = isDarkMode ? "#ffffff" : "#000000";
    const ctx = document.getElementById("timeChart").getContext("2d");
    if (chartInstance) chartInstance.destroy(); // Vorherige Chart-Instanz entfernen, um Speicherlecks und Überlagerungen zu vermeiden

    try {
      const url = weekStart
        ? `/api/analysis/weekly-time-stacked?start=${weekStart}`
        : `/api/analysis/weekly-time-stacked`;
      const res = await fetch(url);
      const { labels, datasets } = await res.json();

      // Gruppieren nach Projekt
      const groupedByProject = {};

      datasets.forEach((d) => {
        const [project, task] = d.label.split(":").map((s) => s.trim()); // Erwartet Format "Projekt: Task", trennt zur späteren Gruppierung und Farbgebung
        if (!groupedByProject[project]) groupedByProject[project] = [];
        groupedByProject[project].push({ ...d, project, task });
      });

      // Tasks pro Projekt sortieren und abgestufte Farben nutzen
      const coloredDatasets = Object.values(groupedByProject).flatMap(
        // Sortiert Tasks pro Projekt alphabetisch und erstellt daraus eine flache Liste mit Farbinfos (getTaskColor(project, task, i, total) vergibt Farben// basierend auf Indexreihenfolge der Tasks innerhalb eines Projekts => Wenn Reihenfolge zufällig bei jedem Aufruf => Farben inkonsistent)
        (entries) => {
          entries.sort((a, b) => a.task.localeCompare(b.task));
          const total = entries.length;

          return entries.map((entry, i) => ({
            ...entry,
            backgroundColor: getTaskColor(entry.project, entry.task, i, total),
          }));
        },
      );

      chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: coloredDatasets,
        },
        options: {
          responsive: true,
          elements: {
            bar: {
              borderRadius: 2,
              barThickness: 50,
              maxBarThickness: 60,
              minBarLength: 1,
              borderSkipped: false,
            },
          },
          scales: {
            x: {
              stacked: true,
              ticks: { color: gridColor },
              grid: { color: gridColor },
              categoryPercentage: 0.7,
              barPercentage: 1.0,
            },
            y: {
              stacked: true,
              beginAtZero: true,
              title: {
                display: true,
                text: "Hours",
                color: gridColor,
              },
              ticks: { color: gridColor },
              grid: { color: gridColor },
            },
          },
          plugins: {
            legend: {
              labels: { color: gridColor },
            },
            tooltip: {
              // Tooltip zeigt Zeit in Stunden, Minuten und Sekunden an (Konvertierung von Dezimalstunden)
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
        },
      });
    } catch (e) {
      console.error("Error occured while loading chart data:", e);
    }
  }

  /**
   * Gibt das Datum des Montags einer Woche mit gegebenem Offset zurück.
   * @param {number} offset - Wochen-Offset relativ zur aktuellen Woche (z.B. -1 für letzte Woche, 0 für diese).
   * @returns {Date} - Das Datum des Montags der Zielwoche.
   */
  function getStartOfWeekWithOffset(offset) {
    const now = new Date();
    const day = now.getDay(); // 0=So, 1=Mo, ..., 6 = Sa
    const monday = new Date(now);
    // Differenz zum aktuellen Montag berechnen (wenn heute Sonntag, dann -6)
    const diff = day === 0 ? -6 : 1 - day;
    // Ziel-Montag berechnen, inkl. Wochenoffset
    monday.setDate(monday.getDate() + diff + offset * 7);
    // Uhrzeit auf 00:00:00 setzen
    monday.setHours(0, 0, 0, 0);
    return monday;
  }
  async function triggerCheckProgress() {
    const res = await fetch("/api/analysis/check_progress", {
      method: "POST",
    });

    if (!res.ok) {
      console.error("Fehler beim Prüfen des Fortschritts");
    } else {
      console.log("Fortschrittsprüfung durchgeführt");
    }
  }
  /**
   * Aktualisiert das Diagramm und die Wochenanzeige basierend auf dem aktuellen Offset.
   * Nutzt das aktuelle weekOffset, um Start- und Enddatum zu berechnen und das Diagramm zu laden.
   */
  function updateChartForWeek() {
    const startOfWeek = getStartOfWeekWithOffset(currentWeekOffset); // Montag der aktuellen Woche (mit Offset)
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6); // Sonntag derselben Woche

    // Wochenzeitraum formatiert als Anzeige (z.B. „3.– 9. Juni 2025“)
    const weekLabel = `${startOfWeek.toLocaleDateString("de-DE", {
      day: "numeric",
      month: "short",
    })} – ${endOfWeek.toLocaleDateString("de-DE", {
      day: "numeric",
      month: "long",
      year: "numeric",
    })}`;
    document.getElementById("week-label").textContent = weekLabel;

    // Diagramm neu laden mit ISO-Startdatum
    const isoStart = startOfWeek.toISOString().split("T")[0];
    renderChart(isoStart);
  }

  /**
   * Initialisiert und rendert den FullCalendar mit Due-Dates und Arbeitszeit-Einträgen.
   * Bindet Event-Listener für Monats- und Jahresansicht.
   * @returns {void}
   */
  function renderFullCalendar() {
    const calendarEl = document.getElementById("calendar");

    if (calendarInstance) {
      calendarInstance.destroy();
    }

    // Fetch nur due dates und aggregierte Arbeitszeit
    Promise.all([
      fetch("/calendar-due-dates").then((res) => res.json()),
      fetch("/calendar-worked-time").then((res) => res.json()),
    ])
      .then(([dueDates, workedTime]) => {
        const events = [...dueDates, ...workedTime];

        calendarInstance = new FullCalendar.Calendar(calendarEl, {
          initialView: "dayGridMonth",
          headerToolbar: {
            left: "prev",
            center: "title",
            right: "next",
          },
          views: {
            multiMonthYear: {
              type: "multiMonth",
              duration: { months: 12 },
            },
          },
          events: events,
          eventDidMount: function (info) {
            const project = info.event.extendedProps.project;

            if (project) {
              let tooltip;

              info.el.addEventListener("mouseenter", (e) => {
                tooltip = document.createElement("div");
                tooltip.innerText = `Projekt: ${project}`;
                tooltip.style.position = "absolute";
                tooltip.style.background = isDarkMode ? '#333' : '#fff';
                tooltip.style.color = gridColor;
                tooltip.style.padding = "4px 8px";
                tooltip.style.borderRadius = "4px";
                tooltip.style.fontSize = "12px";
                tooltip.style.pointerEvents = "none";
                tooltip.style.zIndex = 1000;
                tooltip.style.whiteSpace = "nowrap";
                tooltip.style.boxShadow = "0 2px 6px rgba(0,0,0,0.3)";
                tooltip.style.transition = "opacity 0.1s";

                document.body.appendChild(tooltip);
                tooltip.style.opacity = "1";
                tooltip.style.left = e.pageX + 10 + "px";
                tooltip.style.top = e.pageY + "px";
              });

              info.el.addEventListener("mousemove", (e) => {
                if (tooltip) {
                  tooltip.style.left = e.pageX + 10 + "px";
                  tooltip.style.top = e.pageY + "px";
                }
              });

              info.el.addEventListener("mouseleave", () => {
                if (tooltip) {
                  tooltip.remove();
                  tooltip = null;
                }
              });
            }
          },
        });

        calendarInstance.render();

        // Buttons für Monats- und Jahresansicht
        document
          .getElementById("month-view-btn")
          ?.addEventListener("click", () => {
            calendarInstance.changeView("dayGridMonth");
            setActiveView("month");
          });

        document
          .getElementById("year-view-btn")
          ?.addEventListener("click", () => {
            calendarInstance.changeView("multiMonthYear");
            setActiveView("year");
          });

        // Setzt die aktive Ansicht (z.B. "month" oder "year") und aktualisiert die UI.
        //@param {string} view - Der anzuzeigende Modus: "month" oder "year".
        function setActiveView(view) {
          document
            .getElementById("month-view-btn")
            ?.classList.toggle("active", view === "month");
          document
            .getElementById("year-view-btn")
            ?.classList.toggle("active", view === "year");
        }

        setActiveView("month");
      })
      .catch((err) => {
        console.error("Error occured while loading calendar data:", err);
      });
  }

  /**
   * Renders the Progress view: project completion bars and actual vs planned charts.
   */
  /**
   * Rendert die Fortschrittsansicht mit Projekt-Fortschrittsbalken und Soll-/Ist-Vergleich.
   * @returns {Promise<void>}
   */
  async function renderProgress() {
    await triggerCheckProgress();
    // Destroy existing charts if present
    if (chartActual) chartActual.destroy();
    // Clear and build project completion list
    const listEl = document.getElementById("project-completion-list");
    listEl.innerHTML = "";
    chartCompletion = [];

    try {
      // Fetch completion
      const resProg = await fetch("/api/analysis/project-progress");
      const projData = await resProg.json();
      // Fetch overall progress
      const resOverall = await fetch("/api/analysis/overall-progress");
      const { overall_progress } = await resOverall.json();
      const percentOverall = Math.round(overall_progress * 100);

      // Fortschrittsbalken aktualisieren
      const fill = document.querySelector(".overall-progress-fill");
      if (fill) fill.style.width = `${percentOverall}%`;
      const percentEl = document.querySelector(".overall-progress-percent");
      if (percentEl) percentEl.textContent = `${percentOverall}%`;

      Object.entries(projData).forEach(([project, ratio]) => {
        const percent = Math.round(ratio * 100);
        const item = document.createElement("div");
        item.className = "progress-item";

        // Project label
        const labelEl = document.createElement("span");
        labelEl.className = "label";
        labelEl.textContent = project;
        item.appendChild(labelEl);

        // Progress Circle (copied from Jair)
        const size = 100;
        const radius = size / 2 - 8;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference * (1 - percent / 100);
        const textColor = isDarkMode ? '#fff' : '#000';
        const frag = document.createRange().createContextualFragment(`
          <svg width="${size}" height="${size}">
            <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke="#444" stroke-width="8" fill="none"/>
            <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke="#00bfa5" stroke-width="8" fill="none"
                    stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
                    transform="rotate(-90 ${size / 2} ${size / 2})" class="progress-circle-fill"/>
            <text x="50%" y="50%" text-anchor="middle" dominant-baseline="central" font-size="16" fill="${textColor}">${percent}%</text>
          </svg>
        `);
        item.appendChild(frag);
        listEl.appendChild(item);
      });

      // Fetch actual vs planned
      const resComp = await fetch("/api/analysis/actual-vs-planned");
      const compData = await resComp.json();
      const labels = Object.keys(compData);
      const actuals = labels.map((p) => compData[p].actual);
      const targets = labels.map((p) => compData[p].target);
      const barColorActual = "#376cae";
      const barColorPlanned = "#13406c";

      // actual vs planned chart
      const ctx = document.getElementById("actualChart").getContext("2d");
      chartActual = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Actual (h)",
              data: actuals,
              backgroundColor: barColorActual,
            },
            {
              label: "Planned (h)",
              data: targets,
              backgroundColor: barColorPlanned,
            },
          ],
        },
        options: {
          responsive: true,
          scales: {
            x: {
              stacked: false,
              ticks: { color: gridColor },
              grid: { color: gridColor },
            },
            y: {
              beginAtZero: true,
              ticks: { color: gridColor },
              grid: { color: gridColor },
            },
          },
          plugins: {
            legend: {
              labels: { color: gridColor },
            },
          },
        },
      });
    } catch (e) {
      console.error("Error loading progress data:", e);
    }
  }

  // View Switching (zwischen den Analyse-Ansichten wechseln)
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      // Aktiven Button visuell aktualisieren
      document
        .querySelector("#analysis-controls .active")
        ?.classList.remove("active");
      btn.classList.add("active");

      const selected = btn.dataset.view; // z.B. "weekly", "calendar" oder "progress"

      // Alle View-Container durchgehen und ein-/ausblenden
      Object.entries(views).forEach(([key, el]) => {
        if (key === selected) {
          el.classList.remove("hidden");

          if (key === "weekly") {
            updateChartForWeek();
          } else if (key === "calendar") {
            renderFullCalendar();
          } else if (key === "progress") {
            renderProgress();
          }
        } else {
          el.classList.add("hidden");
        }
      });
    });
  });

  // Navigation zur vorherigen Woche: Offset um -1 verringern und Diagramm aktualisieren
  document.getElementById("prev-week").addEventListener("click", () => {
    currentWeekOffset--;
    updateChartForWeek();
  });

  // Navigation zur nächsten Woche: Offset um +1 erhöhen und Diagramm aktualisieren
  document.getElementById("next-week").addEventListener("click", () => {
    currentWeekOffset++;
    updateChartForWeek();
  });

  //Initial Load: prüfe URL-Parameter
  const params = new URLSearchParams(window.location.search);
  const view = params.get("view") || "weekly";

  // falls Seite über Dashboard Calender Card aufgerufen wird => Kalender aufrufen, ansonsten immer weekly aufrufen
  const targetBtn = document.querySelector(`button[data-view="${view}"]`);
  if (targetBtn) {
    targetBtn.click();
  } else {
    updateChartForWeek();
  }

  const downloadBtn = document.getElementById("download-button");
  const dropdown = document.getElementById("download-dropdown");

  downloadBtn.addEventListener("click", () => {
    dropdown.classList.toggle("hidden");
  });

  // Wenn außerhalb geklickt wird, Dropdown schließen
  document.addEventListener("click", (e) => {
    if (!downloadBtn.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.add("hidden");
    }
  });

  // Export-Logik
  dropdown.addEventListener("click", (e) => {
    if (e.target.tagName !== "BUTTON") return;
    const format = e.target.dataset.format;
    if (!format) return;

    // Aktuelle Woche ermitteln
    const startOfWeek = getStartOfWeekWithOffset(currentWeekOffset);
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);

    const isoStart = startOfWeek.toISOString().split("T")[0];
    const isoEnd = endOfWeek.toISOString().split("T")[0];

    const url =
      format === "pdf"
        ? `/api/analysis/export/pdf?start=${isoStart}&end=${isoEnd}`
        : `/api/analysis/export/csv?start=${isoStart}&end=${isoEnd}`;

    // Startet Download
    window.open(url, "_blank");
  });
});
