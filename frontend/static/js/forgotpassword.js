/**
 * Sendet eine Anfrage zum erneuten Versand der Passwort-Zurücksetzen-E-Mail.
 *
 * - Verhindert das Standardverhalten des Formulars.
 * - Prüft, ob eine E-Mail-Adresse eingegeben wurde.
 * - Sendet eine POST-Anfrage an den Server mit der E-Mail-Adresse.
 * - Zeigt je nach Antwort eine Erfolgsmeldung oder Fehlermeldung an.
 *
 * @param {Event} event - Das Event-Objekt des Formular-Submits.
 */
function resendEmail(event) {
  // Standardverhalten des Formulars verhindern (z.B. Seitenreload)
  event.preventDefault();

  // Eingegebene E-Mail-Adresse aus dem Formular holen
  const email = document.querySelector('input[name="email"]').value;

  // Validierung: Wenn keine E-Mail eingegeben wurde, abbrechen
  if (!email) {
    alert("Please enter your email address first.");
    return;
  }

  // Anfrage an den Server senden, um eine neue Reset-Mail zu versenden
  fetch("/auth/resend-reset-email", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  })
    .then((res) => res.json())
    .then((data) => {
      // Rückmeldung an den Nutzer je nach Server-Antwort
      if (data.success) {
        alert(data.message);  // Erfolg: E-Mail wurde versendet
      } else {
        alert(data.error);  // Fehler vom Server (z.B. "E-Mail nicht gefunden")
      }
    })
    .catch((err) => {
      // Netzwerkfehler oder unerwartete Probleme
      console.error("Error:", err);
      alert("Something went wrong.");
    });
}
