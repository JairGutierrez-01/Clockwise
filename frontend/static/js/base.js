// Ping alle 60 Sekunden an den Server senden, um last_active zu aktualisieren
setInterval(() => {
  fetch("/ping", {
    method: "POST",
    credentials: "same-origin",
  });
}, 60000); // 60000 ms = 60 Sekunden
