const headers = {
  "Content-Type": "application/json"
};

// Global variables for carousel
let cardWidth = 0;
let gap = 0;
let cardWidthWithGap = 0;
let currentCardIndex = 0; // Keep track of current card index
let currentDisplayedTeamId = null; // To store the ID of the currently displayed team

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
  customModalContent = customModal.querySelector(".custom-modal-content"); //Initialize customModalContent
}

function showCustomModal(title, message, inputPlaceholder, confirmText, cancelText, type) {
  return new Promise(resolve => {
    customModalResolve = resolve;

    customModalTitle.textContent = title;
    customModalMessage.textContent = message;

    // Reset and configure input
    customModalInput.value = '';
    customModalInput.placeholder = inputPlaceholder || '';
    customModalInput.style.display = inputPlaceholder ? 'block' : 'none';

    // Configure buttons
    customModalConfirmBtn.textContent = confirmText || 'OK';
    customModalCancelBtn.textContent = cancelText || 'Cancel';
    customModalCancelBtn.style.display = cancelText ? 'inline-block' : 'none';

    // Set modal type class for CSS styling
    customModal.classList.remove('prompt-type', 'alert-type', 'confirm-type');
    customModal.classList.add(`${type}-type`);

    // Add success/error class to content for color changes
    if (customModalContent) { // Ensure customModalContent is initialized
        customModalContent.classList.remove('success', 'error');
        if (type === 'alert' && title.includes('Success')) {
            customModalContent.classList.add('success');
        } else if (type === 'alert' && title.includes('Error')) {
            customModalContent.classList.add('error');
        }
    }


    // Event listeners for buttons
    const handleConfirm = () => {
      hideCustomModal();
      resolve(inputPlaceholder ? customModalInput.value : true);
      removeListeners();
    };

    const handleCancel = () => {
      hideCustomModal();
      resolve(false);
      removeListeners();
    };

    const handleKeydown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleConfirm();
      } else if (e.key === 'Escape' && cancelText) {
        e.preventDefault();
        handleCancel();
      }
    };

    customModalConfirmBtn.addEventListener('click', handleConfirm);
    customModalCancelBtn.addEventListener('click', handleCancel);
    document.addEventListener('keydown', handleKeydown);

    // Function to remove event listeners to prevent memory leaks
    const removeListeners = () => {
      customModalConfirmBtn.removeEventListener('click', handleConfirm);
      customModalCancelBtn.removeEventListener('click', handleCancel);
      document.removeEventListener('keydown', handleKeydown);
    };

    customModal.classList.add('active');
    if (inputPlaceholder) {
      setTimeout(() => customModalInput.focus(), 300); // Focus input after animation
    } else {
      setTimeout(() => customModalConfirmBtn.focus(), 300); // Focus confirm button
    }
  });
}

function hideCustomModal() {
  customModal.classList.remove('active');
  if (customModalContent) { // Ensure customModalContent is initialized
      customModalContent.classList.remove('success', 'error'); // Clean up type classes
  }
}

// Wrapper functions for convenience
function showCustomPrompt(title, message, placeholder) {
  return showCustomModal(title, message, placeholder, 'Submit', 'Cancel', 'prompt');
}

function showCustomAlert(title, message, type = 'alert') { // type can be 'success' or 'error' for styling
  return showCustomModal(title, message, null, 'OK', null, 'alert');
}

function showCustomConfirm(title, message) {
  return showCustomModal(title, message, null, 'Confirm', 'Cancel', 'confirm');
}


document.addEventListener("DOMContentLoaded", () => {
  initializeModalElements(); // Initialize modal elements after DOM is loaded
  fetchUserTeams(); // Initial team load and then carousel setup

  //Team Management Buttons
  const createTeamBtn = document.querySelector(".create-team-btn");
  const addMemberBtn = document.querySelector(".add-member-btn");
  deleteMemberButton = document.querySelector(".delete-member-btn"); // Assign to global variable
  const deleteTeamBtn = document.querySelector(".delete-team-btn");

  //All button event listeners are now at the same level
  if (createTeamBtn) {
    createTeamBtn.addEventListener("click", async () => {
      const teamName = await showCustomPrompt("Create New Team", "Enter the name for your new team:", "Team Name");
      if (!teamName || teamName.trim() === "") {
        showCustomAlert("Error", "Team name is required.", "error");
        return;
      }

      try {
        const response = await fetch("/api/teams/", {
          method: "POST",
          headers: headers,
          body: JSON.stringify({ name: teamName.trim() }),
          credentials: "include"
        });

        const data = await response.json();

        if (response.ok) {
          showCustomAlert("Success!", `Team "${teamName.trim()}" created successfully!`, "success");
          fetchUserTeams();
        } else {
          showCustomAlert("Error", "Error: " + (data.error || "Unknown error"), "error");
        }
      } catch (err) {
        console.error("Error at creating the Team:", err);
        showCustomAlert("Error", "Network error. Please try again.", "error");
      }
    });
  }

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

  // Add member button listener to use User ID or Username
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

      // Clarify prompt: User ID or Username
      const memberInfo = await showCustomPrompt("Add New Member", "Enter new member's User ID or Username and Role (e.g., '123, member' or 'john_doe, admin'):", "User ID or Username, role");
      if (!memberInfo || memberInfo.trim() === "") {
        showCustomAlert("Error", "User ID/Username and Role are required.", "error");
        return;
      }

      const parts = memberInfo.split(',').map(p => p.trim());
      const newMemberIdentifier = parts[0]; // This can be user_id (as string) or username
      const role = parts[1] || 'member'; // Default to 'member' if not specified

      if (!newMemberIdentifier) {
        showCustomAlert("Error", "Invalid User ID or Username provided.", "error");
        return;
      }

      try {
        // Send newMemberIdentifier as user_id to the backend, which handles ID or username
        const response = await fetch(`/api/teams/${currentDisplayedTeamId}/add-member`, {
          method: "PATCH",
          headers: headers,
          body: JSON.stringify({ user_id: newMemberIdentifier, role: role }), // Sending user_id or username
          credentials: "include"
        });

        const data = await response.json();
        console.log("Add Member Response Status:", response.status); // Log status
        console.log("Add Member Response Data:", data); // Log data

        if (response.ok) {
          // Check for specific backend messages even if response.ok is true
          if (data.error) { // If backend returns 200 but with an 'error' key
            showCustomAlert("Error", "Error adding member: " + data.error, "error");
          } else {
            showCustomAlert("Success!", "Member added successfully!", "success");
            fetchUserTeams(); // Re-fetch all teams to update the carousel
          }
        } else {
          showCustomAlert("Error", "Error adding member: " + (data.error || "Unknown error"), "error");
        }
      } catch (err) {
        console.error("Error adding member:", err);
        showCustomAlert("Error", "Network error. Please try again.", "error");
      }
    });
  }

  // Toggle delete mode listener
  if (deleteMemberButton) {
    deleteMemberButton.addEventListener("click", () => {
      if (!currentDisplayedTeamId) {
        showCustomAlert("Error", "Please select a team first.", "error");
        return;
      }
      toggleDeleteMode();
    });
  }

  // Carousel Event Listeners
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

  // Carousel drag event listeners
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

  // Add Escape key listener to exit delete mode
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isDeleteMode) {
      toggleDeleteMode();
    }
  });
});


// Function to toggle delete mode
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

// Handler for clicking a member in delete mode
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
      // Assuming /api/teams/ endpoint returns current_user info
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
      console.log("Final teamsWithMembers data:", teamsWithMembers); // ADDED THIS LOG
      renderTeams(teamsData); // Render teams in the table
      renderMembersForTeams(teamsWithMembers); // Render members into carousel
      setupCarousel(); // Setup carousel *after* members are rendered
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

    tr.innerHTML = `
      <td>${team.team_name}</td>
      <td>${new Date(team.created_at).toLocaleDateString()}</td>
      <td class="${team.role === 'admin' ? 'role-admin' : 'role-member'}">${team.role}</td>
    `;

    tbody.appendChild(tr);
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
          <span class="member-name">${member.username}</span> <span class="member-role ${member.role === 'admin' ? 'admin' : ''}">${member.role}</span>
        </div>
        <span class="delete-icon">✖</span> <!-- Delete icon -->
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

  // Re-apply shake animation if delete mode is active after re-rendering
  if (isDeleteMode) {
    document.querySelectorAll(".member-item").forEach(item => {
      item.classList.add("shake-animation");
      item.addEventListener("click", handleMemberDeleteClick);
    });
  }
}

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
  } else {
    currentDisplayedTeamId = null;
  }

  setTimeout(() => {
    track.style.transition = ""; // Remove transition after animation
    updateCarouselArrows(); // Update arrows after position settles
  }, 300);
}

// Function to show/hide arrows
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