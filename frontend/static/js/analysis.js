import {getTaskColor} from './color_utils.js';

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

  /**
   * Rendert das Wochen-Diagramm mit gestapelten Balken pro Projekt/Task.
   * @param {string|null} [weekStart=null] - ISO-Datum (YYYY-MM-DD) des Wochenanfangs oder null für aktuelle Woche.
   * @returns {Promise<void>}
   */
  async function renderChart(weekStart = null) {
    const ctx = document.getElementById("timeChart").getContext("2d");
    if (chartInstance) chartInstance.destroy();

    try {
      const url = weekStart
        ? `/api/analysis/weekly-time-stacked?start=${weekStart}`
        : `/api/analysis/weekly-time-stacked`;
      const res = await fetch(url);
      const { labels, datasets } = await res.json();

      // Gruppieren nach Projekt
      const groupedByProject = {};

      datasets.forEach((d) => {
        const [project, task] = d.label.split(":").map((s) => s.trim());
        if (!groupedByProject[project]) groupedByProject[project] = [];
        groupedByProject[project].push({ ...d, project, task });
      });

      // Tasks pro Projekt sortieren und abgestufte Farben nutzen
      const coloredDatasets = Object.values(groupedByProject).flatMap(
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
              ticks: { color: "#fff" },
              grid: { color: "rgba(255,255,255,0.1)" },
              categoryPercentage: 0.7,
              barPercentage: 1.0,
            },
            y: {
              stacked: true,
              beginAtZero: true,
              title: {
                display: true,
                text: "Hours",
                color: "#fff",
              },
              ticks: { color: "#fff" },
              grid: { color: "rgba(255,255,255,0.1)" },
            },
          },
          plugins: {
            legend: {
              labels: { color: "#fff" },
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
        },
      });
    } catch (e) {
      console.error("Error occured while loading chart data:", e);
    }
  }

  /**
   * Gibt das Datum des Montags einer Woche mit gegebenem Offset zurück.
   * @param {number} offset - Wochen-Offset relativ zur aktuellen Woche (z. B. -1 für letzte Woche, 0 für diese).
   * @returns {Date} - Das Datum des Montags der Zielwoche.
   */
  function getStartOfWeekWithOffset(offset) {
    const now = new Date();
    const day = now.getDay(); // 0=So, 1=Mo
    const monday = new Date(now);
    const diff = day === 0 ? -6 : 1 - day;
    monday.setDate(monday.getDate() + diff + offset * 7);
    monday.setHours(0, 0, 0, 0);
    return monday;
  }

  /**
   * Aktualisiert das Diagramm und die Wochenanzeige basierend auf dem aktuellen Offset.
   * Nutzt das aktuelle weekOffset, um Start- und Enddatum zu berechnen und das Diagramm zu laden.
   */
  function updateChartForWeek() {
    const startOfWeek = getStartOfWeekWithOffset(currentWeekOffset);
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);

    // Formatieren für Label
    const weekLabel = `${startOfWeek.toLocaleDateString("de-DE", {
      day: "numeric",
      month: "short",
    })} – ${endOfWeek.toLocaleDateString("de-DE", { day: "numeric", month: "long", year: "numeric" })}`;
    document.getElementById("week-label").textContent = weekLabel;

    //
    const isoStart = startOfWeek.toISOString().split("T")[0];
    renderChart(isoStart);
  }

  /**
   * Initialisiert und rendert den FullCalendar mit Due-Dates und Arbeitszeit-Einträgen.
   * Bindet Event-Listener für Monats- und Jahresansicht.
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
                tooltip.style.background = "#333";
                tooltip.style.color = "#fff";
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

        /**
         * Setzt die aktive Ansicht im Kalender (z. B. „month“ oder „year“) und aktualisiert die Button-UI.
         * @param {string} view - Der anzuzeigende Modus: "month" oder "year".
         */
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
  async function renderProgress() {
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
        const frag = document.createRange().createContextualFragment(`
          <svg width="${size}" height="${size}">
            <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke="#444" stroke-width="8" fill="none"/>
            <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke="#00bfa5" stroke-width="8" fill="none"
                    stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
                    transform="rotate(-90 ${size / 2} ${size / 2})" class="progress-circle-fill"/>
            <text x="50%" y="50%" text-anchor="middle" dominant-baseline="central" font-size="16" fill="#fff">${percent}%</text>
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
              ticks: { color: "#fff" },
              grid: { color: "rgba(255,255,255,0.1)" },
            },
            y: {
              beginAtZero: true,
              ticks: { color: "#fff" },
              grid: { color: "rgba(255,255,255,0.1)" },
            },
          },
          plugins: {
            legend: {
              labels: { color: "#fff" },
            },
          },
        },
      });
    } catch (e) {
      console.error("Error loading progress data:", e);
    }
  }

  // View Switching
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelector("#analysis-controls .active")
        ?.classList.remove("active");
      btn.classList.add("active");

      const selected = btn.dataset.view;
      Object.entries(views).forEach(([key, el]) => {
        if (key === selected) {
          el.classList.remove("hidden");

          if (key === "weekly") {
            renderChart();
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

  document.getElementById("prev-week").addEventListener("click", () => {
    currentWeekOffset--;
    updateChartForWeek();
  });

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
