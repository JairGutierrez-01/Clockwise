
//carousel effect
const wrapper = document.querySelector(".carousel-wrapper");
const track = document.querySelector(".carousel-track");
const leftArrow = document.querySelector(".carousel-arrow.left"); // NEW
const rightArrow = document.querySelector(".carousel-arrow.right"); // NEW

let isDown = false;
let startX;
let currentTranslateXAtDragStart = 0;
let cardWidth = 0;
let gap = 0;
let cardWidthWithGap = 0;
let currentCardIndex = 0; // NEW: Keep track of current card index

const DRAG_SENSITIVITY = 2.5; //sensibility
const SNAP_THRESHOLD_PERCENTAGE = 0.2;

document.addEventListener("DOMContentLoaded", () => {
  const card = track.querySelector(".member-team-card");
  if (card) {
    cardWidth = card.offsetWidth;
    const trackStyle = window.getComputedStyle(track);
    gap = parseFloat(trackStyle.gap);
    cardWidthWithGap = cardWidth + gap;
  }
  updateCarouselArrows(); // NEW: Call on load to set initial arrow visibility
});

function getTranslateX(el) {
  const style = window.getComputedStyle(el);
  const matrix = new DOMMatrixReadOnly(style.transform);
  return matrix.m41;
}

function updateCarouselPosition(index) { // NEW: Function to animate carousel to an index
    currentCardIndex = Math.max(0, Math.min(index, track.children.length - 1));

    track.style.transition = "transform 0.3s ease-out";
    track.style.transform = `translateX(-${currentCardIndex * cardWidthWithGap}px)`;

    currentTranslateXAtDragStart = -currentCardIndex * cardWidthWithGap; // Update for future drags

    setTimeout(() => {
        track.style.transition = ""; // Remove transition after animation
        updateCarouselArrows(); // Update arrows after position settles
    }, 300);
}

// NEW: Function to show/hide arrows
function updateCarouselArrows() {
    const maxIndex = track.children.length - 1;

    // Left arrow
    if (currentCardIndex > 0) {
        leftArrow.classList.add("visible");
    } else {
        leftArrow.classList.remove("visible");
    }

    // Right arrow
    if (currentCardIndex < maxIndex) {
        rightArrow.classList.add("visible");
    } else {
        rightArrow.classList.remove("visible");
    }
}

// NEW: Click handlers for arrows
leftArrow.addEventListener("click", () => {
    if (!isDown) { // Prevent clicking during a drag
        updateCarouselPosition(currentCardIndex - 1);
    }
});

rightArrow.addEventListener("click", () => {
    if (!isDown) { // Prevent clicking during a drag
        updateCarouselPosition(currentCardIndex + 1);
    }
});

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

  // Determine target index based on snap threshold
  let targetIndex = Math.round(-currentTranslateX / cardWidthWithGap);
  const snapThresholdPx = cardWidthWithGap * SNAP_THRESHOLD_PERCENTAGE;

  if (movedDistance > snapThresholdPx) { // Dragged right significantly
    targetIndex = currentCardIndex - 1;
  } else if (movedDistance < -snapThresholdPx) { // Dragged left significantly
    targetIndex = currentCardIndex + 1;
  } else { // Slight drag, snap back to current or nearest if very close
    targetIndex = currentCardIndex; // Snap back to where it was
  }


  // Clamp target index to valid range
  const maxIndex = track.children.length - 1;
  const clampedIndex = Math.max(0, Math.min(targetIndex, maxIndex));

  // Update position using the new function
  updateCarouselPosition(clampedIndex);
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

  // Calculate bounds based on track width vs wrapper width
  const totalTrackContentWidth = track.scrollWidth;
  const wrapperVisibleWidth = wrapper.offsetWidth;

  const maxAllowedTranslateX = 0; // Cannot drag past the first card to the right
  const minAllowedTranslateX = wrapperVisibleWidth - totalTrackContentWidth; // Cannot drag past the last card to the left

  newTranslateX = Math.max(newTranslateX, minAllowedTranslateX);
  newTranslateX = Math.min(newTranslateX, maxAllowedTranslateX);

  track.style.transform = `translateX(${newTranslateX}px)`;
});
//ends carousel effect