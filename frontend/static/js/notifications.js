// Benachrichtigung als gelesen markieren
function markAsRead(id) {
  fetch(`/notifications/read/${id}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((res) => {
      if (!res.ok) throw new Error("Error occured while marking message as read");
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