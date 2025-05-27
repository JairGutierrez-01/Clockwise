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

    fetch("/analysis/projects")
      .then((res) => res.json())
      .then((data) => {
        const events = data.projects || [];

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
        });

        calendarInstance.render();

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

        // Set default active button
        setActiveView("month");
      })
      .catch((err) => {
        console.error("Fehler beim Laden der Kalenderdaten:", err);
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
