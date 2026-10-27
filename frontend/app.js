/**
 * AI QA Engineer — Frontend Application Controller
 * Handles UI interactions, job dispatch, status polling, file inspection, and report rendering.
 */

// State
let currentJobId = null;
let pollInterval = null;
let currentReport = null;
let activeProjectPath = "demo";

// Agent Node Mapping
const AGENTS = [
  "code_loader",
  "code_analyzer",
  "security_agent",
  "test_generator",
  "test_runner",
  "coverage_agent",
  "bug_analysis",
  "root_cause",
  "qa_report",
];

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initHealthCheck();
  initDemoProjectInfo();
  initEventListeners();
  initTabs();
});

/**
 * Check backend status and set Demo Mode / Online badges
 */
async function initHealthCheck() {
  const modeBadge = document.getElementById("mode-badge");
  const modeText = document.getElementById("mode-text");

  try {
    const res = await fetch("/health");
    if (!res.ok) throw new Error("Health check failed");
    const data = await res.json();

    if (data.demo_mode) {
      modeBadge.className = "badge badge-pulse demo";
      modeText.textContent = "Demo / Fallback Mode Active";
    } else {
      modeBadge.className = "badge badge-pulse";
      modeText.textContent = "Gemini API Connected";
    }
  } catch (err) {
    modeBadge.className = "badge badge-danger";
    modeText.textContent = "Backend Offline";
  }
}

/**
 * Fetch and populate demo project file tags with click-to-view support
 */
async function initDemoProjectInfo() {
  try {
    const res = await fetch("/api/demo");
    if (!res.ok) return;
    const data = await res.json();

    const tagsContainer = document.getElementById("demo-files-tags");
    if (tagsContainer && data.files && data.files.length > 0) {
      tagsContainer.innerHTML = "";
      data.files.forEach((file) => {
        const tag = document.createElement("span");
        tag.className = "tag clickable";
        tag.textContent = file;
        tag.title = `Click to view ${file}`;
        tag.addEventListener("click", () => openFileModal(file));
        tagsContainer.appendChild(tag);
      });
    }
  } catch (err) {
    console.warn("Could not fetch demo info:", err);
  }
}

/**
 * Setup Button and Input Listeners
 */
function initEventListeners() {
  // Use Demo Project Button
  const btnDemo = document.getElementById("btn-use-demo");
  btnDemo.addEventListener("click", async () => {
    activeProjectPath = "demo";
    document.getElementById("target-project-name").textContent =
      "demo_project/ (Built-in Demo with Planted Issues)";
    document.getElementById("demo-files-tags").style.display = "flex";

    // Refresh tags
    await initDemoProjectInfo();

    showToast("✨ Built-in Demo Project loaded! Starting AI QA Analysis...", "success");
    logActivity("Supervisor", "Loaded built-in demo project. Initiating LangGraph workflow...", "normal");

    // Automatically trigger analysis for seamless 1-click experience
    startAnalysis();
  });

  // Upload Project (.zip)
  const fileInput = document.getElementById("file-input");
  fileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    showToast(`📦 Uploading archive: ${file.name}...`, "info");
    logActivity("Supervisor", `Uploading custom archive: ${file.name}...`);
    document.getElementById("target-project-name").textContent = `Uploaded: ${file.name}`;
    document.getElementById("demo-files-tags").style.display = "none";

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();

      currentJobId = data.job_id;
      activeProjectPath = `uploaded_zip_${currentJobId}`;
      showToast(`🚀 Analysis started for ${file.name}!`, "success");
      startJobTracking(data.job_id);
    } catch (err) {
      showToast(`Upload error: ${err.message}`, "error");
      logActivity("Supervisor", `Upload failed: ${err.message}`, "error");
    }
  });

  // Start QA Analysis
  document.getElementById("btn-start-analysis").addEventListener("click", () => {
    startAnalysis();
  });

  // Close RCA Drawer
  document.getElementById("btn-close-rca").addEventListener("click", () => {
    document.getElementById("rca-drawer").style.display = "none";
  });

  // Close Code Inspector Modal
  const modalCloseBtn = document.getElementById("btn-close-code-modal");
  if (modalCloseBtn) {
    modalCloseBtn.addEventListener("click", () => {
      document.getElementById("code-modal").style.display = "none";
    });
  }

  // Close modal when clicking on overlay
  const codeModal = document.getElementById("code-modal");
  if (codeModal) {
    codeModal.addEventListener("click", (e) => {
      if (e.target === codeModal) {
        codeModal.style.display = "none";
      }
    });
  }

  // Copy Generated Tests
  document.getElementById("btn-copy-tests").addEventListener("click", () => {
    const code = document.getElementById("generated-tests-code").textContent;
    navigator.clipboard.writeText(code);
    showToast("📋 Test suite copied to clipboard!", "success");
  });

  // Human-in-the-loop: Approve Report
  document.getElementById("btn-approve-report").addEventListener("click", () => {
    submitApproval("approved");
  });

  // Human-in-the-loop: Reject Report
  document.getElementById("btn-reject-report").addEventListener("click", () => {
    submitApproval("rejected");
  });
}

/**
 * Setup Tab Switching
 */
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");
    });
  });
}

/**
 * Open file inspector modal
 */
async function openFileModal(filename) {
  const modal = document.getElementById("code-modal");
  const filenameLabel = document.getElementById("modal-filename");
  const lineLabel = document.getElementById("modal-line-count");
  const contentCode = document.getElementById("modal-file-content");

  filenameLabel.textContent = filename;
  lineLabel.textContent = "Loading...";
  contentCode.textContent = "# Fetching source code...";
  modal.style.display = "flex";

  try {
    const res = await fetch(`/api/file?filename=${encodeURIComponent(filename)}`);
    if (!res.ok) throw new Error("File not found");
    const data = await res.json();

    lineLabel.textContent = `${data.lines} lines`;
    contentCode.textContent = data.content;
  } catch (err) {
    contentCode.textContent = `# Error loading file: ${err.message}`;
  }
}

/**
 * Trigger new QA Analysis
 */
async function startAnalysis() {
  resetUI();
  const btnStart = document.getElementById("btn-start-analysis");
  btnStart.disabled = true;
  btnStart.innerHTML = `<span class="status-dot"></span> Analyzing...`;

  logActivity("Supervisor", "Dispatching LangGraph Multi-Agent Orchestrator...");
  showToast("⚡ LangGraph Multi-Agent pipeline active...", "info");

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_path: activeProjectPath }),
    });

    if (!res.ok) throw new Error("Failed to start analysis");
    const data = await res.json();

    currentJobId = data.job_id;
    startJobTracking(data.job_id);
  } catch (err) {
    btnStart.disabled = false;
    btnStart.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> START AI QA ANALYSIS`;
    showToast(`Error starting analysis: ${err.message}`, "error");
    logActivity("Supervisor", `Analysis dispatch failed: ${err.message}`, "error");
  }
}

/**
 * Poll job status until completion
 */
function startJobTracking(jobId) {
  if (pollInterval) clearInterval(pollInterval);

  pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/status/${jobId}`);
      if (!res.ok) return;
      const statusData = await res.json();

      updateWorkflowUI(statusData);

      if (statusData.status === "completed") {
        clearInterval(pollInterval);
        const btnStart = document.getElementById("btn-start-analysis");
        btnStart.disabled = false;
        btnStart.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> START AI QA ANALYSIS`;

        showToast("🎉 QA Analysis completed! Report ready.", "success");
        logActivity("Supervisor", "All agents completed successfully. Fetching QA report.", "success");
        fetchAndRenderReport(jobId);
      } else if (statusData.status === "failed") {
        clearInterval(pollInterval);
        const btnStart = document.getElementById("btn-start-analysis");
        btnStart.disabled = false;
        btnStart.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> START AI QA ANALYSIS`;

        showToast(`Pipeline failed: ${statusData.errors.join(", ")}`, "error");
        logActivity("Supervisor", `Pipeline failed: ${statusData.errors.join(", ")}`, "error");
      }
    } catch (err) {
      console.error("Status polling error:", err);
    }
  }, 750);
}

/**
 * Update Agent Node States & Progress Bar
 */
function updateWorkflowUI(statusData) {
  const workflow = statusData.workflow_status || {};
  const progressPercent = statusData.progress || 0;

  // Update progress bar
  document.getElementById("progress-percent").textContent = `${progressPercent}% Completed`;
  document.getElementById("pipeline-progress-bar").style.width = `${progressPercent}%`;

  // Update each agent node
  AGENTS.forEach((agent) => {
    const node = document.getElementById(`node-${agent}`);
    const stateLabel = document.getElementById(`state-${agent}`);
    const state = workflow[agent] || "pending";

    if (!node || !stateLabel) return;

    node.className = `agent-node ${state}`;
    stateLabel.textContent = state.charAt(0).toUpperCase() + state.slice(1);

    if (state === "running" && stateLabel.textContent !== "Running...") {
      logActivity(formatAgentName(agent), "Agent activated and processing state...");
    }
  });
}

/**
 * Fetch and Render Final QA Report
 */
async function fetchAndRenderReport(jobId) {
  try {
    const res = await fetch(`/api/report/${jobId}`);
    if (!res.ok) throw new Error("Could not retrieve report");
    const report = await res.json();
    currentReport = report;

    // Show Results Area
    document.getElementById("results-area").style.display = "block";
    document.getElementById("results-area").scrollIntoView({ behavior: "smooth" });

    // Render All Sections
    renderKPIs(report);
    renderBugsAndRCA(report);
    renderSecurity(report);
    renderGeneratedTests(report);
    renderCodeQuality(report);
    renderSummaryAndRecommendations(report);
  } catch (err) {
    console.error("Report rendering error:", err);
  }
}

/**
 * Render Top KPI Cards
 */
function renderKPIs(report) {
  const scores = report.scores || {};
  const summary = report.summary || {};

  // Quality Score
  const qScore = scores.quality || 0;
  document.getElementById("kpi-quality-score").textContent = qScore;
  document.getElementById("bar-quality").style.width = `${qScore}%`;

  // Security Score
  const sScore = scores.security || 0;
  document.getElementById("kpi-security-score").textContent = sScore;
  document.getElementById("bar-security").style.width = `${sScore}%`;

  // Test Pass Rate
  const passRate = scores.test_pass_rate || 0;
  document.getElementById("kpi-pass-rate").textContent = passRate;
  document.getElementById("bar-tests").style.width = `${passRate}%`;

  // Coverage
  const cov = scores.coverage || 0;
  document.getElementById("kpi-coverage").textContent = cov;
  document.getElementById("bar-coverage").style.width = `${cov}%`;

  // Defects
  const totalBugs = summary.total_bugs || (report.bugs ? report.bugs.length : 0);
  document.getElementById("kpi-bug-count").textContent = totalBugs;
  document.getElementById("pill-critical").textContent = `${summary.critical || 0} Critical`;
  document.getElementById("pill-major").textContent = `${summary.major || 0} Major`;
  document.getElementById("pill-minor").textContent = `${summary.minor || 0} Minor`;

  // Tab Badge Counters
  document.getElementById("tab-bug-count").textContent = totalBugs;
  document.getElementById("tab-sec-count").textContent =
    report.security && report.security.findings ? report.security.findings.length : 0;
  document.getElementById("tab-test-count").textContent = summary.tests_total || 0;
}

/**
 * Render Bugs Table & RCA Integration
 */
function renderBugsAndRCA(report) {
  const tbody = document.getElementById("bugs-table-body");
  tbody.innerHTML = "";

  const bugs = report.bugs || [];
  const rcaList = report.root_cause_analysis || [];

  if (bugs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-muted" style="text-align:center;">No bugs detected in codebase.</td></tr>`;
    return;
  }

  bugs.forEach((bug) => {
    const tr = document.createElement("tr");
    tr.className = "clickable-row";

    const sevClass =
      bug.severity === "Critical"
        ? "pill-critical"
        : bug.severity === "Major"
        ? "pill-major"
        : "pill-minor";

    tr.innerHTML = `
      <td class="font-mono font-bold">${bug.bug_id}</td>
      <td><span class="pill ${sevClass}">${bug.severity}</span></td>
      <td>${bug.category || "General"}</td>
      <td class="font-mono">${bug.file}</td>
      <td class="font-mono">${bug.line || "-"}</td>
      <td class="font-mono">${bug.function || "-"}</td>
      <td>${bug.description}</td>
      <td><button class="btn btn-xs btn-secondary">Inspect RCA</button></td>
    `;

    // Click handler to open RCA drawer
    tr.addEventListener("click", () => {
      const matchRca = rcaList.find((r) => r.bug_id === bug.bug_id) || {
        root_cause: "Missing validation or boundary check for edge input.",
        affected_component: `${bug.file} → ${bug.function}()`,
        business_impact: "May lead to runtime crash or service disruption.",
        technical_impact: "Unhandled exception propagates up call stack.",
        fix_suggestion: "Add input validation and defensive guard clause.",
        fix_complexity: "Low",
        confidence: bug.confidence || 90,
      };
      displayRCA(bug, matchRca);
    });

    tbody.appendChild(tr);
  });
}

/**
 * Display RCA Drawer with AI Insights
 */
function displayRCA(bug, rca) {
  const drawer = document.getElementById("rca-drawer");
  drawer.style.display = "block";
  drawer.scrollIntoView({ behavior: "smooth", block: "nearest" });

  document.getElementById("rca-badge").textContent = bug.bug_id;
  document.getElementById("rca-badge").className =
    bug.severity === "Critical" ? "badge badge-danger" : "badge badge-pulse demo";
  document.getElementById("rca-title").textContent = `RCA: ${bug.description}`;

  document.getElementById("rca-why").textContent = rca.root_cause || "Analyzing...";
  document.getElementById("rca-component").textContent =
    rca.affected_component || `${bug.file} → ${bug.function}()`;
  document.getElementById("rca-business").textContent =
    rca.business_impact || "Potential risk to application integrity.";
  document.getElementById("rca-technical").textContent =
    rca.technical_impact || "Direct code failure under specific inputs.";

  document.getElementById("rca-complexity").textContent = rca.fix_complexity || "Low";
  document.getElementById("rca-confidence").textContent = `${rca.confidence || 94}%`;
  document.getElementById("rca-fix-code").textContent =
    rca.fix_suggestion || "# Review logic and add guard conditions";
}

/**
 * Render Security Vulnerabilities Table
 */
function renderSecurity(report) {
  const tbody = document.getElementById("security-table-body");
  tbody.innerHTML = "";

  const sec = report.security || {};
  const findings = sec.findings || [];

  if (findings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-muted" style="text-align:center;">No security issues identified.</td></tr>`;
    return;
  }

  findings.forEach((f) => {
    const tr = document.createElement("tr");
    const sevClass =
      f.severity === "Critical"
        ? "pill-critical"
        : f.severity === "High" || f.severity === "Major"
        ? "pill-major"
        : "pill-minor";

    tr.innerHTML = `
      <td class="font-mono font-bold">${f.code || "SEC-01"}</td>
      <td><span class="pill ${sevClass}">${f.severity}</span></td>
      <td class="font-mono">${f.file}</td>
      <td class="font-mono">${f.line || "-"}</td>
      <td>${f.description}</td>
      <td class="text-muted">${f.recommendation || "Sanitize inputs and store secrets in env variables."}</td>
    `;
    tbody.appendChild(tr);
  });
}

/**
 * Render Generated Tests & Pass/Fail stats
 */
function renderGeneratedTests(report) {
  const codeBlock = document.getElementById("generated-tests-code");
  codeBlock.textContent = report.test_cases_generated || "# No tests were generated.";

  const testStats = document.getElementById("test-stats-summary");
  const tr = report.test_results || {};
  testStats.innerHTML = `
    <span class="pill pill-minor">Total: ${tr.total || 0}</span>
    <span class="pill" style="background:rgba(16,185,129,0.2); color:#34d399;">Passed: ${tr.passed || 0}</span>
    <span class="pill pill-critical">Failed: ${tr.failed || 0}</span>
  `;
}

/**
 * Render Code Quality & Coverage Breakdown
 */
function renderCodeQuality(report) {
  // AST Metrics
  const astContainer = document.getElementById("ast-metrics-list");
  astContainer.innerHTML = "";
  const cq = report.code_quality || {};
  const ast = cq.ast_metrics || {};

  const metrics = [
    { name: "Files Analyzed", val: ast.files_analyzed || report.project?.files || 0 },
    { name: "Total Functions", val: ast.total_functions || 0 },
    { name: "Total Classes", val: ast.total_classes || 0 },
    { name: "Average Cyclomatic Complexity", val: ast.avg_complexity || "1.0" },
  ];

  metrics.forEach((m) => {
    const div = document.createElement("div");
    div.className = "metric-item";
    div.innerHTML = `<span class="name">${m.name}</span><span class="val">${m.val}</span>`;
    astContainer.appendChild(div);
  });

  // Coverage List
  const covContainer = document.getElementById("file-coverage-list");
  covContainer.innerHTML = "";
  const byFile = report.coverage?.by_file || {};

  if (Object.keys(byFile).length === 0) {
    covContainer.innerHTML = `<div class="text-muted">Line coverage calculated project-wide: ${report.scores?.coverage || 0}%</div>`;
  } else {
    for (const [fname, stats] of Object.entries(byFile)) {
      const pct = stats.percentage || 0;
      const row = document.createElement("div");
      row.innerHTML = `
        <div class="coverage-item-row">
          <span class="font-mono">${fname}</span>
          <span class="font-mono font-bold">${pct}%</span>
        </div>
        <div class="meter-bar">
          <div class="meter-fill meter-info" style="width: ${pct}%;"></div>
        </div>
      `;
      covContainer.appendChild(row);
    }
  }

  // Linter Table
  const linterBody = document.getElementById("linter-table-body");
  linterBody.innerHTML = "";
  const issues = cq.issues || [];

  if (issues.length === 0) {
    linterBody.innerHTML = `<tr><td colspan="5" class="text-muted" style="text-align:center;">No linter issues found.</td></tr>`;
  } else {
    issues.forEach((item) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td class="font-mono font-bold">${item.code || "LINT"}</td>
        <td class="font-mono">${item.file}</td>
        <td class="font-mono">${item.line || "-"}</td>
        <td>${item.message}</td>
        <td><span class="pill pill-minor">${item.severity || "info"}</span></td>
      `;
      linterBody.appendChild(row);
    });
  }
}

/**
 * Render Executive Summary & Recommendations
 */
function renderSummaryAndRecommendations(report) {
  document.getElementById("executive-summary-text").textContent =
    report.executive_summary || "Executive summary generated.";

  const recList = document.getElementById("recommendations-list");
  recList.innerHTML = "";
  const recs = report.recommendations || [];

  recs.forEach((rec) => {
    const li = document.createElement("li");
    li.textContent = rec;
    recList.appendChild(li);
  });

  // Approval Status
  updateApprovalBadge(report.approval_status || "pending");
}

/**
 * Handle Human-in-the-loop Sign-off
 */
async function submitApproval(decision) {
  if (!currentJobId) {
    showToast("No active QA report to approve.", "error");
    return;
  }

  const notes = document.getElementById("approval-notes").value;

  try {
    const res = await fetch(`/api/approve/${currentJobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, notes }),
    });

    if (!res.ok) throw new Error("Approval submission failed");
    const data = await res.json();

    updateApprovalBadge(decision);
    logActivity("Supervisor", `Human Review: Marked as ${decision.toUpperCase()}. Notes: "${notes || 'None'}"`, "success");
    showToast(`Report marked as ${decision.toUpperCase()}!`, "success");
  } catch (err) {
    showToast(`Approval error: ${err.message}`, "error");
  }
}

function updateApprovalBadge(status) {
  const badge = document.getElementById("approval-status-badge");
  if (status === "approved") {
    badge.textContent = "Status: Approved by QA Lead ✓";
    badge.className = "approval-status-badge approved";
  } else if (status === "rejected") {
    badge.textContent = "Status: Rejected / Re-analysis Requested ✕";
    badge.className = "approval-status-badge rejected";
  } else {
    badge.textContent = "Status: Pending Approval";
    badge.className = "approval-status-badge";
  }
}

/**
 * Display floating toast notification
 */
function showToast(message, type = "info", duration = 4000) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const icon = type === "success" ? "✓" : type === "error" ? "✕" : "ℹ";
  toast.innerHTML = `<span style="font-weight:bold;">${icon}</span> <span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/**
 * Append entry to live activity terminal
 */
function logActivity(agent, message, type = "normal") {
  const terminal = document.getElementById("agent-logs-terminal");
  if (!terminal) return;
  const time = new Date().toLocaleTimeString();

  const line = document.createElement("div");
  line.className = "log-line";

  const msgClass = type === "error" ? "log-msg error" : type === "success" ? "log-msg success" : "log-msg";

  line.innerHTML = `
    <span class="log-time">[${time}]</span>
    <span class="log-agent">[${agent}]</span>
    <span class="${msgClass}">${message}</span>
  `;

  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
}

/**
 * Reset UI before starting new run
 */
function resetUI() {
  document.getElementById("results-area").style.display = "none";
  document.getElementById("progress-percent").textContent = "0% Completed";
  document.getElementById("pipeline-progress-bar").style.width = "0%";

  AGENTS.forEach((agent) => {
    const node = document.getElementById(`node-${agent}`);
    const stateLabel = document.getElementById(`state-${agent}`);
    if (node) node.className = "agent-node";
    if (stateLabel) stateLabel.textContent = "Pending";
  });
}

function formatAgentName(key) {
  return key
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
