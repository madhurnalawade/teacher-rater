const bootstrap = window.APP_BOOTSTRAP || {};

const state = {
    user: bootstrap.user || null,
    isAdmin: Boolean(bootstrap.isAdmin),
    needsUsername: Boolean(bootstrap.needsUsername),
    selectedProfessorId: null,
    professors: [],
    selectedProfessor: null,
};

const professorListEl = document.getElementById("professorList");
const statusMessageEl = document.getElementById("statusMessage");
const createProfessorFormEl = document.getElementById("createProfessorForm");
const reviewFormEl = document.getElementById("reviewForm");
const reviewsListEl = document.getElementById("reviewsList");
const detailEmptyEl = document.getElementById("professorDetailEmpty");
const detailContentEl = document.getElementById("professorDetailContent");
const detailNameEl = document.getElementById("detailName");
const detailDepartmentEl = document.getElementById("detailDepartment");
const detailPhotoEl = document.getElementById("detailPhoto");
const detailAverageEl = document.getElementById("detailAverage");
const detailCountEl = document.getElementById("detailCount");
const editProfessorButtonEl = document.getElementById("editProfessorButton");
const deleteProfessorButtonEl = document.getElementById("deleteProfessorButton");
const editProfessorFormEl = document.getElementById("editProfessorForm");
const editProfessorNameEl = document.getElementById("editProfessorName");
const editProfessorDepartmentEl = document.getElementById("editProfessorDepartment");
const editProfessorPhotoUrlEl = document.getElementById("editProfessorPhotoUrl");
const cancelEditProfessorButtonEl = document.getElementById("cancelEditProfessorButton");
const logoutButtonEl = document.getElementById("logoutButton");
const usernameFormEl = document.getElementById("usernameForm");
const usernameInputEl = document.getElementById("usernameInput");

function setStatus(message, isError = false) {
    if (!statusMessageEl) {
        return;
    }

    statusMessageEl.textContent = message;
    statusMessageEl.classList.toggle("error", isError);
}

function escapeHtml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatStars(rating) {
    return "★".repeat(rating) + "☆".repeat(5 - rating);
}

async function apiFetch(path, options = {}) {
    const config = {
        credentials: "same-origin",
        ...options,
        headers: {
            ...(options.headers || {}),
        },
    };

    if (config.body && !(config.headers["Content-Type"] || config.headers["content-type"])) {
        config.headers["Content-Type"] = "application/json";
    }

    const response = await fetch(path, config);
    const text = await response.text();
    let body = null;

    if (text) {
        try {
            body = JSON.parse(text);
        } catch {
            body = null;
        }
    }

    if (!response.ok) {
        throw new Error(body?.detail || `Request failed (${response.status})`);
    }

    return body;
}

function renderProfessors() {
    if (!professorListEl) {
        return;
    }

    if (!state.professors.length) {
        const emptyMessage = state.isAdmin
            ? "No professors yet. Add the first one."
            : "No professors yet. The admin will add professors soon.";
        professorListEl.innerHTML = `<li class="muted">${emptyMessage}</li>`;
        return;
    }

    professorListEl.innerHTML = state.professors
        .map((professor) => {
            const score = professor.average_rating == null
                ? "No ratings"
                : `${Number(professor.average_rating).toFixed(1)} / 5`;
            const activeClass = state.selectedProfessorId === professor.id ? "active" : "";
            const department = professor.department
                ? `<p class=\"muted\">${escapeHtml(professor.department)}</p>`
                : "";
            const photo = professor.photo_url
                ? `<img class="professor-thumb" src="${escapeHtml(professor.photo_url)}" alt="${escapeHtml(professor.name)}" loading="lazy" />`
                : "";

            return `
                <li>
                    <button class="professor-item ${activeClass}" type="button" data-professor-id="${professor.id}">
                        ${photo}
                        <span class="professor-main">
                            <span class="professor-name">${escapeHtml(professor.name)}</span>
                            ${department}
                        </span>
                        <span class="score-chip">${score}</span>
                    </button>
                </li>
            `;
        })
        .join("");
}

function renderProfessorDetails() {
    if (!detailEmptyEl || !detailContentEl || !reviewsListEl) {
        return;
    }

    if (!state.selectedProfessor) {
        detailEmptyEl.classList.remove("hidden");
        detailContentEl.classList.add("hidden");
        if (editProfessorButtonEl) {
            editProfessorButtonEl.classList.add("hidden");
            editProfessorButtonEl.removeAttribute("data-professor-id");
        }
        if (deleteProfessorButtonEl) {
            deleteProfessorButtonEl.classList.add("hidden");
            deleteProfessorButtonEl.removeAttribute("data-professor-id");
        }
        if (editProfessorFormEl) {
            editProfessorFormEl.classList.add("hidden");
        }
        return;
    }

    const professor = state.selectedProfessor;
    detailEmptyEl.classList.add("hidden");
    detailContentEl.classList.remove("hidden");

    if (editProfessorFormEl) {
        if (state.isAdmin) {
            editProfessorFormEl.classList.remove("hidden");
        } else {
            editProfessorFormEl.classList.add("hidden");
        }
    }

    if (editProfessorButtonEl) {
        if (state.isAdmin) {
            editProfessorButtonEl.classList.remove("hidden");
            editProfessorButtonEl.setAttribute("data-professor-id", String(professor.id));
        } else {
            editProfessorButtonEl.classList.add("hidden");
            editProfessorButtonEl.removeAttribute("data-professor-id");
        }
    }

    if (deleteProfessorButtonEl) {
        if (state.isAdmin) {
            deleteProfessorButtonEl.classList.remove("hidden");
            deleteProfessorButtonEl.setAttribute("data-professor-id", String(professor.id));
        } else {
            deleteProfessorButtonEl.classList.add("hidden");
            deleteProfessorButtonEl.removeAttribute("data-professor-id");
        }
    }

    detailNameEl.textContent = professor.name;
    detailDepartmentEl.textContent = professor.department || "No department listed";

    if (editProfessorNameEl) {
        editProfessorNameEl.value = professor.name || "";
    }
    if (editProfessorDepartmentEl) {
        editProfessorDepartmentEl.value = professor.department || "";
    }
    if (editProfessorPhotoUrlEl) {
        editProfessorPhotoUrlEl.value = professor.photo_url || "";
    }
    if (detailPhotoEl) {
        if (professor.photo_url) {
            detailPhotoEl.src = professor.photo_url;
            detailPhotoEl.classList.remove("hidden");
        } else {
            detailPhotoEl.removeAttribute("src");
            detailPhotoEl.classList.add("hidden");
        }
    }
    detailAverageEl.textContent = professor.average_rating == null
        ? "-"
        : Number(professor.average_rating).toFixed(1);
    detailCountEl.textContent = `${professor.review_count} review${professor.review_count === 1 ? "" : "s"}`;

    if (!professor.reviews.length) {
        reviewsListEl.innerHTML = "<p class=\"muted\">No reviews yet. Be the first to write one.</p>";
        return;
    }

    reviewsListEl.innerHTML = professor.reviews
        .map((review) => {
            const date = new Date(review.created_at).toLocaleDateString();
            const textBlock = review.review_text
                ? `<p class=\"review-text\">${escapeHtml(review.review_text)}</p>`
                : "<p class=\"review-text muted\">No written comment.</p>";
            const reviewerEmail = review.reviewer.email
                ? `<p class="reviewer-email">${escapeHtml(review.reviewer.email)}</p>`
                : "";
            const isDeleted = Boolean(review.is_deleted);
            const canDeleteReview = Boolean(
                state.user
                && (
                    state.isAdmin
                    || Number(state.user.id) === Number(review.reviewer.id)
                )
            );
            const deleteAction = canDeleteReview && !isDeleted
                ? `<div class="review-footer"><button class="button button-danger" type="button" data-delete-review-id="${review.id}">Delete review</button></div>`
                : "";
            const deletedState = isDeleted ? `<p class="muted deleted-review-label">Deleted review</p>` : "";
            const reviewItemClass = [
                "review-item",
                state.isAdmin ? "review-item-admin" : "",
                isDeleted ? "review-item-deleted" : "",
            ]
                .filter(Boolean)
                .join(" ");

            return `
                <article class="${reviewItemClass}">
                    <div class="review-meta">
                        <p class="reviewer-name">@${escapeHtml(review.reviewer.username)}</p>
                        <p class="muted">${date}</p>
                    </div>
                    ${deletedState}
                    ${reviewerEmail}
                    <p class="review-stars">${formatStars(review.rating)}</p>
                    ${textBlock}
                    ${deleteAction}
                </article>
            `;
        })
        .join("");
}

async function loadProfessors() {
    state.professors = await apiFetch("/api/professors");
    renderProfessors();

    if (state.selectedProfessorId) {
        const stillExists = state.professors.some((professor) => professor.id === state.selectedProfessorId);
        if (!stillExists) {
            state.selectedProfessorId = null;
            state.selectedProfessor = null;
            renderProfessorDetails();
        }
    }
}

async function selectProfessor(professorId) {
    state.selectedProfessorId = professorId;
    state.selectedProfessor = await apiFetch(`/api/professors/${professorId}`);
    renderProfessors();
    renderProfessorDetails();
}

async function onCreateProfessorSubmit(event) {
    event.preventDefault();
    if (!state.user) {
        setStatus("Sign in with Google first.", true);
        return;
    }

    if (!state.isAdmin) {
        setStatus("Only the admin account can add professors.", true);
        return;
    }

    const name = document.getElementById("professorName")?.value.trim() || "";
    const department = document.getElementById("professorDepartment")?.value.trim() || "";
    const photoUrl = document.getElementById("professorPhotoUrl")?.value.trim() || "";

    if (!name) {
        setStatus("Professor name is required.", true);
        return;
    }

    const payload = {
        name,
        department: department || null,
        photo_url: photoUrl || null,
    };

    try {
        const created = await apiFetch("/api/professors", {
            method: "POST",
            body: JSON.stringify(payload),
        });

        createProfessorFormEl.reset();
        await loadProfessors();
        await selectProfessor(created.id);
        setStatus("Professor added.");
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function onReviewSubmit(event) {
    event.preventDefault();
    if (!state.user) {
        setStatus("Sign in with Google first.", true);
        return;
    }

    if (!state.user.username) {
        setStatus("Set your username before posting reviews.", true);
        return;
    }

    if (!state.selectedProfessorId) {
        setStatus("Choose a professor first.", true);
        return;
    }

    const formData = new FormData(reviewFormEl);
    const ratingValue = Number(formData.get("rating"));
    const reviewText = (formData.get("review_text") || "").toString().trim();

    if (!ratingValue || ratingValue < 1 || ratingValue > 5) {
        setStatus("Select a star rating between 1 and 5.", true);
        return;
    }

    try {
        await apiFetch(`/api/professors/${state.selectedProfessorId}/reviews`, {
            method: "POST",
            body: JSON.stringify({ rating: ratingValue, review_text: reviewText || null }),
        });

        reviewFormEl.reset();
        await loadProfessors();
        await selectProfessor(state.selectedProfessorId);
        setStatus("Review submitted.");
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function onProfessorListClick(event) {
    const button = event.target.closest("[data-professor-id]");
    if (!button) {
        return;
    }

    const professorId = Number(button.getAttribute("data-professor-id"));
    if (!Number.isInteger(professorId)) {
        return;
    }

    try {
        await selectProfessor(professorId);
        setStatus("");
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function onDeleteProfessorClick(event) {
    const button = event.currentTarget;
    const professorId = Number(button.getAttribute("data-professor-id"));
    if (!Number.isInteger(professorId)) {
        return;
    }

    const confirmed = window.confirm("Delete this professor and all related reviews?");
    if (!confirmed) {
        return;
    }

    try {
        await apiFetch(`/api/professors/${professorId}`, { method: "DELETE" });
        state.selectedProfessorId = null;
        state.selectedProfessor = null;
        renderProfessorDetails();
        await loadProfessors();
        setStatus("Professor deleted.");
    } catch (error) {
        setStatus(error.message, true);
    }
}

function showEditProfessorForm() {
    if (!editProfessorFormEl) {
        return;
    }
    editProfessorFormEl.classList.remove("hidden");
}

function hideEditProfessorForm() {
    if (!editProfessorFormEl) {
        return;
    }
    editProfessorFormEl.classList.add("hidden");
}

async function onEditProfessorClick() {
    if (!state.isAdmin || !state.selectedProfessor) {
        return;
    }
    showEditProfessorForm();
}

async function onEditProfessorSubmit(event) {
    event.preventDefault();
    if (!state.isAdmin || !state.selectedProfessorId) {
        return;
    }

    const name = (editProfessorNameEl?.value || "").trim();
    const department = (editProfessorDepartmentEl?.value || "").trim();
    const photoUrl = (editProfessorPhotoUrlEl?.value || "").trim();

    if (!name) {
        setStatus("Professor name is required.", true);
        return;
    }

    try {
        await apiFetch(`/api/professors/${state.selectedProfessorId}`, {
            method: "PUT",
            body: JSON.stringify({
                name,
                department: department || null,
                photo_url: photoUrl || null,
            }),
        });

        hideEditProfessorForm();
        await loadProfessors();
        await selectProfessor(state.selectedProfessorId);
        setStatus("Professor updated.");
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function onReviewsListClick(event) {
    const button = event.target.closest("[data-delete-review-id]");
    if (!button) {
        return;
    }

    const reviewId = Number(button.getAttribute("data-delete-review-id"));
    if (!Number.isInteger(reviewId)) {
        return;
    }

    const confirmed = window.confirm("Delete this review?");
    if (!confirmed) {
        return;
    }

    try {
        await apiFetch(`/api/reviews/${reviewId}`, { method: "DELETE" });
        if (state.selectedProfessorId) {
            await loadProfessors();
            await selectProfessor(state.selectedProfessorId);
        }
        setStatus("Review deleted.");
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function onLogoutClick() {
    try {
        await apiFetch("/auth/logout", { method: "POST" });
    } catch {
        // Ignore logout errors and refresh anyway.
    }

    window.location.reload();
}

async function onUsernameSubmit(event) {
    event.preventDefault();
    if (!state.user || !usernameInputEl) {
        return;
    }

    const username = usernameInputEl.value.trim();
    if (!username) {
        setStatus("Username is required.", true);
        return;
    }

    try {
        const me = await apiFetch("/api/me/username", {
            method: "POST",
            body: JSON.stringify({ username }),
        });

        state.user = {
            ...state.user,
            username: me.username,
            is_admin: me.is_admin,
        };
        state.isAdmin = Boolean(me.is_admin);
        state.needsUsername = !Boolean(me.username);
        setStatus("Username saved.");
        window.location.reload();
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function init() {
    if (createProfessorFormEl) {
        createProfessorFormEl.addEventListener("submit", onCreateProfessorSubmit);
    }

    if (reviewFormEl) {
        reviewFormEl.addEventListener("submit", onReviewSubmit);
    }

    if (professorListEl) {
        professorListEl.addEventListener("click", onProfessorListClick);
    }

    if (logoutButtonEl) {
        logoutButtonEl.addEventListener("click", onLogoutClick);
    }

    if (deleteProfessorButtonEl) {
        deleteProfessorButtonEl.addEventListener("click", onDeleteProfessorClick);
    }

    if (editProfessorButtonEl) {
        editProfessorButtonEl.addEventListener("click", onEditProfessorClick);
    }

    if (editProfessorFormEl) {
        editProfessorFormEl.addEventListener("submit", onEditProfessorSubmit);
    }

    if (cancelEditProfessorButtonEl) {
        cancelEditProfessorButtonEl.addEventListener("click", hideEditProfessorForm);
    }

    if (reviewsListEl) {
        reviewsListEl.addEventListener("click", onReviewsListClick);
    }

    if (usernameFormEl) {
        usernameFormEl.addEventListener("submit", onUsernameSubmit);
    }

    if (state.user && state.needsUsername) {
        setStatus("Pick a unique username before submitting reviews.");
    }

    try {
        await loadProfessors();
    } catch (error) {
        setStatus(error.message, true);
    }
}

void init();
