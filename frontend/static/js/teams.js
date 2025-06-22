const headers = {
  "Content-Type": "application/json"
};

// Global variables for carousel
let cardWidth = 0;
let gap = 0;
let cardWidthWithGap = 0;
let currentCardIndex = 0; // Keep track of current card index
let currentDisplayedTeamId = null; // To store the ID of the currently displayed team
let allTeamsData = []; // Global storage of all team data, needed for task assignment lookup
let allProjectsData = []; // Store all projects to map team -> project_id

// Global variables to store the logged-in user's ID and username
let currentLoggedInUserId = null;
let currentLoggedInUsername = "Guest"; // Default to Guest until fetched

// Carousel elements
const wrapper = document.querySelector(".carousel-wrapper");
const track = document.querySelector(".carousel-track");
const leftArrow = document.querySelector(".carousel-arrow.left");
const rightArrow = document.querySelector(".carousel-arrow.right");

let isDown = false;
let startX;
let currentTranslateXAtDragStart = 0;

const DRAG_SENSITIVITY = 2.5; // sensibility
const SNAP_THRESHOLD_PERCENTAGE = 0.2;

// Custom Modal Elements (get references once DOM is loaded)
let customModal, customModalTitle, customModalMessage, customModalInput,
    customModalConfirmBtn, customModalCancelBtn, customModalContent;

let customModalResolve; // To store the resolve function for promises

// Global variable for the dynamic content area inside the modal
let dynamicContentArea;

// New global variable for delete mode
let isDeleteMode = false;
let deleteMemberButton = null; // Reference to the delete member button

// Custom Modal Functions
function initializeModalElements() {
  customModal = document.getElementById("customModal");
  customModalTitle = document.getElementById("customModalTitle");
  customModalMessage = document.getElementById("customModalMessage");
  customModalInput = document.getElementById("customModalInput");
  customModalConfirmBtn = document.getElementById("customModalConfirmBtn");
  customModalCancelBtn = document.getElementById("customModalCancelBtn");
  customModalContent = customModal.querySelector(".custom-modal-content");
  // NEW: Initialize dynamicContentArea
  dynamicContentArea = customModal.querySelector(".dynamic-content-area");
}

// showCustomModal to accept customContentHtml and manage default elements' visibility
function showCustomModal({ title, message = '', inputPlaceholder = '', confirmText = 'OK', cancelText = 'Cancel', type = 'alert', onConfirm = null, onCancel = null, customContentHtml = '' }) {
  return new Promise(resolve => {
    customModalResolve = resolve;

    customModalTitle.textContent = title;
    customModalMessage.textContent = message;

    // Reset input value
    customModalInput.value = '';

    // Inject custom content or clear if not provided
    if (dynamicContentArea) {
        dynamicContentArea.innerHTML = customContentHtml;
    }

    // Manage visibility of standard modal elements based on whether custom content is provided
    if (customContentHtml) {
        customModalInput.style.display = 'none';
        customModalMessage.style.display = 'none'; // Hide default message
        customModalConfirmBtn.style.display = 'none'; // Hide default confirm button
        customModalCancelBtn.style.display = 'none'; // Hide default cancel button
        customModalTitle.style.display = 'none'; // Hide default title if custom content has its own header
    } else {
        customModalInput.style.display = inputPlaceholder ? 'block' : 'none';
        customModalInput.placeholder = inputPlaceholder; // Set placeholder only if input is shown

        customModalMessage.style.display = 'block'; // Show default message
        customModalConfirmBtn.style.display = 'inline-block'; // Show default confirm
        customModalConfirmBtn.textContent = confirmText; // Set text for default confirm
        customModalCancelBtn.style.display = cancelText ? 'inline-block' : 'none'; // Show default cancel
        customModalCancelBtn.textContent = cancelText; // Set text for default cancel
        customModalTitle.style.display = 'block'; // Show default title
    }

    // Set modal type class for CSS styling
    customModal.classList.remove('prompt-type', 'alert-type', 'confirm-type');
    customModal.classList.add(`${type}-type`);

    // Add success/error class to content for color changes
    if (customModalContent) {
        customModalContent.classList.remove('success', 'error');
        if (type === 'alert' && title.includes('Success')) {
            customModalContent.classList.add('success');
        } else if (type === 'alert' && title.includes('Error')) {
            customModalContent.classList.add('error');
        }
    }

    // Define handlers for default buttons (used when customContentHtml is NOT present)
    const handleConfirmDefault = () => {
      hideCustomModal();
      resolve(inputPlaceholder ? customModalInput.value : true);
      removeDefaultListeners();
    };

    const handleCancelDefault = () => {
      hideCustomModal();
      resolve(false);
      removeDefaultListeners();
    };

    const handleKeydownDefault = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (customModalConfirmBtn.style.display !== 'none') { // Only trigger if confirm button is visible
          handleConfirmDefault();
        }
      } else if (e.key === 'Escape' && customModalCancelBtn.style.display !== 'none') { // Only trigger if cancel button is visible
        e.preventDefault();
        handleCancelDefault();
      }
    };

    // Function to remove default event listeners to prevent memory leaks
    const removeDefaultListeners = () => {
      customModalConfirmBtn.removeEventListener('click', handleConfirmDefault);
      customModalCancelBtn.removeEventListener('click', handleCancelDefault);
      document.removeEventListener('keydown', handleKeydownDefault);
    };

    // Clear previous default listeners before attaching new ones
    removeDefaultListeners();

    // Attach default listeners only if no custom content is provided
    if (!customContentHtml) {
      customModalConfirmBtn.addEventListener('click', handleConfirmDefault);
      customModalCancelBtn.addEventListener('click', handleCancelDefault);
      document.addEventListener('keydown', handleKeydownDefault);
    }

    customModal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Disable scrolling

    // Focus management
    if (customContentHtml) {
        // For custom content, attempt to focus the first focusable element inside dynamicContentArea
        setTimeout(() => {
            const firstFocusable = dynamicContentArea.querySelector('input, button, a, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            } else {
                // Fallback to customModalConfirmBtn if no focusable elements in custom content and it's visible
                if (customModalConfirmBtn.style.display !== 'none') {
                    customModalConfirmBtn.focus();
                }
            }
        }, 300);
    } else if (inputPlaceholder && customModalInput.style.display !== 'none') {
        setTimeout(() => customModalInput.focus(), 300);
    } else if (customModalConfirmBtn.style.display !== 'none') {
        setTimeout(() => customModalConfirmBtn.focus(), 300);
    }
  });
}

// hideCustomModal to clear dynamic content
function hideCustomModal() {
  customModal.classList.remove('active');
  document.body.style.overflow = ''; // Re-enable scrolling
  if (customModalContent) {
      customModalContent.classList.remove('success', 'error'); // Clean up type classes
  }
  if (dynamicContentArea) { // Clear dynamic content when hiding
      dynamicContentArea.innerHTML = '';
  }
  // Ensure default modal elements are in a consistent hidden state after clearing custom content
  customModalInput.style.display = 'none';
  customModalMessage.style.display = 'block'; // Default to visible for next standard modal call
  customModalTitle.style.display = 'block'; // Default to visible
  customModalConfirmBtn.style.display = 'inline-block'; // Default to visible (will be hidden by next showCustomModal if needed)
  customModalCancelBtn.style.display = 'inline-block'; // Default to visible
}

// Wrapper functions for convenience (remain unchanged)
function showCustomPrompt(title, message, placeholder) {
  return showCustomModal({title, message, inputPlaceholder: placeholder, confirmText: 'Submit', cancelText: 'Cancel', type: 'prompt'});
}

function showCustomAlert(title, message, type = 'alert') {
  return showCustomModal({title, message, confirmText: 'OK', type: 'alert'});
}

function showCustomConfirm(title, message) {
  return showCustomModal({title, message, confirmText: 'Confirm', cancelText: 'Cancel', type: 'confirm'});
}


document.addEventListener("DOMContentLoaded", () => {
  initializeModalElements(); // Initialize modal elements after DOM is loaded
  fetchUserTeams(); // Initial team load and then carousel setup
  fetchAllProjects();

  //Team Management Buttons
  const createTeamBtn = document.querySelector(".create-team-btn");
  const addMemberBtn = document.querySelector(".add-member-btn");
  deleteMemberButton = document.querySelector(".delete-member-btn"); // Assign to global variable
  const deleteTeamBtn = document.querySelector(".delete-team-btn");

  // Add event listener for team table rows to open the modal for project assignment
  let teamsTableBody = document.getElementById("teamsBody");

  if (teamsTableBody) {
      teamsTableBody.addEventListener("click", async (event) => {
          const row = event.target.closest("tr");
          if (!row || !row.dataset.teamId) return;

          const teamId = row.dataset.teamId;
          const teamName = row.dataset.teamName;

          // Show loading state initially within the modal
          const loadingHtml = `
              <div class="modal-header">
                  <h3 id="modalDynamicTitle">Assign Project to <strong>${teamName}</strong></h3>
                  <button class="modal-close-btn">X</button>
              </div>
              <div class="modal-content-area">
                  <p style="text-align: center; color: var(--text-muted);">Loading projects...</p>
              </div>
          `;

          // Pass custom content to showCustomModal
          showCustomModal({
              title: `Assign Project to ${teamName}`, // Default title for general modal tracking if needed
              customContentHtml: loadingHtml,
              type: 'custom' // Use a generic 'custom' type to indicate it's not a standard alert/prompt
          });

          // Attach close button listener immediately after showing modal with loading content
          // This listener needs to be re-attached each time the custom content is updated
          const modalCloseBtn = customModal.querySelector('.modal-close-btn');
          if (modalCloseBtn) {
              modalCloseBtn.addEventListener('click', hideCustomModal);
          }

          try {
              const response = await fetch("/api/projects");
              const result = await response.json();
              allProjectsData = result.projects || [];

              if (!result.projects || !Array.isArray(result.projects)) {
                  // Update content area with error message
                  if (dynamicContentArea) {
                      dynamicContentArea.querySelector('.modal-content-area').innerHTML = "<p>Error loading projects.</p>";
                  }
                  return;
              }

              const allTeamProjects = result.projects.filter(p => p.type === "TeamProject");

              const assignedProjects = allTeamProjects.filter(p => p.team_id == teamId);
              const availableProjects = allTeamProjects.filter(p => !p.team_id);

              let html = `
                  <div class="modal-header">
                      <h3 id="modalDynamicTitle">Assign Project to <strong>${teamName}</strong></h3>
                      <button class="modal-close-btn">X</button>
                  </div>
                  <div class="modal-content-area">
              `;

              if (assignedProjects.length > 0) {
                  html += "<p><strong>Already Assigned:</strong></p><ul class='modal-assign-members-list'>"; // Reusing list style
                  assignedProjects.forEach(p => {
                      html += `<li>${p.name}</li>`;
                  });
                  html += "</ul>";
              }

              if (availableProjects.length > 0) {
                  html += "<p><strong>Available to Assign:</strong></p><ul class='modal-assign-members-list'>";
                  availableProjects.forEach(p => {
                      html += `
                          <li>
                              <span>${p.name}</span>
                              <button class="assign-project-btn assign-button" data-project-id="${p.project_id}" data-team-id="${teamId}">Assign</button>
                          </li>
                      `;
                  });
                  html += "</ul>";
              } else {
                  html += "<p>No available projects to assign.</p>";
              }

              html += `</div>`; // Close modal-content-area div

              // Update the modal's content with the fetched project data
              if (dynamicContentArea) {
                  dynamicContentArea.innerHTML = html;
              }

              // Re-attach close button listener (important because innerHTML overwrites it)
              const updatedModalCloseBtn = customModal.querySelector('.modal-close-btn');
              if (updatedModalCloseBtn) {
                  updatedModalCloseBtn.addEventListener('click', hideCustomModal);
              }

              // Attach event listener for the new "Assign" buttons
              if (dynamicContentArea) { // Check if dynamicContentArea exists before querying
                  dynamicContentArea.querySelectorAll(".assign-project-btn").forEach(button => {
                      button.addEventListener("click", handleAssignProject);
                  });
              }

          } catch (err) {
              console.error(err);
              if (dynamicContentArea) { // Check if dynamicContentArea exists before querying
                  dynamicContentArea.innerHTML = `
                      <div class="modal-header">
                          <h3 id="modalDynamicTitle">Error</h3>
                          <button class="modal-close-btn">X</button>
                      </div>
                      <div class="modal-content-area">
                          <p style="text-align: center; color: var(--delete-color);">Failed to fetch projects.</p>
                      </div>
                  `;
                  const errorModalCloseBtn = customModal.querySelector('.modal-close-btn');
                  if (errorModalCloseBtn) {
                      errorModalCloseBtn.addEventListener('click', hideCustomModal);
                  }
              }
          }
      });
  }

  // Separate function for handling project assignment (previously embedded in popover listener)
  async function handleAssignProject(e) {
      const projectId = e.target.dataset.projectId;
      const teamId = e.target.dataset.teamId;

      // Get teamName for re-rendering refreshed modal content if needed
      const teamRow = document.querySelector(`tr[data-team-id="${teamId}"]`);
      const teamName = teamRow ? teamRow.dataset.teamName : "";

      try {
          const response = await fetch(`/api/teams/${teamId}/assign_project`, {
              method: "POST",
              headers,
              body: JSON.stringify({ project_id: projectId }),
          });

          const result = await response.json();

          if (response.ok) {
              showCustomAlert("Success!", "Project assigned successfully!", "success");
              hideCustomModal(); // Close the modal after successful assignment
              fetchUserTeams(); // This will refresh everything
          } else {
              const errorMessage = result.error || "Failed to assign project.";
              showCustomAlert("Error", errorMessage, "error");
          }
      } catch (err) {
          console.error("Error assigning project:", err);
          showCustomAlert("Error", "Network error. Error assigning project.", "error");
      }
  }


  // createTeamBtn listener to use customContentHtml
  if (createTeamBtn) {
    createTeamBtn.addEventListener("click", async () => {
      const createTeamFormHtml = `
          <div class="modal-header">
              <h3 id="modalDynamicTitle">Create New Team</h3>
              <button class="modal-close-btn">X</button>
          </div>
          <div class="popover-content">
              <input type="text" id="newTeamName" placeholder="Team Name">
              <textarea id="newTeamDescription" placeholder="Team Description (optional)"></textarea>
              <div class="action-buttons">
                  <button id="createTeamConfirm" class="custom-modal-btn confirm-btn">Create Team</button>
                  <button id="createTeamCancel" class="custom-modal-btn cancel-btn">Cancel</button>
              </div>
          </div>
      `;

      showCustomModal({
          title: 'Create Team', // This will be the fallback title if modalDynamicTitle isn't used
          customContentHtml: createTeamFormHtml,
          type: 'custom' // Indicate it's a custom content modal
      });

      // Attach listeners to dynamically created elements
      const newTeamNameInput = document.getElementById('newTeamName');
      const newTeamDescriptionInput = document.getElementById('newTeamDescription');
      const createTeamConfirm = document.getElementById('createTeamConfirm');
      const createTeamCancel = document.getElementById('createTeamCancel');
      const modalCloseBtn = customModal.querySelector('.modal-close-btn'); // Get the close button

      // Focus on the input
      if (newTeamNameInput) {
          setTimeout(() => newTeamNameInput.focus(), 300);
      }

      createTeamConfirm.onclick = async () => {
          const teamName = newTeamNameInput.value.trim();
          const teamDescription = newTeamDescriptionInput.value.trim();

          if (!teamName) {
              showCustomAlert("Error", "Team name is required.", "error");
              return; // Don't hide modal, let user fix
          }

          try {
              const response = await fetch("/api/teams/", {
                  method: "POST",
                  headers: headers,
                  body: JSON.stringify({ name: teamName, description: teamDescription }), // Include description
                  credentials: "include"
              });

              const data = await response.json();

              if (response.ok) {
                  showCustomAlert("Success!", `Team "${teamName}" created successfully!`, "success");
                  hideCustomModal(); // Hide modal after success
                  fetchUserTeams();
              } else {
                  showCustomAlert("Error", "Error: " + (data.error || "Unknown error"), "error");
              }
          } catch (err) {
              console.error("Error at creating the Team:", err);
              showCustomAlert("Error", "Network error. Please try again.", "error");
          }
      };

      createTeamCancel.onclick = hideCustomModal;
      if (modalCloseBtn) { // Attach to the 'X' button
          modalCloseBtn.onclick = hideCustomModal;
      }
    });
  }

  // deleteTeamBtn listener (no custom HTML, uses standard confirm)
  if (deleteTeamBtn) {
    deleteTeamBtn.addEventListener("click", async () => {
      if (!currentDisplayedTeamId) {
        showCustomAlert("Error", "Please select a team first.", "error");
        return;
      }

      const confirmDelete = await showCustomConfirm("Delete Team", "Are you sure you want to delete this team? This action cannot be undone.");
      if (!confirmDelete) return;

      try {
        const response = await fetch(`/api/teams/${currentDisplayedTeamId}`, {
          method: "DELETE",
          headers: headers,
          credentials: "include"
        });

        const data = await response.json();

        if (response.ok) {
          showCustomAlert("Success!", "Team deleted successfully!", "success");
          fetchUserTeams(); // Refresh
        } else {
          showCustomAlert("Error", "Error deleting team: " + (data.error || "Unknown error"), "error");
        }
      } catch (err) {
        console.error("Network error:", err);
        showCustomAlert("Error", "Network error. Please try again.", "error");
      }
    });
  }

  // Add member button listener to use customContentHtml
  if (addMemberBtn) {
    addMemberBtn.addEventListener("click", async () => {
      if (!currentDisplayedTeamId) {
        showCustomAlert("Error", "Please select a team first.", "error");
        return;
      }

      // Exit delete mode if active before adding
      if (isDeleteMode) {
        toggleDeleteMode();
      }

      const addMemberFormHtml = `
          <div class="modal-header">
              <h3 id="modalDynamicTitle">Add New Member</h3>
              <button class="modal-close-btn">X</button>
          </div>
          <div class="popover-content">
              <p style="color: var(--text-muted); text-align: center;">Enter new member's Username and Role:</p>
              <input type="text" id="memberIdentifierInput" placeholder="Username">
              <input type="text" id="memberRoleInput" placeholder="Role (member, admin, default: member)">
              <div class="action-buttons">
                  <button id="addMemberConfirm" class="custom-modal-btn confirm-btn">Add Member</button>
                  <button id="addMemberCancel" class="custom-modal-btn cancel-btn">Cancel</button>
              </div>
          </div>
      `;

      showCustomModal({
          title: 'Add New Member',
          customContentHtml: addMemberFormHtml,
          type: 'custom'
      });

      // Attach listeners to dynamically created elements
      const memberIdentifierInput = document.getElementById('memberIdentifierInput');
      const memberRoleInput = document.getElementById('memberRoleInput');
      const addMemberConfirm = document.getElementById('addMemberConfirm');
      const addMemberCancel = document.getElementById('addMemberCancel');
      const modalCloseBtn = customModal.querySelector('.modal-close-btn');

      if (memberIdentifierInput) {
          setTimeout(() => memberIdentifierInput.focus(), 300);
      }

      addMemberConfirm.onclick = async () => {
          const newMemberIdentifier = memberIdentifierInput.value.trim();
          const role = memberRoleInput.value.trim() || 'member'; // Default to 'member' if not specified

          if (!newMemberIdentifier) {
              showCustomAlert("Error", "Username is required.", "error");
              return;
          }

          if (!isNaN(newMemberIdentifier)) {
              showCustomAlert("Error", "Only usernames are allowed.", "error");
              return;
          }

          try {
              // Send newMemberIdentifier as user_id to the backend, which handles ID or username
              const response = await fetch(`/api/teams/${currentDisplayedTeamId}/add-member`, {
                  method: "PATCH",
                  headers: headers,
                  body: JSON.stringify({ user_id: newMemberIdentifier, role: role }),
                  credentials: "include"
              });

              const data = await response.json();

              if (response.ok) {
                  if (data.error) {
                    showCustomAlert("Error", "Error adding member: " + data.error, "error");
                  } else {
                    showCustomAlert("Success!", "Member added successfully!", "success");
                    hideCustomModal();
                    fetchUserTeams(); // Re-fetch all teams to update the carousel
                  }
              } else {
                  showCustomAlert("Error", "Error adding member: " + (data.error || "Unknown error"), "error");
              }
          } catch (err) {
              console.error("Error adding member:", err);
              showCustomAlert("Error", "Network error. Please try again.", "error");
          }
      };

      addMemberCancel.onclick = hideCustomModal;
      if (modalCloseBtn) {
          modalCloseBtn.onclick = hideCustomModal;
      }
    });
  }

  // Toggle delete mode listener (remains unchanged, it's specific to the carousel)
  if (deleteMemberButton) {
    deleteMemberButton.addEventListener("click", () => {
      if (!currentDisplayedTeamId) {
        showCustomAlert("Error", "Please select a team first.", "error");
        return;
      }
      toggleDeleteMode();
    });
  }

  // Carousel Event Listeners (remain unchanged)
  if (leftArrow) {
    leftArrow.addEventListener("click", () => {
      if (!isDown) { // Prevent clicking during a drag
        if (isDeleteMode) toggleDeleteMode(); // Exit delete mode on carousel navigation
        updateCarouselPosition(currentCardIndex - 1);
      }
    });
  }

  if (rightArrow) {
    rightArrow.addEventListener("click", () => {
      if (!isDown) { // Prevent clicking during a drag
        if (isDeleteMode) toggleDeleteMode(); // Exit delete mode on carousel navigation
        updateCarouselPosition(currentCardIndex + 1);
      }
    });
  }

  // Carousel drag event listeners (remain unchanged)
  if (wrapper && track) {
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

      let targetIndex;

      // Determine target index based on snap threshold
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
        wrapper.dispatchEvent(new Event("mouseup")); // Trigger mouseup if dragging ends on mouseleave
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

      const maxAllowedTranslateX = 0; // Cannot drag past the first card to the right (0px translate)
      const minAllowedTranslateX = -(totalTrackContentWidth - wrapperVisibleWidth);


      // Clamp the newTranslateX within the valid range
      newTranslateX = Math.max(newTranslateX, minAllowedTranslateX);
      newTranslateX = Math.min(newTranslateX, maxAllowedTranslateX);


      track.style.transform = `translateX(${newTranslateX}px)`;
    });
  }

  // Add Escape key listener to exit delete mode (remains unchanged)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isDeleteMode) {
      toggleDeleteMode();
    }
  });
});


// Function to toggle delete mode (remains unchanged)
function toggleDeleteMode() {
  isDeleteMode = !isDeleteMode;
  const memberItems = document.querySelectorAll(".member-item");

  if (isDeleteMode) {
    deleteMemberButton.textContent = "Done";
    deleteMemberButton.classList.add("delete-mode-active");
    memberItems.forEach(item => {
      item.classList.add("shake-animation");
      // Add click listener for deletion
      item.addEventListener("click", handleMemberDeleteClick);
    });
  } else {
    deleteMemberButton.textContent = "Delete Member";
    deleteMemberButton.classList.remove("delete-mode-active");
    memberItems.forEach(item => {
      item.classList.remove("shake-animation");
      // Remove click listener
      item.removeEventListener("click", handleMemberDeleteClick);
    });
  }
}

// Handler for clicking a member in delete mode (remains unchanged)
async function handleMemberDeleteClick(event) {
  if (!isDeleteMode) return; // Only proceed if in delete mode

  const memberItem = event.currentTarget;
  const userIdToDelete = memberItem.dataset.userId;
  const usernameToDelete = memberItem.querySelector(".member-name").textContent; // Get username for confirmation

  if (!userIdToDelete || !currentDisplayedTeamId) {
    showCustomAlert("Error", "Could not identify member or team.", "error");
    return;
  }

  const confirmDelete = await showCustomConfirm(
    "Remove Member",
    `Are you sure you want to remove "${usernameToDelete}" from this team?`
  );

  if (!confirmDelete) {
    return; // User cancelled
  }

  try {
    const response = await fetch(`/api/teams/${currentDisplayedTeamId}/remove-member`, {
      method: "PATCH",
      headers: headers,
      body: JSON.stringify({ user_id: userIdToDelete }), // Send the user ID from the data attribute
      credentials: "include"
    });

    const data = await response.json();

    if (response.ok) {
      if (data.error) {
        showCustomAlert("Error", "Error removing member: " + data.error, "error");
      } else {
        showCustomAlert("Success!", "Member removed successfully!", "success");
        fetchUserTeams(); // Re-fetch all teams to update the carousel
        toggleDeleteMode(); // Exit delete mode after successful deletion
      }
    } else {
      showCustomAlert("Error", "Error removing member: " + (data.error || "Unknown error"), "error");
    }
  } catch (err) {
    console.error("Error removing member:", err);
    showCustomAlert("Error", "Network error. Please try again.", "error");
  }
}


async function fetchUserTeams() {
  try {
    const response = await fetch("/api/teams/", {
      method: "GET",
      headers: headers,
      credentials: "include" // important for FLASK login
    });

    const responseData = await response.json();

    if (response.ok) {

      if (responseData.current_user) {
        currentLoggedInUserId = responseData.current_user.user_id;
        currentLoggedInUsername = responseData.current_user.username;
        console.log(`Logged in as: ${currentLoggedInUsername} (ID: ${currentLoggedInUserId})`);
      } else {
        console.warn("Current user data not found in /api/teams/ response. Displaying 'Guest'.");
        currentLoggedInUserId = null;
        currentLoggedInUsername = "Guest";
      }

      const teamsData = responseData.teams || []; // Get the teams array

      console.log("Teams received:", teamsData);

      // Fetch members for each team and their usernames
      const teamsWithMembersPromises = teamsData.map(async (team) => {
        try {
          const membersResponse = await fetch(`/api/teams/${team.team_id}/members`, {
            method: "GET",
            headers: headers,
            credentials: "include"
          });
          const membersData = await membersResponse.json();

          // Check if membersResponse was successful and membersData is an array
          if (!membersResponse.ok) {
            console.error(`Error fetching members for team ${team.team_id}:`, membersData.error || "Unknown error");
            return { ...team, members: [] }; // Return team with empty members on backend error
          }
          if (!Array.isArray(membersData)) {
            console.error(`Unexpected members data format for team ${team.team_id}:`, membersData);
            return { ...team, members: [] }; // Ensure membersData is an array
          }


          const membersWithUsernames = await Promise.all(membersData.map(async (member) => {
            let username = `${member.user_id}`; // Fallback: Use User ID if username can't be fetched
            // Check if the member is the current logged-in user
            if (currentLoggedInUserId && member.user_id === currentLoggedInUserId) {
                username = currentLoggedInUsername;
            } else {
                // Fetch actual username from the CORRECTED dedicated user endpoint
                try {
                  const userDetailsResponse = await fetch(`/api/teams/users/${member.user_id}`, { // <-- CHANGED THIS LINE
                    method: "GET",
                    headers: headers,
                    credentials: "include"
                  });
                  const userDetails = await userDetailsResponse.json();
                  if (userDetailsResponse.ok && userDetails.username) {
                    username = userDetails.username;
                  } else {
                    console.warn(`Could not fetch username for user ID: ${member.user_id}. Response:`, userDetails);
                  }
                } catch (userErr) {
                  console.error(`Error fetching user details for ID ${member.user_id}:`, userErr);
                }
            }
            return { ...member, username: username };
          }));

          return { ...team, members: membersWithUsernames };
        } catch (memberErr) {
          console.error(`Error fetching members for team ${team.team_id}:`, memberErr);
          return { ...team, members: [] }; // Return team with empty members array on error
        }
      });

      const teamsWithMembers = await Promise.all(teamsWithMembersPromises);
      console.log("Final teamsWithMembers data:", teamsWithMembers);
      allTeamsData = teamsWithMembers; // Store globally for task lookup later
      renderTeams(teamsData); // Render teams in the table
      renderMembersForTeams(teamsWithMembers); // Render members into carousel
      setupCarousel(); // Setup carousel *after* members are rendered
      renderTeamTasksOverview(); // Render the Tasks Overview card
    } else {
      showCustomAlert("Error", "Error fetching teams: " + (responseData.error || "Unknown error"), "error");
      console.error("Error fetching teams:", responseData.error);
    }
  } catch (err) {
    showCustomAlert("Error", "Network error. Could not load teams.", "error");
    console.error("Network error", err);
  }
}


// Show teams
function renderTeams(teams) {
  const tbody = document.getElementById("teamsBody");
  tbody.innerHTML = "";

  teams.forEach(team => {
    const tr = document.createElement("tr");

    tr.dataset.teamId = team.team_id;
    tr.dataset.teamName = team.team_name;
    tr.innerHTML = `
      <td>${team.team_name}</td>
      <td>${new Date(team.created_at).toLocaleDateString()}</td>
      <td class="${team.role === 'admin' ? 'role-admin' : 'role-member'}">${team.role}</td>
    `;
    tbody.appendChild(tr);
  });
}

//highlight chosen team
function highlightActiveTeamRow(teamId) {
  const allRows = document.querySelectorAll("#teamsBody tr");
  allRows.forEach(row => {
    if (row.dataset.teamId === teamId) {
      row.classList.add("active-team-row");
    } else {
      row.classList.remove("active-team-row");
    }
  });
}


// Show members of the Team
function renderMembersForTeams(teams) {
  const trackElement = document.getElementById("carouselTrack");
  if (!trackElement) return; // Safeguard

  trackElement.innerHTML = "";

  if (teams.length === 0) {
    trackElement.innerHTML = "<p style='text-align: center; color: var(--text-muted); margin-top: 20px;'>No teams available to display members.</p>";
    return;
  }

  teams.forEach(team => {
    const card = document.createElement("div");
    card.className = "member-team-card";
    card.dataset.teamId = team.team_id; // Store team ID on the card

    const members = team.members || [];

    const membersHtml = members.map(member => `
  <div class="member-item" data-user-id="${member.user_id}">
    <div class="member-avatar" style="background-color:${member.role === 'admin' ? '#b18aff' : '#6ec5ff'}"></div>
    <div class="member-info">
      <span class="member-name">${member.username}</span> 
      <span class="member-role ${member.role === 'admin' ? 'admin' : ''}">${member.role}</span>
    </div>
    <button class="assign-options-btn" title="Assign Task" data-user-id="${member.user_id}">⋮</button>
    <span class="delete-icon">✖</span>
  </div>
`).join("");

    // Display current user's role in this team
    const currentUserRoleInThisTeam = team.role;
    const roleDisplay = currentUserRoleInThisTeam === 'admin' ?
      `<span class="role-indicator role-admin">You are Admin</span>` :
      `<span class="role-indicator role-member">You are Member</span>`;

    card.innerHTML = `
      <h3>Team: ${team.team_name}</h3>
      <p class="current-user-team-role">${roleDisplay}</p>
      <div class="members-grid">${membersHtml}</div>
    `;

    trackElement.appendChild(card);
  });

document.addEventListener("click", async function (event) {
  const assignOptionsBtn = event.target.closest(".assign-options-btn");
  if (assignOptionsBtn) {
    const userId = assignOptionsBtn.dataset.userId;
    const teamId = currentDisplayedTeamId;

    try {
        const assignedTasks = await fetchAssignedTaskForUser(userId, teamId); // Get the array of assigned tasks
        showAssignPopover(assignOptionsBtn, assignedTasks, userId);
    } catch (err) {
        console.error("Error fetching assigned task for popover:", err);
        showAssignPopover(assignOptionsBtn, null, userId);
    }
  }

  // The actual action button is inside the popover
  if (event.target.classList.contains("open-assign-modal-btn")) {
    const userId = event.target.dataset.userId;
    const teamId = currentDisplayedTeamId;

    const project = allProjectsData.find(p => p.team_id === Number(teamId));
    if (!project) {
      showCustomAlert("Error", "No project assigned to this team.", "error");
      return;
    }

    const projectId = project.project_id;

    try {
      const response = await fetch(`/api/tasks?project_id=${projectId}`);
      if (!response.ok) throw new Error("Error fetching tasks.");
      const tasks = await response.json(); //array de las tareas

      if (!tasks || tasks.length === 0) {
        showCustomAlert("Info", "No tasks found for this project.", "alert");
        return;
      }

      const availableTasks = tasks.filter(task => {
          return task.user_id === null || task.user_id === undefined;
      });

      if (availableTasks.length === 0) {
          showCustomAlert("Info", "No available tasks to assign for this user.", "alert");
          return;
      }

      const taskListHtml = availableTasks.map(task => `
        <li>
          <button class="assign-task-btn" data-task-id="${task.task_id}" data-user-id="${userId}">
            ${task.title}
          </button>
        </li>`).join("");

      const modalHtml = `
        <div class="modal-header">
          <h3 id="modalDynamicTitle">Assign Task</h3>
          <button class="modal-close-btn">X</button>
        </div>
        <div class="modal-content-area">
          <p>Select a task to assign:</p>
          <ul class="modal-assign-members-list">${taskListHtml}</ul>
        </div>
      `;

      showCustomModal({
        title: "Assign Task",
        customContentHtml: modalHtml,
        type: "custom"
      });

      const closeBtn = customModal.querySelector(".modal-close-btn");
      if (closeBtn) closeBtn.onclick = hideCustomModal;

      dynamicContentArea.querySelectorAll(".assign-task-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const selectedTaskId = btn.dataset.taskId;
        let targetUserId = btn.dataset.userId;

        targetUserId = Number(targetUserId);

        try {
          const assignResponse = await fetch(`/api/tasks/${selectedTaskId}/assign`, {
            method: "PATCH",
            headers,
            body: JSON.stringify({ user_id: targetUserId }),
            credentials: "include"
          });

          const result = await assignResponse.json();

          if (assignResponse.ok) {
            showCustomAlert("Success", "Task assigned successfully!", "success");
            hideCustomModal();
            const memberOptionsButton = document.querySelector(`.assign-options-btn[data-user-id="${targetUserId}"]`);
            if (memberOptionsButton) {
                const updatedTaskInfo = await fetchAssignedTaskForUser(targetUserId, teamId);
                document.querySelectorAll(".assign-popover").forEach(el => el.remove());
                showAssignPopover(memberOptionsButton, updatedTaskInfo, targetUserId);
            }
          } else {
            showCustomAlert("Error", result.error || "Failed to assign task.", "error");
          }
        } catch (err) {
          console.error("Assignment error:", err);
          showCustomAlert("Error", "Network error. Could not assign task.", "error");
        }
      });
    });

    } catch (err) {
      console.error("Error fetching tasks for assignment:", err);
      showCustomAlert("Error", "Could not fetch tasks.", "error");
    }
  }

  // Handle click on "View Tasks" button in the popover
  if (event.target.classList.contains("view-assigned-tasks-btn")) {
    const userId = event.target.dataset.userId;
    const teamId = currentDisplayedTeamId;

    try {
      const assignedTasks = await fetchAssignedTaskForUser(userId, teamId);

      if (!assignedTasks || assignedTasks.length === 0) {
        showCustomAlert("Info", "No tasks currently assigned to this user in this project.", "alert");
        return;
      }

      const taskListHtml = assignedTasks.map(task => `
        <li>
          <div class="assigned-task-item">
            <span class="task-title">${task.title}</span>
            <span class="task-status-display">Status: ${task.status || 'Not Set'}</span>
            </div>
        </li>`).join("");

      const modalHtml = `
        <div class="modal-header">
          <h3 id="modalDynamicTitle">Assigned Tasks</h3>
          <button class="modal-close-btn">X</button>
        </div>
        <div class="modal-content-area">
          <p>Tasks assigned to this member:</p>
          <ul class="modal-assigned-tasks-list">${taskListHtml}</ul>
        </div>
      `;

      showCustomModal({
        title: "Assigned Tasks",
        customContentHtml: modalHtml,
        type: "custom"
      });

      const closeBtn = customModal.querySelector(".modal-close-btn");
      if (closeBtn) closeBtn.onclick = hideCustomModal;

    } catch (err) {
      console.error("Error fetching assigned tasks for view modal:", err);
      showCustomAlert("Error", "Could not fetch assigned tasks.", "error");
    }
    document.querySelectorAll(".assign-popover").forEach(el => el.remove());
  }
});

async function fetchAssignedTaskForUser(userId, teamId) {
    // Find the current team in the global list
    const team = allTeamsData.find(t => t.team_id === Number(teamId));
    if (!team) {
      console.warn("Team not found for teamId:", teamId);
      return []; // Return an empty array if team is not found
    }

    let projectId = team.project_id;

    if (!projectId) {
      const project = allProjectsData.find(p => p.team_id === Number(teamId));
      if (!project) {
        console.warn("No project assigned to team for teamId:", teamId);
        return []; // Return an empty array if no project is assigned
      }
      projectId = project.project_id;
    }

    // Get ALL tasks for the user
    const response = await fetch(`/api/users/${userId}/tasks`);
    if (!response.ok) {
        console.error("Error fetching user's tasks for userId:", userId, "Status:", response.status);
        return []; // Return an empty array if API fetch fails
    }

    const allUserTasks = await response.json();

    // Filter tasks that belong to the currently displayed project
    // Return the array of task objects (empty if none)
    return allUserTasks.filter(t => t.project_id === projectId);
}

function showAssignPopover(buttonElement, assignedTasks, userId) {
  document.querySelectorAll(".assign-popover").forEach(el => el.remove());

  // let statusText = "";
  let showViewTasksButton = false;

  if (assignedTasks && assignedTasks.length > 0) { // Check if there are assigned tasks
      showViewTasksButton = true; // Only show the view tasks button if there are assigned tasks
  }

  const popover = document.createElement("div");
  popover.className = "assign-popover";
  popover.innerHTML = `
    <div class="popover-header">
      <button class="popover-close-btn">X</button>
    </div>
    <button class="open-assign-modal-btn" data-user-id="${userId}">Assign Task</button>
    ${showViewTasksButton ? `<button class="view-assigned-tasks-btn" data-user-id="${userId}">View Tasks</button>` : ''}
  `;

  buttonElement.parentNode.appendChild(popover);

  const closeBtn = popover.querySelector(".popover-close-btn");
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      popover.remove();
    });
  }
}

  // Re-apply shake animation if delete mode is active after re-rendering
  if (isDeleteMode) {
    document.querySelectorAll(".member-item").forEach(item => {
      item.classList.add("shake-animation");
      item.addEventListener("click", handleMemberDeleteClick);
    });
  }
}

// Carousel helper functions (remain unchanged)
function setupCarousel() {
  if (!track || track.children.length === 0) {
    currentCardIndex = 0; // Reset index if no cards
    currentDisplayedTeamId = null; // No team displayed
    updateCarouselArrows();
    return; // No cards to set up carousel for
  }

  const firstCard = track.querySelector(".member-team-card");
  if (firstCard) {
    cardWidth = firstCard.offsetWidth;
    const style = window.getComputedStyle(track);
    // Ensure gap is parsed correctly, default to 0 if not a valid number
    gap = parseFloat(style.gap) || 0;
    cardWidthWithGap = cardWidth + gap;
  }

  // Ensure currentCardIndex is valid after potential content changes
  currentCardIndex = Math.max(0, Math.min(currentCardIndex, track.children.length - 1));
  updateCarouselPosition(currentCardIndex); // Set initial position and update arrows
}


function getTranslateX(el) {
  const style = window.getComputedStyle(el);
  const matrix = new DOMMatrixReadOnly(style.transform);
  return matrix.m41;
}

function updateCarouselPosition(index) {
  currentCardIndex = Math.max(0, Math.min(index, track.children.length - 1));

  track.style.transition = "transform 0.3s ease-out";
  track.style.transform = `translateX(-${currentCardIndex * cardWidthWithGap}px)`;

  // Update for future drags. This is important!
  currentTranslateXAtDragStart = -currentCardIndex * cardWidthWithGap;

  // Update the currentDisplayedTeamId based on the visible card
  const activeCard = track.children[currentCardIndex];
  if (activeCard) {
    currentDisplayedTeamId = activeCard.dataset.teamId;
    highlightActiveTeamRow(currentDisplayedTeamId); // Hebt die aktive Zeile links hervor
  } else {
    currentDisplayedTeamId = null;
  }

  setTimeout(() => {
    track.style.transition = ""; // Remove transition after animation
    updateCarouselArrows(); // Update arrows after position settles
  }, 300);
}

// Function to show/hide arrows (remains unchanged)
function updateCarouselArrows() {
  if (!leftArrow || !rightArrow || !track || track.children.length === 0) return;

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
// Fetch all projects and store globally
async function fetchAllProjects() {
  try {
    const response = await fetch("/api/projects");
    const result = await response.json();
    allProjectsData = result.projects || [];
    console.log("Projects loaded:", allProjectsData);
  } catch (err) {
    console.error("Error fetching projects:", err);
  }
}

//tasks container!!
async function renderTeamTasksOverview() {
  const container = document.getElementById("tasksOverviewContainer");
  if (!container) return;

  container.innerHTML = "";

  for (const team of allTeamsData) {
    const teamProjects = allProjectsData.filter(p => p.team_id === team.team_id);
    if (teamProjects.length === 0) continue;

    let teamHtml = `<div class="team-task-block"><h3>Team: ${team.team_name}</h3>`;

    for (const project of teamProjects) {
      const tasks = await fetchTasksForProject(project.project_id);
      teamHtml += `<div class="project-block"><h4>Project: ${project.name}</h4>`;

      if (tasks.length === 0) {
        teamHtml += `<p style="color: var(--text-muted);">No tasks found.</p>`;
      } else {
        teamHtml += `<ul>`;
        for (const task of tasks) {
          teamHtml += `<li>${task.title} <span style="color: var(--text-muted); font-size: 0.9em;">(Status: ${task.status})</span></li>`;
        }
        teamHtml += `</ul>`;
      }

      teamHtml += `</div>`; // Close project-block
    }

    teamHtml += `</div>`; // Close team-task-block
    container.innerHTML += teamHtml;
  }
}

async function fetchTasksForProject(projectId) {
  try {
    const res = await fetch(`/api/tasks?project_id=${projectId}`, {
      method: "GET",
      credentials: "include"
    });

    if (!res.ok) {
      console.error(`Failed to fetch tasks for project ${projectId}`);
      return [];
    }

    return await res.json();
  } catch (err) {
    console.error("Error fetching tasks:", err);
    return [];
  }
}