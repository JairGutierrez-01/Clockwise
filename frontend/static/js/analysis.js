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

  //Farbpalette für das Säulendiagramm
  const colorPalette = [
    "#00ff7f",
    "#b700ff",
    "#00f8dc",
    "#ff6b00",
    "#5a4132",
    "#0bd800",
    "#f032e6",
    "#f8ff00",
    "#c59595",
    "#008080",
    "#765595",
    "#ffc200",
    "#800000",
    "#64ac79",
    "#808000",
    "#0048ba",
    "#f1136f",
    "#ff2600",
    "#00cdfb",
    "#beff00",
  ];

  /**
   * Konvertiert eine hexadezimale Farbe in ein RGB-Objekt (um veschiedene Helligkeiten einer Farbe für die Tasks eines Projekts zu verwenden).
   * @param {string} hex - Farbwert in hex-Notation (z.B. "#ff0000")
   * @returns {{r: number, g: number, b: number}} - Die RGB-Werte.
   */
  function hexToRgb(hex) {
    // Entferne das "#" falls vorhanden
    hex = hex.replace(/^#/, "");
    if (hex.length === 3) {
      hex = hex
        .split("")
        .map((c) => c + c)
        .join("");
    }
    const bigint = parseInt(hex, 16);
    return {
      r: (bigint >> 16) & 255,
      g: (bigint >> 8) & 255,
      b: bigint & 255,
    };
  }

  /**
   * Wandelt RGB-Werte in HSL um.
   * @param {number} r - Rotwert (0–255)
   * @param {number} g - Grünwert (0–255)
   * @param {number} b - Blauwert (0–255)
   * @returns {[number, number, number]} - HSL als [Hue, Saturation, Lightness]
   */
  function rgbToHsl(r, g, b) {
    r /= 255;
    g /= 255;
    b /= 255;

    const max = Math.max(r, g, b),
      min = Math.min(r, g, b);
    let h,
      s,
      l = (max + min) / 2;

    if (max === min) {
      h = s = 0; // Grau
    } else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r:
          h = (g - b) / d + (g < b ? 6 : 0);
          break;
        case g:
          h = (b - r) / d + 2;
          break;
        case b:
          h = (r - g) / d + 4;
          break;
      }
      h /= 6;
    }

    return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
  }

  /**
   * Gibt eine zu einem Projektnamen gehörende Farbe zurück.
   * @param {string} projectName - Name des Projekts.
   * @returns {string} - Hex-Farbwert.
   */
  function getColorForProject(projectName) {
    let hash = 0;
    const full = projectName + "_hash";
    for (let i = 0; i < full.length; i++) {
      hash = full.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % colorPalette.length;
    return colorPalette[index];
  }

  /**
   * Gibt eine abgestufte HSL-Farbe für eine Task innerhalb eines Projekts zurück.
   * @param {string} project - Projektname.
   * @param {string} task - Taskname.
   * @param {number} [indexInStack=0] - Position der Task im Stapel.
   * @param {number} [total=1] - Gesamtanzahl der Tasks.
   * @returns {string} - Farbwert im HSL-Format.
   */
  function getTaskColor(project, task, indexInStack = 0, total = 1) {
    const baseColor = getColorForProject(project);
    const rgb = hexToRgb(baseColor);
    let [h, s, l] = rgbToHsl(rgb.r, rgb.g, rgb.b);

    // Staffelung: dunkel unten (index = 0), hell oben
    const step = 40 / Math.max(total - 1, 1); // max. 40% Unterschied
    l = Math.min(90, Math.max(10, l - 20 + step * indexInStack));

    return `hsl(${h}, ${s}%, ${l}%)`;
  }

  /**
   * Passt die Helligkeit einer Hexfarbe um einen Prozentwert an.
   * @param {string} color - Ausgangsfarbe in Hex.
   * @param {number} percent - Prozentuale Veränderung (-100 bis +100).
   * @returns {string} - Neue Hexfarbe.
   */
  function shadeColor(color, percent) {
    const f = parseInt(color.slice(1), 16),
      t = percent < 0 ? 0 : 255,
      p = Math.abs(percent) / 100,
      R = f >> 16,
      G = (f >> 8) & 0x00ff,
      B = f & 0x0000ff;

    const newColor = (
      0x1000000 +
      (Math.round((t - R) * p) + R) * 0x10000 +
      (Math.round((t - G) * p) + G) * 0x100 +
      (Math.round((t - B) * p) + B)
    )
      .toString(16)
      .slice(1);

    return `#${newColor}`;
  }

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
