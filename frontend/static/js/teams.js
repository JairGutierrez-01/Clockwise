 document.getElementById('addMemberBtn').addEventListener('click', function () {
  const name = prompt('Name des neuen Mitglieds:');
  const role = prompt('Rolle:');
  if (name && role) alert(`Würde ${name} als ${role} hinzufügen.`);
});

document.getElementById('deleteMemberBtn').addEventListener('click', function () {
  const name = prompt('Welches Mitglied löschen?');
  if (name) alert(`Würde ${name} löschen.`);
});

document.getElementById('chooseProjectBtn').addEventListener('click', function () {
  const project = prompt('Projektname:');
  if (project) alert(`Würde zu Projekt "${project}" wechseln.`);
});
