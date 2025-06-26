/**
 * Sendet alle 60 Sekunden einen Ping an den Server, um den Benutzerstatus (last_active) aktuell zu halten.
 * Verwendet `fetch()` mit POST-Methode und gleichen Origin-Credentials.
 *
 * @function
 * @returns {void}
 */
setInterval(() => {
  fetch("/ping", {
    method: "POST",
    credentials: "same-origin",
  });
}, 60000); // 60000 ms = 60 Sekunden
