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
