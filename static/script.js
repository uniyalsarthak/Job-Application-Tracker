let applications = [];

const tableBody = document.getElementById("applicationTable");
const emptyState = document.getElementById("emptyState");
const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
const modalOverlay = document.getElementById("modalOverlay");
const applicationForm = document.getElementById("applicationForm");

async function loadApplications() {
    try {
        const response = await fetch("/api/applications");

        if (response.status === 401) {
            window.location.href = "/";
            return;
        }

        if (!response.ok) {
            throw new Error("Could not load applications");
        }

        applications = await response.json();
        renderApplications();

    } catch (error) {
        console.error(error);
        alert("Could not load applications. Check that Flask and MySQL are running.");
    }
}

function formatDate(dateString) {
    if (!dateString) return "-";

    const date = new Date(dateString + "T00:00:00");

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
}

function getStatusClass(status) {
    return "status-" + status.toLowerCase();
}

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderApplications() {
    const search = searchInput.value.toLowerCase().trim();
    const filter = statusFilter.value;

    const filtered = applications.filter(application => {
        const matchesSearch =
            application.company.toLowerCase().includes(search) ||
            application.role.toLowerCase().includes(search);

        const matchesStatus =
            filter === "All" || application.status === filter;

        return matchesSearch && matchesStatus;
    });

    tableBody.innerHTML = "";

    filtered.forEach(application => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>
                <span class="company-name">
                    ${escapeHTML(application.company)}
                </span>
            </td>

            <td>
                <span class="role-name">
                    ${escapeHTML(application.role)}
                </span>
            </td>

            <td>
                ${formatDate(application.application_date)}
            </td>

            <td>
                <span class="status ${getStatusClass(application.status)}">
                    ${escapeHTML(application.status)}
                </span>
            </td>

            <td>
                <span class="notes"
                      title="${escapeHTML(application.notes || "")}">
                    ${escapeHTML(application.notes || "-")}
                </span>
            </td>

            <td>
                ${application.resume_path
                    ? `<a class="resume-link" href="/api/applications/${application.id}/resume" target="_blank" title="${escapeHTML(application.resume_filename || "")}">📄 View</a>`
                    : `<span class="notes">-</span>`}
            </td>

            <td>
                <div class="actions">
                    <button
                        class="action-btn"
                        onclick="editApplication(${application.id})"
                        title="Edit">
                        ✎
                    </button>

                    <button
                        class="action-btn"
                        onclick="deleteApplication(${application.id})"
                        title="Delete">
                        ×
                    </button>
                </div>
            </td>
        `;

        tableBody.appendChild(row);
    });

    emptyState.style.display = filtered.length ? "none" : "block";

    updateStats();
    updateProgress();
}

function updateStats() {
    document.getElementById("totalCount").textContent =
        applications.length;

    document.getElementById("inProgressCount").textContent =
        applications.filter(app => app.status === "In Progress").length;

    document.getElementById("selectedCount").textContent =
        applications.filter(app => app.status === "Selected").length;

    document.getElementById("rejectedCount").textContent =
        applications.filter(app => app.status === "Rejected").length;
}

function updateProgress() {
    const statuses = [
        "Applied",
        "In Progress",
        "Selected",
        "Rejected"
    ];

    const progressList = document.getElementById("progressList");

    progressList.innerHTML = statuses.map(status => {
        const count = applications.filter(
            app => app.status === status
        ).length;

        const percentage = applications.length
            ? Math.round((count / applications.length) * 100)
            : 0;

        return `
            <div class="progress-row">
                <div class="progress-label">
                    <span>${status}</span>
                    <span>${count}</span>
                </div>

                <div class="progress-track">
                    <div
                        class="progress-bar"
                        style="width: ${percentage}%">
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

function openModal(application = null) {
    applicationForm.reset();

    if (application) {
        document.getElementById("modalTitle").textContent =
            "Edit Application";

        document.getElementById("editId").value =
            application.id;

        document.getElementById("company").value =
            application.company;

        document.getElementById("role").value =
            application.role;

        document.getElementById("applicationDate").value =
            application.application_date;

        document.getElementById("status").value =
            application.status;

        document.getElementById("notes").value =
            application.notes || "";

        const resumeInfo = document.getElementById("currentResumeInfo");

        if (application.resume_path) {
            resumeInfo.innerHTML =
                `Current resume: <a href="/api/applications/${application.id}/resume" target="_blank">${escapeHTML(application.resume_filename || "view")}</a> (uploading a new file will replace it)`;
        } else {
            resumeInfo.textContent = "No resume uploaded yet.";
        }

    } else {
        document.getElementById("modalTitle").textContent =
            "Add Application";

        document.getElementById("applicationDate").value =
            new Date().toISOString().split("T")[0];

        document.getElementById("currentResumeInfo").textContent = "";
    }

    modalOverlay.classList.add("show");
}

function closeModal() {
    modalOverlay.classList.remove("show");
}

function editApplication(id) {
    const application = applications.find(
        app => app.id === id
    );

    if (application) {
        openModal(application);
    }
}

async function deleteApplication(id) {
    const application = applications.find(
        app => app.id === id
    );

    if (!application) return;

    const confirmed = confirm(
        `Delete the application for ${application.company}?`
    );

    if (!confirmed) return;

    try {
        const response = await fetch(
            `/api/applications/${id}`,
            {
                method: "DELETE"
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Delete failed");
        }

        await loadApplications();

    } catch (error) {
        console.error(error);
        alert(error.message);
    }
}

applicationForm.addEventListener("submit", async event => {
    event.preventDefault();

    const editId =
        document.getElementById("editId").value;

    const formData = new FormData();

    formData.append("company", document.getElementById("company").value.trim());
    formData.append("role", document.getElementById("role").value.trim());
    formData.append("application_date", document.getElementById("applicationDate").value);
    formData.append("status", document.getElementById("status").value);
    formData.append("notes", document.getElementById("notes").value.trim());

    const resumeFile = document.getElementById("resume").files[0];

    if (resumeFile) {
        formData.append("resume", resumeFile);
    }

    try {
        let url = "/api/applications";
        let method = "POST";

        if (editId) {
            url = `/api/applications/${editId}`;
            method = "PUT";
        }

        const response = await fetch(url, {
            method: method,
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Request failed");
        }

        closeModal();
        await loadApplications();

    } catch (error) {
        console.error(error);
        alert(error.message);
    }
});

document.getElementById("openModalBtn")
    .addEventListener("click", () => openModal());

document.getElementById("closeModalBtn")
    .addEventListener("click", closeModal);

document.getElementById("cancelBtn")
    .addEventListener("click", closeModal);

document.getElementById("logoutBtn")
    .addEventListener("click", async () => {
        await fetch("/api/logout", {
            method: "POST"
        });

        window.location.href = "/";
    });

modalOverlay.addEventListener("click", event => {
    if (event.target === modalOverlay) {
        closeModal();
    }
});

searchInput.addEventListener("input", renderApplications);
statusFilter.addEventListener("change", renderApplications);

loadApplications();