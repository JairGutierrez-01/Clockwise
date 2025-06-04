document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("#analysis-controls button");
  const views = {
    weekly: document.getElementById("view-weekly"),
    calendar: document.getElementById("view-calendar"),
    progress: document.getElementById("view-progress"),
  };

  let chartInstance = null;
  let calendarInstance = null;

  function renderChart() {
    const ctx = document.getElementById("timeChart").getContext("2d");

    if (chartInstance) {
      chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
        datasets: [
          {
            label: "Analysis",
            data: [2, 3, 0, 0, 0, 0, 0],
            backgroundColor: "#4dd0e1",
          },
          {
            label: "SEP",
            data: [1, 0, 2, 1, 0, 0, 0],
            backgroundColor: "#f06292",
          },
        ],
      },
      options: {
        responsive: true,
        animation: {
          duration: 800,
          easing: "easeOutQuart",
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Hours",
            },
          },
        },
      },
    });
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
