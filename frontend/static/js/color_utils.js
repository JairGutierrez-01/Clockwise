/**
 * Farbpalette für die Projektfarbenzuweisung im Säulendiagramm.
 * @type {string[]}
 */
const colorPalette = [
  "#00ff7f",
  "#b700ff",
  "#00f8dc",
  "#ff6b00",
  "#5a4132",
  "#0bd800",
  "#f032e6",
  "#f8ff00",
  "#c59595",
  "#008080",
  "#765595",
  "#ffc200",
  "#800000",
  "#64ac79",
  "#808000",
  "#0048ba",
  "#f1136f",
  "#ff2600",
  "#00cdfb",
  "#beff00",
];

/**
 * Gibt eine zu einem Projektnamen gehörende Farbe zurück.
 * @param {string} projectName - Name des Projekts.
 * @returns {string} - Hex-Farbwert.
 */
export function getColorForProject(projectName) {
  let hash = 0;
  const full = projectName + "_hash";
  for (let i = 0; i < full.length; i++) {
    hash = full.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % colorPalette.length;
  return colorPalette[index];
}

/**
 * Konvertiert eine hexadezimale Farbe in ein RGB-Objekt (um verschiedene Helligkeiten einer Farbe für die Tasks eines Projekts zu verwenden).
 * @param {string} hex - Farbwert in hex-Notation (z.B. "#ff0000")
 * @returns {{r: number, g: number, b: number}} - Die RGB-Werte.
 */
export function hexToRgb(hex) {
  // Entferne das "#" falls vorhanden
  hex = hex.replace(/^#/, "");
  if (hex.length === 3) {
    hex = hex
      .split("")
      .map((c) => c + c)
      .join("");
  }
  const bigint = parseInt(hex, 16);
  return {
    r: (bigint >> 16) & 255,
    g: (bigint >> 8) & 255,
    b: bigint & 255,
  };
}

/**
 * Wandelt RGB-Werte in HSL um.
 * @param {number} r - Rotwert (0–255)
 * @param {number} g - Grünwert (0–255)
 * @param {number} b - Blauwert (0–255)
 * @returns {[number, number, number]} - HSL als [Hue, Saturation, Lightness]
 */
export function rgbToHsl(r, g, b) {
  r /= 255;
  g /= 255;
  b /= 255;

  const max = Math.max(r, g, b),
    min = Math.min(r, g, b);
  let h,
    s,
    l = (max + min) / 2;

  if (max === min) {
    h = s = 0; // Grau
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      case b:
        h = (r - g) / d + 4;
        break;
    }
    h /= 6;
  }

  return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
}

/**
 * Gibt eine abgestufte HSL-Farbe für eine Task innerhalb eines Projekts zurück.
 * @param {string} project - Projektname.
 * @param {string} task - Taskname.
 * @param {number} [indexInStack=0] - Position der Task im Stapel.
 * @param {number} [total=1] - Gesamtanzahl der Tasks.
 * @returns {string} - Farbwert im HSL-Format.
 */
export function getTaskColor(project, task, indexInStack = 0, total = 1) {
  const baseColor = getColorForProject(project);
  const rgb = hexToRgb(baseColor);
  let [h, s, l] = rgbToHsl(rgb.r, rgb.g, rgb.b);

  // Staffelung: dunkel unten (index = 0), hell oben
  const step = 40 / Math.max(total - 1, 1); // max. 40% Unterschied
  l = Math.min(90, Math.max(10, l - 20 + step * indexInStack));

  return `hsl(${h}, ${s}%, ${l}%)`;
}

/**
 * Passt die Helligkeit einer Hexfarbe um einen Prozentwert an.
 * @param {string} color - Ausgangsfarbe in Hex.
 * @param {number} percent - Prozentuale Veränderung der Helligkeit: negativ = abdunkeln, positiv = aufhellen (-100 bis +100).
 * @returns {string} - Neue Hexfarbe.
 */
export function shadeColor(color, percent) {
  const f = parseInt(color.slice(1), 16),
    t = percent < 0 ? 0 : 255,
    p = Math.abs(percent) / 100,
    R = f >> 16,
    G = (f >> 8) & 0x00ff,
    B = f & 0x0000ff;

  const newColor = (
    0x1000000 +
    (Math.round((t - R) * p) + R) * 0x10000 +
    (Math.round((t - G) * p) + G) * 0x100 +
    (Math.round((t - B) * p) + B)
  )
    .toString(16)
    .slice(1);

  return `#${newColor}`;
}
