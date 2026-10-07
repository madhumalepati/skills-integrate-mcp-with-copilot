document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authButton = document.getElementById("auth-button");
  const authLabel = document.getElementById("auth-label");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  const teacherOnlyMessage = document.getElementById("teacher-only-message");
  let isTeacher = false;

  function showMessage(element, message, type) {
    element.textContent = message;
    element.className = type;
    element.classList.remove("hidden");
  }

  function setTeacherState(authenticated) {
    isTeacher = authenticated;
    signupForm.classList.toggle("hidden", !isTeacher);
    teacherOnlyMessage.classList.toggle("hidden", isTeacher);
    authLabel.textContent = isTeacher ? "Sign out teacher" : "Teacher login";
    authButton.setAttribute(
      "aria-label",
      isTeacher ? "Sign out teacher" : "Teacher login"
    );
    fetchActivities();
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      if (!response.ok) {
        throw new Error(`Activity request failed with status ${response.status}`);
      }
      const activities = await response.json();

      activitiesList.replaceChildren();
      activitySelect.replaceChildren(new Option("-- Select an activity --", ""));

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";
        const spotsLeft =
          details.max_participants - details.participants.length;

        activityCard.innerHTML = `
          <h4></h4>
          <p class="activity-description"></p>
          <p><strong>Schedule:</strong> <span class="activity-schedule"></span></p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            <div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list"></ul>
              <p class="empty-participants hidden"><em>No participants yet</em></p>
            </div>
          </div>
        `;
        activityCard.querySelector("h4").textContent = name;
        activityCard.querySelector(".activity-description").textContent =
          details.description;
        activityCard.querySelector(".activity-schedule").textContent =
          details.schedule;

        const participantsList =
          activityCard.querySelector(".participants-list");
        const emptyParticipants = activityCard.querySelector(
          ".empty-participants"
        );
        emptyParticipants.classList.toggle(
          "hidden",
          details.participants.length > 0
        );
        details.participants.forEach((email) => {
          const listItem = document.createElement("li");
          const emailText = document.createElement("span");
          emailText.className = "participant-email";
          emailText.textContent = email;
          listItem.appendChild(emailText);

          if (isTeacher) {
            const unregisterButton = document.createElement("button");
            unregisterButton.className = "delete-btn";
            unregisterButton.type = "button";
            unregisterButton.textContent = "❌";
            unregisterButton.setAttribute("aria-label", `Unregister ${email}`);
            unregisterButton.dataset.activity = name;
            unregisterButton.dataset.email = email;
            unregisterButton.addEventListener("click", handleUnregister);
            listItem.appendChild(unregisterButton);
          }
          participantsList.appendChild(listItem);
        });

        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.textContent =
        "Failed to load activities. Please try again later.";
      console.error("Error fetching activities:", error);
    }
  }

  async function checkAuthStatus() {
    try {
      const response = await fetch("/auth/status");
      if (!response.ok) {
        throw new Error(`Authentication status failed with ${response.status}`);
      }
      const status = await response.json();
      setTeacherState(status.authenticated);
    } catch (error) {
      setTeacherState(false);
      console.error("Error checking teacher session:", error);
    }
  }

  async function handleUnregister(event) {
    const button = event.currentTarget;
    const activity = button.dataset.activity;
    const email = button.dataset.email;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      const result = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          setTeacherState(false);
        }
        throw new Error(result.detail || "An error occurred");
      }
      showMessage(messageDiv, result.message, "success");
      fetchActivities();
    } catch (error) {
      showMessage(
        messageDiv,
        error.message || "Failed to unregister. Please try again.",
        "error"
      );
      console.error("Error unregistering:", error);
    }

    setTimeout(() => messageDiv.classList.add("hidden"), 5000);
  }

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const activity = activitySelect.value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        { method: "POST" }
      );
      const result = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          setTeacherState(false);
        }
        throw new Error(result.detail || "An error occurred");
      }
      showMessage(messageDiv, result.message, "success");
      signupForm.reset();
      fetchActivities();
    } catch (error) {
      showMessage(
        messageDiv,
        error.message || "Failed to sign up. Please try again.",
        "error"
      );
      console.error("Error signing up:", error);
    }

    setTimeout(() => messageDiv.classList.add("hidden"), 5000);
  });

  authButton.addEventListener("click", async () => {
    if (!isTeacher) {
      loginMessage.classList.add("hidden");
      loginForm.reset();
      loginDialog.showModal();
      return;
    }

    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to sign out");
      }
      setTeacherState(false);
    } catch (error) {
      showMessage(
        messageDiv,
        error.message || "Unable to sign out. Please try again.",
        "error"
      );
      console.error("Error signing out:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to sign in");
      }
      loginDialog.close();
      setTeacherState(true);
      showMessage(messageDiv, result.message, "success");
    } catch (error) {
      showMessage(
        loginMessage,
        error.message || "Unable to sign in. Please try again.",
        "error"
      );
      console.error("Error signing in:", error);
    }
  });

  document.getElementById("cancel-login").addEventListener("click", () => {
    loginDialog.close();
  });

  checkAuthStatus();
});
