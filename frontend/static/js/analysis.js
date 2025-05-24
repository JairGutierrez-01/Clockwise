document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("#analysis-controls button");
  const views = {
    weekly: document.getElementById("view-weekly"),
    calendar: document.getElementById("view-calendar"),
    progress: document.getElementById("view-progress")
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
            backgroundColor: "#4dd0e1"
          },
          {
            label: "SEP",
            data: [1, 0, 2, 1, 0, 0, 0],
            backgroundColor: "#f06292"
          }
        ]
      },
      options: {
        responsive: true,
        animation: {
          duration: 800,
          easing: "easeOutQuart"
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Hours"
            }
          }
        }
      }
    });
  }

  function renderFullCalendar() {
    const calendarEl = document.getElementById("calendar");

    if (calendarInstance) {
      calendarInstance.destroy();
    }

    calendarInstance = new FullCalendar.Calendar(calendarEl, {
      initialView: "dayGridMonth",
        headerToolbar: {
          left: "prev",
          center: "title",
          right: "next"
        },
      views: {
        multiMonthYear: {
          type: "multiMonth",
          duration: { months: 12 }
        }
      },
      events: [
        { title: "Work", date: "2024-03-04", color: "#f28b82" },
        { title: "Check", date: "2024-03-11", color: "#a7c0f2" },
        { title: "Cram", date: "2024-03-13", color: "#81c995" },
        { title: "Final", date: "2024-03-22", color: "#e53935" }
      ]
    });

    calendarInstance.render();

    // View buttons
    document.getElementById("month-view-btn")?.addEventListener("click", () => {
      calendarInstance.changeView("dayGridMonth");
      setActiveView("month");
    });

    document.getElementById("year-view-btn")?.addEventListener("click", () => {
      calendarInstance.changeView("multiMonthYear");
      setActiveView("year");
    });

    function setActiveView(view) {
      document.getElementById("month-view-btn")?.classList.toggle("active", view === "month");
      document.getElementById("year-view-btn")?.classList.toggle("active", view === "year");
    }

    // Set default active button
    setActiveView("month");
  }

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelector("#analysis-controls .active")?.classList.remove("active");
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

  // Initial: render Chart (default view)
  renderChart();

  // === Calendar Grid fallback (if not using FullCalendar) ===
  const dueDates = ["2025-05-22", "2025-05-25"];
  function generateSimpleCalendar() {
    const grid = document.getElementById("calendar-grid");
    if (!grid) return;

    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();

    const firstDay = new Date(year, month, 1);
    const startDay = firstDay.getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    weekdays.forEach(day => {
      const cell = document.createElement("div");
      cell.textContent = day;
      grid.appendChild(cell);
    });

    for (let i = 0; i < startDay; i++) {
      grid.appendChild(document.createElement("div"));
    }

    for (let i = 1; i <= daysInMonth; i++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(i).padStart(2, "0")}`;
      const cell = document.createElement("div");
      cell.textContent = i;

      if (dueDates.includes(dateStr)) {
        cell.style.border = "2px solid red";
        cell.style.borderRadius = "6px";
      }

      grid.appendChild(cell);
    }
  }

  // Optional fallback (e.g. if FullCalendar not used)
  // generateSimpleCalendar();
});