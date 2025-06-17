/**
 * Initialisiert die Filterfunktion für Benachrichtigungskarten.
 * Reagiert auf Button-Klicks und blendet Karten je nach Typ dynamisch ein/aus.
 */
document.addEventListener("DOMContentLoaded", () => {
  const filterButtons = document.querySelectorAll("#filter-controls button");
  const cards = document.querySelectorAll(".notification-card");

  filterButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      // Entfernt aktive Hervorhebung von allen Buttons und markiert den geklickten als aktiv
      filterButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const selectedType = btn.dataset.filter;

      cards.forEach((card) => {
        const cardType = card.dataset.type;

        if (
          selectedType === "all" ||
          (selectedType === "info" &&
            !["task", "team", "project", "progress"].includes(cardType)) ||
          cardType === selectedType
        ) {
          card.style.display = "";
        } else {
          card.style.display = "none";
        }
      });
    });
  });
});

/**
 * Markiert eine Benachrichtigung auf dem Server als gelesen.
 * @param {string} id - Die ID der Benachrichtigung.
 */
function markAsRead(id) {
  fetch(`/notifications/read/${id}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((res) => {
      if (!res.ok)
        throw new Error("Error occured while marking message as read");
      return res.json();
    })
    .then((data) => {
      console.log(data.message);
      location.reload();
    })
    .catch((err) => {
      console.error("Error:", err);
    });
}

/**
 * Löscht eine Benachrichtigung auf dem Server.
 * @param {string} id - Die ID der Benachrichtigung.
 */
function deleteNotification(id) {
  fetch(`/notifications/delete/${id}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  }).then(() => {
    location.reload();
  });
}