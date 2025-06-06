document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("#analysis-controls button");
  const views = {
    weekly: document.getElementById("view-weekly"),
    calendar: document.getElementById("view-calendar"),
    progress: document.getElementById("view-progress"),
  };

  let chartInstance = null;
  let calendarInstance = null;

    const colorPalette = [
    // Rottöne & Orange
    "#F94144", "#F3722C", "#F8961E", "#F9C74F",

    // Grüntöne
    "#90BE6D", "#43AA8B", "#2A9D8F", "#06D6A0",

    // Blautöne
    "#577590", "#277DA1", "#118AB2", "#1D3557",

    // Violett & Pink
    "#9B5DE5", "#F15BB5", "#C77DFF", "#A2D2FF",

    // Türkis & Mint
    "#00BBF9", "#00F5D4", "#38B000", "#80FFDB",

    // Dunkel- und Kontrastfarben
    "#6A4C93", "#8338EC", "#3A0CA3", "#FF6D00"
  ];

  // Farbe pro Projektname zuweisen
  function getColorForProject(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % colorPalette.length;
    return colorPalette[index];
  }


  function getColorForProject(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % colorPalette.length;
    return colorPalette[index];
  }

  async function renderChart() {
    const ctx = document.getElementById("timeChart").getContext("2d");

    if (chartInstance) {
      chartInstance.destroy();
    }

    try {
      const res = await fetch("/api/analysis/weekly-time");
      const json = await res.json();
      const { labels, projects } = json;

      const datasets = Object.entries(projects).map(([project, data]) => ({
        label: project || "No Project",
        data: data,
        backgroundColor: getColorForProject(project),
      }));

      chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: datasets,
        },
        options: {
          responsive: true,
          animation: {
            duration: 800,
            easing: "easeOutQuart",
          },
          scales: {
            x: {
              ticks: {
                color: "#ffffff"
              },
              grid: {
                color: "rgba(255, 255, 255, 0.1)"
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: "Hours",
                color: "#ffffff"
              },
              ticks: {
                color: "#ffffff"
              },
              grid: {
                color: "rgba(255, 255, 255, 0.1)"
              }
            }
          },
          plugins: {
            legend: {
              labels: {
                color: "#ffffff"
              }
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  const totalSeconds = context.raw * 3600;
                  const h = Math.floor(totalSeconds / 3600);
                  const m = Math.floor((totalSeconds % 3600) / 60);
                  const s = Math.floor(totalSeconds % 60);
                  return `${context.dataset.label}: ${h}h ${m}min ${s}s`;
                }
              }
            }
          }
        }
      });
    } catch (err) {
      console.error("Error occured while loading chart data:", err);
    }
  }


  function renderFullCalendar() {
  const calendarEl = document.getElementById("calendar");

  if (calendarInstance) {
    calendarInstance.destroy();
  }

  // Fetch nur due dates und aggregierte Arbeitszeit
  Promise.all([
    fetch("/calendar-due-dates").then(res => res.json()),
    fetch("/calendar-worked-time").then(res => res.json())
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
    eventDidMount: function(info) {
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
    }
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

  // === Initial Load (Default: Weekly) ===
  renderChart();
});
