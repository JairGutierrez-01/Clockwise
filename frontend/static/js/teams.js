;const wrapper = document.querySelector(".carousel-wrapper");
const track = document.querySelector(".carousel-track");

let isDown = false;
let startX;
let currentTranslateXAtDragStart = 0;
let cardWidth = 0;
let gap = 0;
let cardWidthWithGap = 0;

// SENSITIVITY ADJUSTMENTS
const DRAG_SENSITIVITY = 2.0; // Multiplier for drag movement (1.0 = normal, <1.0 = less sensitive, >1.0 = more sensitive)
const SNAP_THRESHOLD_PERCENTAGE = 0.2; // Percentage of cardWidthWithGap to trigger a snap (e.g., 0.1 = 10% of card width)

document.addEventListener("DOMContentLoaded", () => {
  const card = track.querySelector(".member-team-card");
  if (card) {
    cardWidth = card.offsetWidth;

    const trackStyle = window.getComputedStyle(track);
    gap = parseFloat(trackStyle.gap);

    cardWidthWithGap = cardWidth + gap;
  }
});

function getTranslateX(el) {
  const style = window.getComputedStyle(el);
  const matrix = new DOMMatrixReadOnly(style.transform);
  return matrix.m41;
}

wrapper.addEventListener("mousedown", (e) => {
  isDown = true;
  wrapper.classList.add("active");
  startX = e.pageX;
  currentTranslateXAtDragStart = getTranslateX(track);
});

wrapper.addEventListener("mouseup", () => {
  if (!isDown) return;
  isDown = false;
  wrapper.classList.remove("active");

  const currentTranslateX = getTranslateX(track);
  const movedDistance = currentTranslateX - currentTranslateXAtDragStart;

  let targetIndex = Math.round(-currentTranslateX / cardWidthWithGap);

  const snapThresholdPx = cardWidthWithGap * SNAP_THRESHOLD_PERCENTAGE;

  if (movedDistance > snapThresholdPx) {
    targetIndex--;
  } else if (movedDistance < -snapThresholdPx) {
    targetIndex++;
  }

  const maxIndex = track.children.length - 1;
  const clampedIndex = Math.max(0, Math.min(targetIndex, maxIndex));

  track.style.transition = "transform 0.3s ease-out";
  track.style.transform = `translateX(-${clampedIndex * cardWidthWithGap}px)`;

  currentTranslateXAtDragStart = -clampedIndex * cardWidthWithGap;

  setTimeout(() => {
    track.style.transition = "";
  }, 300);
});

wrapper.addEventListener("mouseleave", () => {
  if (isDown) {
    wrapper.dispatchEvent(new Event("mouseup"));
  }
});

wrapper.addEventListener("mousemove", (e) => {
  if (!isDown) return;
  e.preventDefault();

  const x = e.pageX;
  let walk = (x - startX) * DRAG_SENSITIVITY;

  let newTranslateX = currentTranslateXAtDragStart + walk;

  const totalTrackContentWidth = track.scrollWidth;
  const wrapperVisibleWidth = wrapper.offsetWidth;

  const maxAllowedTranslateX = 0;
  const minAllowedTranslateX = wrapperVisibleWidth - totalTrackContentWidth;

  newTranslateX = Math.max(newTranslateX, minAllowedTranslateX);
  newTranslateX = Math.min(newTranslateX, maxAllowedTranslateX);

  track.style.transform = `translateX(${newTranslateX}px)`;
});
