const API = "http://127.0.0.1:8000";

function authHeaders() {

    const token =
        localStorage.getItem(
            "access_token"
        );

    if (!token) {

        showToast(
            "Please login first",
            "warning"
        );

        throw new Error(
            "No authentication token"
        );
    }

    return {
        Authorization:
            `Bearer ${token}`
    };
}

let fileId = null;
let taskId = null;
let pollInterval = null;
let logCount = 0;
const renderedLogs = new Set();

let pendingLogs = [];
let logRendererRunning = false;

const latestAgentState = {};
let currentLoadingStage = null;
let pipelineFinished = false;

function normalizeAgentName(name) {

    const normalized = name.toLowerCase();

    if (normalized.includes("data")) {
        return "Data";
    }

    if (normalized.includes("analysis")) {
        return "Analysis";
    }

    if (normalized.includes("visual")) {
        return "Visualization";
    }

    if (normalized.includes("report")) {
        return "Report";
    }

    return name;
}

function normalizeStatus(status) {

    return String(status)
        .trim()
        .toLowerCase();
}

// ── File selection ──────────────────────────────────────────────
const fileInput = document.getElementById("fileInput");
const dropZone  = document.getElementById("dropZone");

fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) setSelectedFile(fileInput.files[0]);
});

dropZone.addEventListener("dragover", e => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const f = e.dataTransfer.files[0];
    if (f) { fileInput.files = e.dataTransfer.files; setSelectedFile(f); }
});

function setSelectedFile(file) {
    document.getElementById("fileName").textContent = file.name;
    document.getElementById("fileSelected").style.display = "flex";
    document.getElementById("uploadBtn").disabled = false;
}

// ── Upload file ─────────────────────────────────────────────────
async function uploadFile() {
    const file = fileInput.files[0];
    if (!file) return;

    const btn = document.getElementById("uploadBtn");
    showLoading("Uploading dataset...");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Uploading…`;

    try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(API + "/upload", { method: "POST", headers: authHeaders(), body: formData });
        if (!res.ok) throw new Error(`Upload failed: ${res.status}`);

        const data = await res.json();
        fileId = data.file_id;

        btn.innerHTML = `✓ Uploaded`;
        showToast("File uploaded successfully", "success");
        hideLoading();

        btn.style.background = "var(--green-light)";
        btn.style.color = "var(--green)";
        document.getElementById("runBtn").disabled = false;

    } catch (err) {
        btn.disabled = false;
        btn.textContent = "Retry Upload";
        showError("Upload failed: " + err.message);
        showToast("Upload failed", "error");
        hideLoading();
    }
}

// ── Create task ─────────────────────────────────────────────────
async function createTask() {
    const input = document.getElementById("taskInput").value.trim();
    if (!input) { document.getElementById("taskInput").focus(); return; }

    // Reset state
    clearLogs();
    resetAgents();
    document.getElementById("resultCard").style.display = "none";
    document.getElementById("result").textContent = "";
    if (pollInterval) clearInterval(pollInterval);

    const btn = document.getElementById("runBtn");
    showLoading("Launching AI pipeline...");
    btn.disabled = true;
    btn.innerHTML = `<span>Running…</span>`;

    try {
        const res = await fetch(API + "/task/create", {
            method: "POST",
            headers: { ...authHeaders(),"Content-Type": "application/json" },
            body: JSON.stringify({ user_input: input, file_id: fileId })
        });

        if (!res.ok) throw new Error(`Task creation failed: ${res.status}`);

        const data = await res.json();
        taskId = data.task_id;
        showToast("Analysis pipeline started", "info");

        pollLogs();

    } catch (err) {
        btn.disabled = false;
        btn.innerHTML = `▶ Run Analysis`;
        showError("Failed to start task: " + err.message);
    }
}

// ── Poll logs ───────────────────────────────────────────────────
function pollLogs() {
    pollInterval = setInterval(async () => {
        try {
            const res = await fetch(API + `/task/${taskId}/logs`, {headers: authHeaders()});
            if (!res.ok) return; // transient error — keep polling

            const logs = await res.json();
            console.log("LIVE LOGS:", logs);
            if (!Array.isArray(logs)) return;

            updateUI(logs);

            const done = logs.some(l => {
            
                const agent =
                    normalizeAgentName(l.agent);
            
                const status =
                    normalizeStatus(l.status);
            
                return (
                    agent === "Report"
                    &&
                    (
                        status === "completed"
                        ||
                        status === "success"
                        ||
                        status === "done"
                        ||
                        status === "finished"
                    )
                );
            });
            const failed = logs.some(l =>
                normalizeStatus(l.status) === "error"
            );

            if (done || failed) {
            
                // FORCE FINAL UI SYNC
                logs.forEach(log => {
                
                    const normalized =
                        normalizeAgentName(log.agent);
                
                    latestAgentState[normalized] = {
                        ...log,
                        agent: normalized
                    };
                });
            
                updateAgentUI();
            
                // WAIT for remaining streamed logs
                const waitForLogs = setInterval(() => {
                
                    if (pendingLogs.length === 0) {
                    
                        clearInterval(waitForLogs);
                    
                        clearInterval(pollInterval);
                    
                        pollInterval = null;
                    
                        const btn =
                            document.getElementById("runBtn");
                    
                        btn.disabled = false;
                    
                        btn.innerHTML = `▶ Run Analysis`;
                    
                        // FORCE FINAL STATES
                        finalizeCompletedAgents();
                        pipelineFinished = true;
                        setTimeout(() => {
                            hideLoading();
                        }, 500);
                    

                        if (failed) {

                            pipelineFinished = true;
                            hideLoading();

                            showToast(
                                "Pipeline execution failed",
                                "error"
                            );
                        }
                        if (done) {

                            showToast(
                                "Analysis completed successfully",
                                "success"
                            );
                        
                            fetchResult();
                        }
                    }
                
                }, 300);
            }
        } catch (err) {
            // network blip — keep polling silently
        }
    }, 800);
}

// ── Fetch final result ──────────────────────────────────────────
async function fetchResult() {
    try {
        const res = await fetch(API + `/task/${taskId}/result`, {headers: authHeaders()});
        if (!res.ok) return;

        const data = await res.json();

        console.log("RESULT:", data); // 🔥 DEBUG

        const resultEl = document.getElementById("result");
        const resultCard = document.getElementById("resultCard");

        resultCard.style.display = "block";

        resultEl.innerHTML = `
            <div style="margin-bottom:10px;">
                <strong>Analysis Completed</strong>
            </div>

            <div style="display:flex;gap:10px;flex-wrap:wrap;">

                <a href="${API + data.download_url}" target="_blank"
                   class="btn btn-primary">
                   Download PDF
                </a>

                <a href="${API + data.ppt_url}" target="_blank"
                   class="btn btn-gemini">
                   Export PPT
                </a>

            </div>
        `;

    } catch (err) {
        console.error(err);
    }
}

// ── Update UI ───────────────────────────────────────────────────
function updateUI(logs) {

    logs.forEach(log => {

        const normalizedAgent =
            normalizeAgentName(log.agent);

        log.agent = normalizedAgent;

        latestAgentState[normalizedAgent] = log;

        const uniqueKey =
            `${log.agent}-${log.message}-${log.time}`;

        if (renderedLogs.has(uniqueKey)) return;

        renderedLogs.add(uniqueKey);

        pendingLogs.push(log);
    });

    // Always update pipeline immediately
    updateAgentUI();

    startLogRenderer();
}

// ── REAL-TIME DELAY ───────────────────────────────────────────────────
function startLogRenderer() {

    if (logRendererRunning) return;

    logRendererRunning = true;

    const logsEl = document.getElementById("logs");

    const renderNext = () => {

        if (pendingLogs.length === 0) {
            logRendererRunning = false;
            return;
        }

        const wasEmpty =
            logsEl.querySelector(".logs-empty");

        if (wasEmpty) {
            wasEmpty.remove();
        }

        const log = pendingLogs.shift();

        logCount++;

        const entry = document.createElement("div");

        entry.className = "log-entry live-log";

        const status =
            normalizeStatus(log.status);
            
        const dotColor =
            ["completed", "success", "done", "finished"]
                .includes(status)
                    ? "var(--green)"
                    : status === "running"
                    ? "var(--blue)"
                    : status === "error"
                    ? "var(--red)"
                    : "var(--text-tertiary)";

        const time =
            new Date(log.time).toLocaleTimeString();

        entry.innerHTML = `
            <div class="log-dot"
                 style="background:${dotColor}">
            </div>

            <span class="log-agent-tag tag-${log.agent}">
                ${log.agent}
            </span>

            <span class="log-msg typing-text"></span>

            <span class="log-time">
                ${time}
            </span>
        `;

        logsEl.appendChild(entry);

        smoothScrollLogs();

        document.getElementById("logCount").textContent =
            `${logCount} events`;

        const textElement =
            entry.querySelector(".typing-text");

        typeText(
            textElement,
            log.message || "",
            () => {

                let delay = 450;

                if (log.agent === "Analysis") {
                    delay = 1100;
                }

                if (log.agent === "Visualization") {
                    delay = 700;
                }

                if (log.agent === "Report") {
                    delay = 900;
                }

                setTimeout(renderNext, delay);
            }
        );
    };

    renderNext();
}
// ── Log Typing Animation Function───────────────────────────────────────────────────
function typeText(element, text, callback) {

    let index = 0;

    const speed = 14;

    function type() {

        if (index < text.length) {

            element.textContent += text.charAt(index);

            index++;

            setTimeout(type, speed);

        } else {

            if (callback) {
                callback();
            }
        }
    }

    type();
}

// ── SMOOTH SCROLL───────────────────────────────────────────────────
function smoothScrollLogs() {

    const logsEl = document.getElementById("logs");

    logsEl.scrollTo({
        top: logsEl.scrollHeight,
        behavior: "smooth"
    });
}

// ── REAL-TIME AGENT UPDATE ───────────────────────────────────────────────────
function updateAgentUI() {
    if (!pipelineFinished) {

        const activeAgent =
            Object.values(latestAgentState)
                .find(log => log.status === "running");

        if (activeAgent) {

            const messages = {

                Data:
                    "Cleaning and preparing dataset...",

                Analysis:
                    "Running statistical analysis...",

                Visualization:
                    "Generating visualizations...",

                Report:
                    "Building report exports..."
            };

            const newStage =
                messages[activeAgent.agent];

            // ONLY update if stage changed
            if (currentLoadingStage !== newStage) {

                currentLoadingStage = newStage;

                showLoading(
                    newStage || "Processing..."
                );
            }
        }
    }    

    Object.values(latestAgentState).forEach(log => {

        const node =
            document.getElementById(`agent-${log.agent}`);

        const status =
            document.getElementById(`status-${log.agent}`);

        if (!node || !status) return;

        node.classList.remove(
            "running",
            "completed",
            "error"
        );

        if (normalizeStatus(log.status) === "running") {

            node.classList.add("running");

            status.textContent = "Running...";
        }

        else if (
            [
                "completed",
                "success",
                "done",
                "finished"
            ].includes(
                normalizeStatus(log.status)
            )
        ) {

            node.classList.add("completed");

            status.textContent = "Completed";
        }

        else if (normalizeStatus(log.status) === "error") {

            node.classList.add("error");

            status.textContent = "Error";
        }
    });
}


function finalizeCompletedAgents() {

    ["Data", "Analysis", "Visualization", "Report"]
        .forEach(agent => {

            const node =
                document.getElementById(`agent-${agent}`);

            const status =
                document.getElementById(`status-${agent}`);

            if (!node || !status) return;

            // Skip errors
            if (node.classList.contains("error")) {
                return;
            }

            node.classList.remove("running");

            node.classList.add("completed");

            status.textContent = "Done";
        });
}

// ── Helpers ─────────────────────────────────────────────────────
function clearLogs() {
    renderedLogs.clear();

    pendingLogs = [];
    logRendererRunning = false;
    currentLoadingStage = null;
    pipelineFinished = false;

    Object.keys(latestAgentState)
    .forEach(key => delete latestAgentState[key]);

    logCount = 0;
    const logsEl = document.getElementById("logs");
    logsEl.innerHTML = `<div class="logs-empty">
        <svg viewBox="0 0 24 24" width="32" height="32" opacity="0.3"><path fill="currentColor" d="M20 3H4v10c0 2.21 1.79 4 4 4h6c2.21 0 4-1.79 4-4v-3h2c1.11 0 2-.89 2-2V5c0-1.11-.89-2-2-2zm0 5h-2V5h2v3zM4 19h16v2H4z"/></svg>
        <p>No activity yet. Run an analysis to see logs.</p>
    </div>`;
    document.getElementById("logCount").textContent = "0 events";
}

function resetAgents() {
    ["Data", "Analysis", "Visualization", "Report"].forEach(name => {
        const node = document.getElementById(`agent-${name}`);
        const status = document.getElementById(`status-${name}`);
        if (node)   node.className = "agent-node";
        if (status) status.textContent = "Idle";
    });
}

function showError(msg) {
    const logsEl = document.getElementById("logs");
    logsEl.querySelector(".logs-empty")?.remove();
    const err = document.createElement("div");
    err.className = "log-entry";
    err.innerHTML = `<div class="log-dot" style="background:var(--red)"></div>
        <span class="log-agent-tag" style="background:#fce8e6;color:var(--red)">Error</span>
        <span class="log-msg">${msg}</span>`;
    logsEl.appendChild(err);
}

function showSection(section) {

    document.getElementById("dashboardSection").style.display = "none";
    document.getElementById("reportsSection").style.display = "none";
    document.getElementById("historySection").style.display = "none";

    document.getElementById(section + "Section").style.display = "block";

    document.querySelectorAll(".nav-item")
        .forEach(item => item.classList.remove("active"));

    event.currentTarget.classList.add("active");

    if (section === "history") {
        loadHistory();
    }

    if (section === "reports") {
        loadReports();
    }
}

// ── LoadHistory ───────────────────────────────────────────────────
async function loadHistory() {

    const res = await fetch(API + "/tasks", {headers: authHeaders() });

    const tasks = await res.json();

    const container =
        document.getElementById("historySection");

    container.innerHTML = `
        <div class="section-header">
            <h2>Task History</h2>
        </div>
    `;

    if (!tasks.length) {

        container.innerHTML += `
            <div class="empty-state">
                No task history available
            </div>
        `;

        return;
    }

    tasks.forEach(task => {

        let statusClass = "status-pending";

        if (task.status === "completed") {
            statusClass = "status-completed";
        }

        if (task.status === "running") {
            statusClass = "status-running";
        }

        if (task.status === "error") {
            statusClass = "status-error";
        }

        container.innerHTML += `
            <div class="history-card">

                <div class="history-top">

                    <div>
                        <div class="history-title">
                            Task #${task.id}
                        </div>

                        <div class="history-input">
                            ${task.input || "No input"}
                        </div>
                    </div>

                    <div class="history-status ${statusClass}">
                        ${task.status}
                    </div>
                </div>

                <div class="history-actions">

                    <button
                        class="history-btn"
                        onclick="viewTask(${task.id})"
                    >
                        View Logs
                    </button>

                    ${
                        task.result
                        ? `
                        <a
                            href="${API}/download/${task.id}/pdf"
                            target="_blank"
                            class="history-btn download"
                        >
                            PDF
                        </a>
                        `
                        : ""
                    }

                    ${
                        task.ppt
                        ? `
                        <a
                            href="${API}/download/${task.id}/ppt"
                            target="_blank"
                            class="history-btn ppt"
                        >
                            PPT
                        </a>
                        `
                        : ""
                    }

                </div>
            </div>
        `;
    });
}

// ── LoadReport ───────────────────────────────────────────────────
async function loadReports() {

    const res = await fetch(API + "/tasks", {headers: authHeaders()});
    const tasks = await res.json();

    const container =
        document.getElementById("reportsSection");

    container.innerHTML = `
        <div class="section-header">
            <h2>Reports</h2>
        </div>
    `;

    const completed =
        tasks.filter(t => t.status === "completed");

    if (!completed.length) {

        container.innerHTML += `
            <div class="empty-state">
                No reports available
            </div>
        `;

        return;
    }

    completed.forEach(t => {

        container.innerHTML += `
            <div class="report-card">

                <div>
                    <div class="report-title">
                        Task #${t.id}
                    </div>

                    <div class="report-status">
                        Completed
                    </div>
                </div>

                <div class="report-actions">

                    <a
                        href="${API}/download?path=${t.result}"
                        target="_blank"
                        class="btn-download"
                    >
                        PDF
                    </a>

                    ${
                        t.ppt
                        ? `
                        <a
                            href="${API}/download?path=${t.ppt}"
                            target="_blank"
                            class="btn-download ppt"
                        >
                            PPT
                        </a>
                        `
                        : ""
                    }
                
                </div>

            </div>
        `;
    });
}

function viewTask(id) {
    hideLoading();
    taskId = id;
    clearLogs();
    resetAgents();
    pollLogs();
    showSection("dashboard");
}

// ── Log in Logic ───────────────────────────────────────────────────

async function login() {

    const email =
        document.getElementById("email").value;

    const password =
        document.getElementById("password").value;

    const res = await fetch(
        API + "/login",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                email,
                password
            })
        }
    );

    const data = await res.json();

    if (data.access_token) {

        saveToken(data.access_token);

        showToast(
            "Login successful",
            "success"
        );

        document.getElementById(
            "authSection"
        ).style.display = "none";
    }

    else {

        showToast(
            "Login failed",
            "error"
        );
    }
}

function saveToken(token) {

    localStorage.setItem(
        "access_token",
        token
    );
}

// ── Log out ───────────────────────────────────────────────────

function logout() {

    localStorage.removeItem(
        "access_token"
    );

    location.reload();
}

window.addEventListener(
    "DOMContentLoaded",
    () => {

        const token =
            localStorage.getItem(
                "access_token"
            );

        if (token) {

            document.getElementById(
                "authSection"
            ).style.display = "none";
        }
    }
);

window.onload = () => {
    loadHistory();
};