// ==== Notification Filtering ====
document.addEventListener("DOMContentLoaded", () => {
  const filterButtons = document.querySelectorAll("#filter-controls button");
  const cards = document.querySelectorAll(".notification-card");

  filterButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      // Reset active class
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

// Benachrichtigung als gelesen markieren
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

// Benachrichtigung löschen
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
