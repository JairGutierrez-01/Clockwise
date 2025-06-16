document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("#analysis-controls button");
  const views = {
    weekly: document.getElementById("view-weekly"),
    calendar: document.getElementById("view-calendar"),
    progress: document.getElementById("view-progress"),
  };

  let chartInstance = null;
  let calendarInstance = null;
  let currentWeekOffset = 0;

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
    "#57956a",
    "#808000",
  ];

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

  function getColorForProject(projectName) {
    let hash = 0;
    const full = projectName + "_hash";
    for (let i = 0; i < full.length; i++) {
      hash = full.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % colorPalette.length;
    return colorPalette[index];
  }

  function getTaskColor(project, task, indexInStack = 0, total = 1) {
    const baseColor = getColorForProject(project);
    const rgb = hexToRgb(baseColor);
    let [h, s, l] = rgbToHsl(rgb.r, rgb.g, rgb.b);

    // Staffelung: dunkel unten (index = 0), hell oben
    const step = 40 / Math.max(total - 1, 1); // max. 40% Unterschied
    l = Math.min(90, Math.max(10, l - 20 + step * indexInStack));

    return `hsl(${h}, ${s}%, ${l}%)`;
  }

  // Funktion zur Helligkeitsanpassung in Prozent
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

  function getStartOfWeekWithOffset(offset) {
    const now = new Date();
    const day = now.getDay(); // 0=So, 1=Mo
    const monday = new Date(now);
    const diff = day === 0 ? -6 : 1 - day;
    monday.setDate(monday.getDate() + diff + offset * 7);
    monday.setHours(0, 0, 0, 0);
    return monday;
  }

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

        // Buttons für Ansicht
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
        console.error("❌ Fehler beim Laden von Kalenderdaten:", err);
      });
  }

  // === View Switching ===
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

  // === Initial Load: prüfe URL-Parameter
  const params = new URLSearchParams(window.location.search);
  const view = params.get("view") || "weekly";

  // falls Seite über Dashboard Calender Card aufgerufen wird => Kalender aufrufen, ansonsten immer weekly aufrufen
  const targetBtn = document.querySelector(`button[data-view="${view}"]`);
  if (targetBtn) {
    targetBtn.click();
  } else {
    updateChartForWeek();
  }
});
