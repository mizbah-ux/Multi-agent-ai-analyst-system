let API = localStorage.getItem("api_base_url") || "http://localhost:8000";
const AGENTS = ["Data", "Analysis", "Visualization", "Report"];

let fileId = null;
let taskId = null;
let pollInterval = null;
let pipelineFinalized = false;
let pollingSilentMode = false;
const renderedLogKeys = new Set();
let exportPreviewUrl = null;
let exportPreviewBlob = null;
let exportPreviewType = null;
let exportPreviewFilename = null;
let exportPreviewTaskId = null;
let downloadPromptTimer = null;

document.addEventListener("DOMContentLoaded", async () => {
    applyStoredTheme();
    bindUploadInteractions();
    bindPreviewShortcuts();
    await resolveApiBase();
    checkAuthentication();
});

async function resolveApiBase() {
    const candidates = [
        API,
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001"
    ].filter((value, index, array) => value && array.indexOf(value) === index);

    for (const candidate of candidates) {
        try {
            const res = await fetch(`${candidate}/`, { method: "GET" });
            if (res.ok) {
                API = candidate;
                localStorage.setItem("api_base_url", candidate);
                return;
            }
        } catch (error) {
            continue;
        }
    }
}

function applyStoredTheme() {
    const saved = localStorage.getItem("theme") ||
        (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", saved);
    updateThemeToggleText(saved);
}

function updateThemeToggleText(theme) {
    const el = document.getElementById("themeToggleText");
    const toggle = document.getElementById("themeToggle");
    if (el) {
        el.textContent = theme === "dark" ? "Dark mode active" : "Light mode active";
    }
    if (toggle) {
        toggle.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
        toggle.dataset.mode = theme;
        toggle.title = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateThemeToggleText(next);
}

async function checkAuthentication() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.replace("landing.html");
        return;
    }

    document.getElementById("authCheck").classList.remove("hidden");
    document.getElementById("dashboardSection").classList.add("hidden");

    try {
        const res = await fetchWithAuth(`${API}/tasks`);
        if (!res || !res.ok) {
            logout();
            return;
        }
        document.getElementById("authCheck").classList.add("hidden");
        document.getElementById("dashboardSection").classList.remove("hidden");
        showSection("dashboard");
        await Promise.all([loadHistory(), loadReports()]);
    } catch (error) {
        logout();
    }
}

async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem("access_token");
    options.headers = {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`
    };

    let response = await fetch(url, options);

    if (response.status === 401) {
        const refreshed = await refreshAccessToken();
        if (!refreshed) {
            return null;
        }
        const newToken = localStorage.getItem("access_token");
        options.headers.Authorization = `Bearer ${newToken}`;
        response = await fetch(url, options);
    }

    return response;
}

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) {
        return false;
    }

    try {
        const res = await fetch(`${API}/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!res.ok) {
            return false;
        }

        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        return true;
    } catch (error) {
        return false;
    }
}

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("role");
    window.location.href = "landing.html";
}

function bindUploadInteractions() {
    const fileInput = document.getElementById("fileInput");
    const dropZone = document.getElementById("dropZone");

    dropZone.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", () => {
        if (fileInput.files[0]) {
            setSelectedFile(fileInput.files[0]);
        }
    });

    dropZone.addEventListener("dragover", (event) => {
        event.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (event) => {
        event.preventDefault();
        dropZone.classList.remove("drag-over");
        const file = event.dataTransfer.files[0];
        if (file) {
            fileInput.files = event.dataTransfer.files;
            setSelectedFile(file);
        }
    });
}

function bindPreviewShortcuts() {
    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") {
            return;
        }

        const promptEl = document.getElementById("downloadPrompt");
        if (promptEl && promptEl.classList.contains("open")) {
            dismissDownloadPrompt();
            return;
        }

        const modal = document.getElementById("exportPreviewModal");
        if (modal && !modal.classList.contains("hidden")) {
            closeExportPreview();
        }
    });
}

function setSelectedFile(file) {
    document.getElementById("fileName").textContent = file.name;
    document.getElementById("fileSelected").classList.remove("hidden");
    document.getElementById("uploadBtn").disabled = false;
}

async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];
    if (!file) {
        return;
    }

    showLoading("Uploading dataset...");
    const uploadBtn = document.getElementById("uploadBtn");
    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading...";

    try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetchWithAuth(`${API}/upload`, {
            method: "POST",
            body: formData
        });

        if (!res || !res.ok) {
            throw new Error(`Upload failed (${res ? res.status : "auth"})`);
        }

        const data = await res.json();
        fileId = data.file_id;
        showToast("Dataset uploaded successfully", "success");
        uploadBtn.textContent = "Uploaded";
        document.getElementById("runBtn").disabled = false;
    } catch (error) {
        uploadBtn.disabled = false;
        uploadBtn.textContent = "Upload File";
        showToast(error.message, "error");
    } finally {
        hideLoading();
    }
}

async function createTask() {
    const requestText = document.getElementById("taskInput").value.trim();
    if (!fileId) {
        showToast("Upload a file before starting analysis", "warning");
        return;
    }
    if (!requestText) {
        showToast("Enter an analysis request", "warning");
        return;
    }

    clearLogs();
    resetPipeline();
    pipelineFinalized = false;
    document.getElementById("resultCard").classList.add("hidden");
    showLoading("Launching multi-agent pipeline...");

    const runBtn = document.getElementById("runBtn");
    runBtn.disabled = true;
    runBtn.textContent = "Starting...";

    try {
        const res = await fetchWithAuth(`${API}/task/create`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_input: requestText,
                file_id: fileId
            })
        });

        if (!res || !res.ok) {
            throw new Error(`Task start failed (${res ? res.status : "auth"})`);
        }

        const data = await res.json();
        taskId = data.task_id;
        showToast(`Task #${taskId} started`, "info");
        startTaskPolling();
    } catch (error) {
        hideLoading();
        runBtn.disabled = false;
        runBtn.textContent = "Run Analysis";
        showToast(error.message, "error");
    }
}

function startTaskPolling(silentMode = false) {
    pollingSilentMode = silentMode;
    if (pollInterval) {
        clearInterval(pollInterval);
    }

    pollTaskRealtime();
    pollInterval = setInterval(pollTaskRealtime, 1400);
}

async function pollTaskRealtime() {
    if (!taskId || pipelineFinalized) {
        return;
    }

    try {
        const [statusRes, logsRes] = await Promise.all([
            fetchWithAuth(`${API}/task/${taskId}/status`),
            fetchWithAuth(`${API}/task/${taskId}/logs`)
        ]);

        if (!statusRes || !statusRes.ok || !logsRes || !logsRes.ok) {
            return;
        }

        const statusBody = await statusRes.json();
        const logsBody = await logsRes.json();
        const logs = Array.isArray(logsBody.logs) ? logsBody.logs : [];

        renderLiveLogs(logs);
        updatePipelineFromLogs(logs, statusBody.status);

        if (statusBody.status === "completed") {
            await finalizeTaskSuccess();
        } else if (statusBody.status === "failed" || statusBody.status === "error") {
            finalizeTaskFailure();
        }
    } catch (error) {
        console.error(error);
    }
}

function renderLiveLogs(logs) {
    const logsEl = document.getElementById("logs");
    const sorted = [...logs].sort((a, b) => new Date(a.time) - new Date(b.time));

    sorted.forEach((log) => {
        const key = `${log.agent}|${log.message}|${log.time}`;
        if (renderedLogKeys.has(key)) {
            return;
        }
        renderedLogKeys.add(key);

        logsEl.querySelector(".logs-empty")?.remove();

        const normalizedStatus = normalizeStatus(log.status);
        const dotColor =
            normalizedStatus === "completed" ? "var(--success)" :
            normalizedStatus === "running" ? "var(--accent)" :
            "var(--danger)";

        const entry = document.createElement("div");
        entry.className = "log-entry";
        entry.innerHTML = `
            <span class="log-dot" style="background:${dotColor};"></span>
            <span class="log-agent">${normalizeAgentName(log.agent)}</span>
            <span class="log-msg">${log.message || ""}</span>
            <span class="log-time">${formatTime(log.time)}</span>
        `;
        logsEl.appendChild(entry);
    });

    document.getElementById("logCount").textContent = `${renderedLogKeys.size} events`;
    logsEl.scrollTop = logsEl.scrollHeight;
}

function resetPipeline() {
    AGENTS.forEach((agent) => {
        const node = document.getElementById(`agent-${agent}`);
        const status = document.getElementById(`status-${agent}`);
        node.classList.remove("running", "completed", "failed");
        status.textContent = "Idle";
    });
    document.getElementById("pipelineState").textContent = "Running";
}

function normalizeStatus(status) {
    const s = String(status || "").toLowerCase();
    if (["completed", "success", "done", "finished"].includes(s)) {
        return "completed";
    }
    if (["failed", "error"].includes(s)) {
        return "failed";
    }
    return s;
}

function normalizeAgentName(name) {
    const n = String(name || "").toLowerCase();
    if (n.includes("data")) {
        return "Data";
    }
    if (n.includes("analysis")) {
        return "Analysis";
    }
    if (n.includes("visual")) {
        return "Visualization";
    }
    if (n.includes("report")) {
        return "Report";
    }
    return name;
}

function updatePipelineFromLogs(logs, taskStatus) {
    const latestByAgent = {};
    for (const log of logs) {
        const agent = normalizeAgentName(log.agent);
        latestByAgent[agent] = log;
    }

    AGENTS.forEach((agent) => {
        const node = document.getElementById(`agent-${agent}`);
        const statusEl = document.getElementById(`status-${agent}`);
        node.classList.remove("running", "completed", "failed");

        const log = latestByAgent[agent];
        if (!log) {
            statusEl.textContent = "Idle";
            return;
        }

        const status = normalizeStatus(log.status);
        if (status === "running") {
            node.classList.add("running");
            statusEl.textContent = "Running";
        } else if (status === "completed") {
            node.classList.add("completed");
            statusEl.textContent = "Completed";
        } else if (status === "failed") {
            node.classList.add("failed");
            statusEl.textContent = "Failed";
        } else {
            statusEl.textContent = status || "Idle";
        }
    });

    if (taskStatus === "completed") {
        document.getElementById("pipelineState").textContent = "Completed";
    } else if (taskStatus === "failed" || taskStatus === "error") {
        document.getElementById("pipelineState").textContent = "Failed";
    } else {
        document.getElementById("pipelineState").textContent = "Running";
    }
}

async function finalizeTaskSuccess() {
    if (pipelineFinalized) {
        return;
    }
    pipelineFinalized = true;
    clearInterval(pollInterval);
    pollInterval = null;
    hideLoading();

    const runBtn = document.getElementById("runBtn");
    runBtn.disabled = false;
    runBtn.textContent = "Run Analysis";

    renderExportCard();
    await Promise.all([loadAnalysisDashboard(), loadHistory(), loadReports()]);
    if (!pollingSilentMode) {
        showToast("Pipeline completed successfully", "success");
    }
    pollingSilentMode = false;
}

function finalizeTaskFailure() {
    if (pipelineFinalized) {
        return;
    }
    pipelineFinalized = true;
    clearInterval(pollInterval);
    pollInterval = null;
    hideLoading();

    const runBtn = document.getElementById("runBtn");
    runBtn.disabled = false;
    runBtn.textContent = "Run Analysis";
    document.getElementById("pipelineState").textContent = "Failed";
    if (!pollingSilentMode) {
        showToast("Pipeline execution failed", "error");
    }
    pollingSilentMode = false;
}

function clearLogs() {
    renderedLogKeys.clear();
    const logsEl = document.getElementById("logs");
    logsEl.innerHTML = `<div class="logs-empty">No activity yet. Run an analysis to stream logs.</div>`;
    document.getElementById("logCount").textContent = "0 events";
}

function renderExportCard() {
    if (!taskId) {
        return;
    }
    const card = document.getElementById("resultCard");
    const result = document.getElementById("result");
    card.classList.remove("hidden");
    result.innerHTML = `
        <div class="result-actions">
            <button class="export-btn primary" onclick="openExportPreview(${taskId}, 'pdf')">View PDF Export</button>
            <button class="export-btn success" onclick="openExportPreview(${taskId}, 'ppt')">View PPT Export</button>
        </div>
    `;
}

function formatTime(value) {
    if (!value) {
        return "--:--";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "--:--";
    }
    return date.toLocaleTimeString();
}

function classifyChartType(chartPath) {
    const path = String(chartPath).toLowerCase();
    if (path.includes("heatmap") || path.includes("scatter")) {
        return "correlation";
    }
    if (path.includes("pie") || path.includes("_bar")) {
        return "category";
    }
    if (path.includes("line") || path.includes("trend")) {
        return "trend";
    }
    if (path.includes("hist") || path.includes("boxplot")) {
        return "distribution";
    }
    return "other";
}

function setChartFilter(type) {
    const cards = document.querySelectorAll(".chart-card");
    cards.forEach((card) => {
        const chartType = card.getAttribute("data-chart-type");
        if (type === "all" || chartType === type) {
            card.classList.remove("hidden");
        } else {
            card.classList.add("hidden");
        }
    });

    const filters = document.querySelectorAll(".filter-btn");
    filters.forEach((btn) => {
        if (btn.getAttribute("data-filter") === type) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });
}

function showSection(section, triggerEl = null) {
    const sections = ["dashboard", "analysis", "reports", "history"];
    sections.forEach((item) => {
        const sectionEl = document.getElementById(`${item}Section`);
        if (!sectionEl) {
            return;
        }
        if (item === section) {
            sectionEl.classList.remove("hidden");
        } else {
            sectionEl.classList.add("hidden");
        }
    });

    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach((btn) => btn.classList.remove("active"));
    if (triggerEl) {
        triggerEl.classList.add("active");
    } else {
        navItems.forEach((btn) => {
            if ((btn.getAttribute("onclick") || "").includes(`'${section}'`)) {
                btn.classList.add("active");
            }
        });
    }

    if (section === "history") {
        loadHistory();
    } else if (section === "reports") {
        loadReports();
    } else if (section === "analysis") {
        loadAnalysisDashboard();
    }
}

function getExportMeta(fileType) {
    if (fileType === "pdf") {
        return {
            label: "PDF",
            extension: ".pdf",
            accept: { "application/pdf": [".pdf"] }
        };
    }
    return {
        label: "PPT",
        extension: ".pptx",
        accept: { "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"] }
    };
}

function escapeHtml(value) {
    return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#039;");
}

function formatBytes(size) {
    if (!Number.isFinite(size) || size <= 0) {
        return "0 B";
    }
    const units = ["B", "KB", "MB", "GB"];
    let unitIndex = 0;
    let value = size;
    while (value >= 1024 && unitIndex < units.length - 1) {
        value /= 1024;
        unitIndex += 1;
    }
    return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[unitIndex]}`;
}

function parseFilenameFromDisposition(value) {
    if (!value) {
        return null;
    }

    const utfMatch = value.match(/filename\*=UTF-8''([^;]+)/i);
    if (utfMatch && utfMatch[1]) {
        try {
            return decodeURIComponent(utfMatch[1]).replaceAll("\"", "");
        } catch (error) {
            return utfMatch[1].replaceAll("\"", "");
        }
    }

    const simpleMatch = value.match(/filename="?([^\";]+)"?/i);
    return simpleMatch && simpleMatch[1] ? simpleMatch[1] : null;
}

function cleanupPreparedExport() {
    if (exportPreviewUrl) {
        URL.revokeObjectURL(exportPreviewUrl);
    }
    exportPreviewUrl = null;
    exportPreviewBlob = null;
    exportPreviewType = null;
    exportPreviewFilename = null;
    exportPreviewTaskId = null;
}

function dismissDownloadPrompt() {
    const prompt = document.getElementById("downloadPrompt");
    prompt?.classList.remove("open");
}

function openDownloadPrompt(fileLabel, filename) {
    const prompt = document.getElementById("downloadPrompt");
    const text = document.getElementById("downloadPromptText");
    if (!prompt || !text) {
        return;
    }
    text.textContent = `${fileLabel} is ready (${filename}). Download now?`;
    prompt.classList.add("open");
}

async function fetchAnalysisPreview(targetTaskId) {
    try {
        const res = await fetchWithAuth(`${API}/task/${targetTaskId}/analysis`);
        if (!res || !res.ok) {
            return null;
        }
        const payload = await res.json();
        const analysis = payload.analysis || {};
        return {
            request: payload.analysis_request || "",
            summary: analysis.business_summary || "",
            chartCount: Array.isArray(payload.charts) ? payload.charts.length : 0,
            rows: analysis.row_count || 0,
            columns: analysis.column_count || 0
        };
    } catch (error) {
        return null;
    }
}

function renderPreviewBody(fileType, objectUrl, previewInfo, blob) {
    const body = document.getElementById("exportPreviewBody");
    if (!body) {
        return;
    }

    const summaryRequest = previewInfo?.request
        ? `<p class="preview-summary-item"><strong>Request:</strong> ${escapeHtml(previewInfo.request)}</p>`
        : "<p class=\"preview-summary-item\"><strong>Request:</strong> No request text captured.</p>";

    const summaryBusiness = previewInfo?.summary
        ? `<p class="preview-summary-item"><strong>Business Summary:</strong> ${escapeHtml(previewInfo.summary)}</p>`
        : "<p class=\"preview-summary-item\"><strong>Business Summary:</strong> Not available for this task.</p>";

    const summaryMetrics = `
        <div class="preview-metrics">
            <span class="chip">Rows: ${previewInfo?.rows || 0}</span>
            <span class="chip">Columns: ${previewInfo?.columns || 0}</span>
            <span class="chip">Charts: ${previewInfo?.chartCount || 0}</span>
            <span class="chip">File Size: ${formatBytes(blob?.size || 0)}</span>
        </div>
    `;

    if (fileType === "pdf") {
        body.innerHTML = `
            <div class="preview-summary">
                ${summaryRequest}
                ${summaryBusiness}
                ${summaryMetrics}
            </div>
            <div class="preview-frame-wrap">
                <iframe class="preview-frame" src="${objectUrl}" title="PDF Preview"></iframe>
            </div>
        `;
        return;
    }

    body.innerHTML = `
        <div class="preview-summary">
            ${summaryRequest}
            ${summaryBusiness}
            ${summaryMetrics}
        </div>
        <div class="preview-placeholder">
            <p>PPT preview is limited in browser. The deck contains your generated analysis slides and is ready to download.</p>
        </div>
    `;
}

async function openExportPreview(selectedTaskId, fileType) {
    if (!selectedTaskId) {
        showToast("Task ID not available for export", "warning");
        return;
    }

    const meta = getExportMeta(fileType);
    showLoading(`Preparing ${meta.label} preview...`);

    try {
        if (downloadPromptTimer) {
            clearTimeout(downloadPromptTimer);
            downloadPromptTimer = null;
        }
        dismissDownloadPrompt();
        cleanupPreparedExport();

        const response = await fetchWithAuth(`${API}/download/${selectedTaskId}/${fileType}`);
        if (!response || !response.ok) {
            throw new Error(`${meta.label} export is not available for this task`);
        }

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        const contentName = parseFilenameFromDisposition(response.headers.get("content-disposition"));
        const fallbackName = `task_${selectedTaskId}_report${meta.extension}`;
        const filename = contentName || fallbackName;
        const previewInfo = await fetchAnalysisPreview(selectedTaskId);

        exportPreviewUrl = objectUrl;
        exportPreviewBlob = blob;
        exportPreviewType = fileType;
        exportPreviewFilename = filename;
        exportPreviewTaskId = selectedTaskId;

        const labelEl = document.getElementById("exportPreviewLabel");
        const titleEl = document.getElementById("exportPreviewTitle");
        const modal = document.getElementById("exportPreviewModal");
        if (labelEl) {
            labelEl.textContent = `${meta.label} Export`;
        }
        if (titleEl) {
            titleEl.textContent = `Task #${selectedTaskId} ${meta.label} Preview`;
        }
        renderPreviewBody(fileType, objectUrl, previewInfo, blob);
        modal?.classList.remove("hidden");

        downloadPromptTimer = window.setTimeout(() => {
            openDownloadPrompt(meta.label, filename);
        }, 250);
    } catch (error) {
        showToast(error.message || "Unable to open export preview", "error");
    } finally {
        hideLoading();
    }
}

function closeExportPreview() {
    if (downloadPromptTimer) {
        clearTimeout(downloadPromptTimer);
        downloadPromptTimer = null;
    }
    dismissDownloadPrompt();
    const modal = document.getElementById("exportPreviewModal");
    const body = document.getElementById("exportPreviewBody");
    modal?.classList.add("hidden");
    if (body) {
        body.innerHTML = "";
    }
    cleanupPreparedExport();
}

async function savePreparedExport() {
    if (!exportPreviewBlob || !exportPreviewType) {
        showToast("No export file prepared yet", "warning");
        return;
    }

    const meta = getExportMeta(exportPreviewType);
    const filename = exportPreviewFilename || `task_${exportPreviewTaskId || "report"}${meta.extension}`;

    if ("showSaveFilePicker" in window) {
        try {
            const handle = await window.showSaveFilePicker({
                suggestedName: filename,
                types: [
                    {
                        description: `${meta.label} file`,
                        accept: meta.accept
                    }
                ]
            });

            const writable = await handle.createWritable();
            await writable.write(exportPreviewBlob);
            await writable.close();
            showToast(`${meta.label} saved successfully`, "success");
            return;
        } catch (error) {
            if (error && error.name === "AbortError") {
                showToast("Download canceled", "info");
                return;
            }
        }
    }

    if (!exportPreviewUrl) {
        exportPreviewUrl = URL.createObjectURL(exportPreviewBlob);
    }

    const link = document.createElement("a");
    link.href = exportPreviewUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    showToast(`${meta.label} download started`, "success");
}

async function confirmDownloadPrompt() {
    await savePreparedExport();
    dismissDownloadPrompt();
}

async function loadHistory() {
    const res = await fetchWithAuth(`${API}/tasks`);
    if (!res || !res.ok) {
        return;
    }

    const tasks = await res.json();
    const sorted = [...tasks].sort((a, b) => b.id - a.id);
    const container = document.getElementById("historySection");

    container.innerHTML = `
        <div class="section-header">
            <h2>Task History</h2>
            <p>Review previous runs and open logs or exports.</p>
        </div>
    `;

    if (!sorted.length) {
        container.innerHTML += `<div class="logs-empty">No task history available.</div>`;
        return;
    }

    sorted.forEach((task) => {
        const statusClass =
            task.status === "completed" ? "status-completed" :
            task.status === "running" ? "status-running" :
            task.status === "failed" ? "status-failed" :
            "status-pending";

        container.innerHTML += `
            <div class="history-card">
                <div class="history-top">
                    <div>
                        <p class="history-title">Task #${task.id}</p>
                        <p class="history-subtitle">${task.input || "No request text provided"}</p>
                    </div>
                    <span class="status-pill ${statusClass}">${task.status}</span>
                </div>
                <div class="history-actions">
                    <button class="mini-btn" onclick="viewTask(${task.id})">View Live Panel</button>
                    ${task.result ? `<button class="mini-btn" onclick="openExportPreview(${task.id}, 'pdf')">PDF</button>` : ""}
                    ${task.ppt ? `<button class="mini-btn" onclick="openExportPreview(${task.id}, 'ppt')">PPT</button>` : ""}
                </div>
            </div>
        `;
    });
}

async function loadReports() {
    const res = await fetchWithAuth(`${API}/tasks`);
    if (!res || !res.ok) {
        return;
    }

    const tasks = await res.json();
    const completed = tasks.filter((task) => task.status === "completed").sort((a, b) => b.id - a.id);
    const container = document.getElementById("reportsSection");

    container.innerHTML = `
        <div class="section-header">
            <h2>Exports</h2>
            <p>All completed runs with downloadable PDF and PPT reports.</p>
        </div>
    `;

    if (!completed.length) {
        container.innerHTML += `<div class="logs-empty">No completed reports yet.</div>`;
        return;
    }

    completed.forEach((task) => {
        container.innerHTML += `
            <div class="report-card">
                <div class="report-top">
                    <div>
                        <p class="report-title">Task #${task.id}</p>
                        <p class="report-subtitle">${task.input || "No request text provided"}</p>
                    </div>
                    <span class="status-pill status-completed">completed</span>
                </div>
                <div class="report-actions">
                    <button class="mini-btn" onclick="openExportPreview(${task.id}, 'pdf')">Download PDF</button>
                    <button class="mini-btn" onclick="openExportPreview(${task.id}, 'ppt')">Download PPT</button>
                </div>
            </div>
        `;
    });
}

function viewTask(id) {
    taskId = id;
    pipelineFinalized = false;
    clearLogs();
    resetPipeline();
    renderExportCard();
    showSection("dashboard");
    startTaskPolling(true);
    loadAnalysisDashboard();
}

async function loadAnalysisDashboard() {
    const container = document.getElementById("analysisSection");

    if (!taskId) {
        container.innerHTML = `
            <div class="section-header">
                <h2>Advanced Analysis</h2>
                <p>Select or run a task to inspect adaptive analytics.</p>
            </div>
        `;
        return;
    }

    const res = await fetchWithAuth(`${API}/task/${taskId}/analysis`);
    if (!res || !res.ok) {
        container.innerHTML = `
            <div class="section-header">
                <h2>Advanced Analysis</h2>
                <p>Analysis is not ready for task #${taskId}.</p>
            </div>
        `;
        return;
    }

    const payload = await res.json();
    const analysis = payload.analysis || {};
    const charts = payload.charts || [];
    const requestText = payload.analysis_request || analysis.request_alignment?.request || "No explicit request captured.";
    const summary = analysis.business_summary || "No business summary available.";
    const requestInsights = (analysis.request_alignment?.insights || []).map((item) => `<li>${item}</li>`).join("");
    const chips = (analysis.request_alignment?.matched_columns || [])
        .map((col) => `<span class="chip">${col}</span>`)
        .join("");

    const numericRows = Object.entries(analysis.numeric_summary || {}).map(([col, stats]) => `
        <tr>
            <td>${col}</td>
            <td>${Number(stats.mean).toFixed(2)}</td>
            <td>${Number(stats.median).toFixed(2)}</td>
            <td>${Number(stats.min).toFixed(2)}</td>
            <td>${Number(stats.max).toFixed(2)}</td>
            <td>${Number(stats.std || 0).toFixed(2)}</td>
        </tr>
    `).join("");

    const categoryCards = Object.entries(analysis.categorical_summary || {}).map(([col, values]) => {
        const lines = Object.entries(values).map(([value, count]) => `${value}: ${count}`).join("<br>");
        return `
            <div class="category-item">
                <h4>${col}</h4>
                <p>${lines || "No category data"}</p>
            </div>
        `;
    }).join("");

    const chartHtml = charts.map((chartPath) => {
        const type = classifyChartType(chartPath);
        return `
            <div class="chart-card" data-chart-type="${type}">
                <img src="${API}/${chartPath}" alt="chart ${chartPath}" />
                <p class="chart-caption">${type}</p>
            </div>
        `;
    }).join("");

    const missingColumns = Object.entries(analysis.data_quality?.missing_by_column || {}).map(([col, meta]) => `
        <span class="chip">${col}: ${meta.count} (${Number(meta.percent).toFixed(1)}%)</span>
    `).join("");

    container.innerHTML = `
        <div class="section-header">
            <h2>Advanced Analysis for Task #${taskId}</h2>
            <p>Request: ${requestText}</p>
        </div>

        <div class="analytics-grid">
            <div class="analytics-card"><h3>Rows</h3><p>${analysis.row_count || 0}</p></div>
            <div class="analytics-card"><h3>Columns</h3><p>${analysis.column_count || 0}</p></div>
            <div class="analytics-card"><h3>Numeric Fields</h3><p>${Object.keys(analysis.numeric_summary || {}).length}</p></div>
            <div class="analytics-card"><h3>Categorical Fields</h3><p>${Object.keys(analysis.categorical_summary || {}).length}</p></div>
        </div>

        <div class="analysis-layout">
            <div class="analysis-card">
                <h3>Business Narrative Summary</h3>
                <p class="analysis-text">${summary}</p>
            </div>

            <div class="analysis-card">
                <h3>Request-Aligned Insights</h3>
                <ul class="insight-list">${requestInsights || "<li>No request-specific insights generated.</li>"}</ul>
                <div class="chips">${chips || '<span class="chip">No direct matched columns</span>'}</div>
            </div>

            <div class="analysis-card">
                <h3>Data Quality Signals</h3>
                <div class="chips">
                    <span class="chip">Duplicate Rows: ${analysis.data_quality?.duplicate_rows || 0}</span>
                    ${missingColumns || '<span class="chip">No missing-value columns detected</span>'}
                </div>
            </div>

            <div class="analysis-card">
                <h3>Numeric Summary</h3>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Column</th>
                                <th>Mean</th>
                                <th>Median</th>
                                <th>Min</th>
                                <th>Max</th>
                                <th>Std</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${numericRows || '<tr><td colspan="6">No numeric columns available.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="analysis-card">
                <h3>Categorical Highlights</h3>
                <div class="category-grid">
                    ${categoryCards || "<div class='logs-empty'>No categorical summary available.</div>"}
                </div>
            </div>

            <div class="analysis-card">
                <h3>Adaptive Charts</h3>
                <div class="filter-row">
                    <button class="filter-btn active" data-filter="all" onclick="setChartFilter('all')">All</button>
                    <button class="filter-btn" data-filter="distribution" onclick="setChartFilter('distribution')">Distribution</button>
                    <button class="filter-btn" data-filter="category" onclick="setChartFilter('category')">Category</button>
                    <button class="filter-btn" data-filter="correlation" onclick="setChartFilter('correlation')">Correlation</button>
                    <button class="filter-btn" data-filter="trend" onclick="setChartFilter('trend')">Trend</button>
                </div>
                <div class="chart-grid">
                    ${chartHtml || "<div class='logs-empty'>No charts generated for this dataset.</div>"}
                </div>
            </div>
        </div>
    `;
}
