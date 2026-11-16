/**
 * app.js - Frontend logic for Discrete Mathematics Fest Team Optimizer
 */

let allStudents = [];
let conflictEdges = [];
let selectedMemberIds = new Set();
let canvas, ctx;

document.addEventListener("DOMContentLoaded", () => {
    initCanvas();
    setupEventListeners();
    fetchDatasetAndRun();
});

function initCanvas() {
    canvas = document.getElementById("conflictCanvas");
    ctx = canvas.getContext("2d");
    // Handle retina display crispness
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
}

function setupEventListeners() {
    // Sliders
    bindSlider("teamSizeSlider", "teamSizeVal");
    bindSlider("minSeniorsSlider", "minSeniorsVal");
    bindSlider("minJuniorsSlider", "minJuniorsVal");
    bindSlider("minSkillsSlider", "minSkillsVal");
    bindSlider("lambdaSlider", "lambdaVal");

    // Action buttons
    document.getElementById("optimizeBtn").addEventListener("click", runOptimization);
    document.getElementById("sidebarOptimizeBtn").addEventListener("click", runOptimization);

    // Search filter
    document.getElementById("poolSearchInput").addEventListener("input", (e) => {
        renderStudentTable(e.target.value);
    });

    // Math Modal
    const modal = document.getElementById("mathModal");
    document.getElementById("openMathModalBtn").addEventListener("click", () => {
        modal.classList.add("open");
    });
    document.getElementById("closeMathModalBtn").addEventListener("click", () => {
        modal.classList.remove("open");
    });
    modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.classList.remove("open");
    });

    window.addEventListener("resize", () => {
        initCanvas();
        drawConflictGraph();
    });
}

function bindSlider(sliderId, labelId) {
    const slider = document.getElementById(sliderId);
    const label = document.getElementById(labelId);
    slider.addEventListener("input", () => {
        label.textContent = slider.value;
    });
}

async function fetchDatasetAndRun() {
    try {
        const res = await fetch("/api/dataset");
        const data = await res.json();
        allStudents = data.students;
        conflictEdges = data.edges;
        renderStudentTable();
        await runOptimization();
    } catch (err) {
        console.error("Failed to load initial dataset:", err);
    }
}

async function runOptimization() {
    const btn = document.getElementById("optimizeBtn");
    const spinner = document.getElementById("btnSpinner");
    const btnText = document.getElementById("btnText");

    spinner.style.display = "inline-block";
    btnText.textContent = "Optimizing...";
    btn.disabled = true;

    const payload = {
        team_size: parseInt(document.getElementById("teamSizeSlider").value),
        min_seniors: parseInt(document.getElementById("minSeniorsSlider").value),
        min_juniors: parseInt(document.getElementById("minJuniorsSlider").value),
        min_skills: parseInt(document.getElementById("minSkillsSlider").value),
        lambda_weight: parseFloat(document.getElementById("lambdaSlider").value),
        run_naive: document.getElementById("runNaiveCheckbox").checked,
    };

    try {
        const res = await fetch("/api/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        updateUIWithResults(data);
    } catch (err) {
        console.error("Optimization query failed:", err);
    } finally {
        spinner.style.display = "none";
        btnText.textContent = "Run Optimization";
        btn.disabled = false;
    }
}

function updateUIWithResults(data) {
    if (!data.success) {
        alert("No feasible team found satisfying these constraints! Try loosening senior, junior, or skill requirements.");
        return;
    }

    selectedMemberIds = new Set(data.team.member_ids);

    // 1. Stats Bar
    document.getElementById("statCombinations").textContent = data.bnb_stats.combinations_space.toLocaleString();
    document.getElementById("statNodesVisited").textContent = data.bnb_stats.nodes_visited.toLocaleString();
    document.getElementById("statBnbTime").textContent = `${data.bnb_stats.time_ms.toFixed(2)} ms`;
    document.getElementById("statObjective").textContent = data.team.objective_value.toFixed(3);
    document.getElementById("statVarianceSub").textContent = `Score: ${data.team.total_score} | Var: ${data.team.variance.toFixed(3)}`;

    // 2. Comparison Table
    document.getElementById("tblBnbSpace").textContent = data.bnb_stats.combinations_space.toLocaleString();
    document.getElementById("tblBnbNodes").textContent = data.bnb_stats.nodes_visited.toLocaleString();
    document.getElementById("tblBnbLeaves").textContent = data.bnb_stats.leaves_evaluated.toLocaleString();
    document.getElementById("tblBnbFeasible").textContent = data.bnb_stats.feasible_found.toLocaleString();
    document.getElementById("tblBnbTime").textContent = `${data.bnb_stats.time_ms.toFixed(2)} ms`;

    if (data.naive_stats) {
        document.getElementById("tblNaiveSpace").textContent = data.naive_stats.combinations_space.toLocaleString();
        document.getElementById("tblNaiveNodes").textContent = data.naive_stats.nodes_visited.toLocaleString();
        document.getElementById("tblNaiveLeaves").textContent = data.naive_stats.leaves_evaluated.toLocaleString();
        document.getElementById("tblNaiveFeasible").textContent = data.naive_stats.feasible_found.toLocaleString();
        document.getElementById("tblNaiveTime").textContent = `${data.naive_stats.time_ms.toFixed(2)} ms`;
        document.getElementById("tblNodeReduction").textContent = `${data.naive_stats.node_reduction_pct.toFixed(1)}% eliminated`;
        document.getElementById("tblSpeedupFactor").textContent = `${data.naive_stats.speedup_factor.toFixed(1)}x faster`;
        document.getElementById("speedupPill").textContent = `${data.naive_stats.speedup_factor.toFixed(0)}x Speedup`;
        document.getElementById("statSpeedupBadge").textContent = `${data.naive_stats.speedup_factor.toFixed(0)}x faster than naive search`;
    }

    // 3. Optimal Team Members Grid
    renderTeamMembers(data.team);

    // 4. Verification Strip
    document.getElementById("vSeniors").textContent = `${data.team.senior_count} Seniors (${data.team.senior_count >= 2 ? "Qualified" : "Deficit"})`;
    document.getElementById("vJuniors").textContent = `${data.team.junior_count} Junior (${data.team.junior_count >= 1 ? "Qualified" : "Deficit"})`;
    document.getElementById("vSkills").textContent = `${data.team.unique_skills.length} Unique Skills (${data.team.unique_skills.join(", ")})`;

    // 5. Pruning Taxonomy
    renderPruningBreakdown(data.bnb_stats.pruning_breakdown, data.bnb_stats.total_pruned);

    // 6. Redraw Conflict Graph with Team Highlight
    drawConflictGraph();

    // 7. Update Student Pool Table statuses
    renderStudentTable(document.getElementById("poolSearchInput").value);
}

function renderTeamMembers(team) {
    const grid = document.getElementById("teamMembersGrid");
    grid.innerHTML = "";

    document.getElementById("teamScoreBadge").textContent = `Total Score: ${team.total_score} / ${team.members.length * 5}`;
    document.getElementById("teamVarBadge").textContent = `Variance: ${team.variance.toFixed(4)} (μ = ${team.mean_score})`;

    team.members.forEach(s => {
        const card = document.createElement("div");
        card.className = "member-card";
        const stars = "★".repeat(s.rating) + "☆".repeat(5 - s.rating);
        const skillClass = getSkillBadgeClass(s.skill);

        card.innerHTML = `
            <div class="member-header">
                <span class="member-id">#${s.id}</span>
                <span class="badge ${s.level === 'Senior' ? 'badge-purple' : 'badge-cyan'}">${s.level} (Y${s.year})</span>
            </div>
            <div class="member-name">${s.name}</div>
            <div class="member-year-role">${s.skill} Specialist</div>
            <div class="member-skill-row">
                <span class="badge ${skillClass}">${s.skill}</span>
                <span class="rating-stars">${stars}</span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderPruningBreakdown(breakdown, total) {
    const list = document.getElementById("pruningList");
    list.innerHTML = "";
    document.getElementById("totalPrunedBadge").textContent = `${total.toLocaleString()} Subtrees Pruned`;

    const labels = {
        upper_bound: "Upper Bounding (f(T) <= Best Objective)",
        conflict: "Interpersonal Conflict (Conflict Graph Edge)",
        capacity: "Capacity Shortfall (|T| + Rem < k)",
        senior_deficit: "Senior Quota Deficit (Seniors < 2)",
        junior_deficit: "Junior Quota Deficit (Juniors < 1)",
        skill_deficit: "Skill Diversity Deficit (Distinct < 3)",
    };

    for (const [key, label] of Object.entries(labels)) {
        const count = breakdown[key] || 0;
        const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;

        const item = document.createElement("div");
        item.className = "pruning-item";
        item.innerHTML = `
            <div class="pruning-header">
                <span class="pruning-title">${label}</span>
                <span class="pruning-count">${count.toLocaleString()} (${pct}%)</span>
            </div>
            <div class="pruning-bar-track">
                <div class="pruning-bar-fill" style="width: ${pct}%"></div>
            </div>
        `;
        list.appendChild(item);
    }
}

function drawConflictGraph() {
    if (!ctx || allStudents.length === 0) return;

    const width = canvas.width / (window.devicePixelRatio || 1);
    const height = canvas.height / (window.devicePixelRatio || 1);
    ctx.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) - 40;

    // Compute circular node positions
    const nodePositions = [];
    const n = allStudents.length;
    for (let i = 0; i < n; i++) {
        const angle = (2 * Math.PI * i) / n - Math.PI / 2;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        nodePositions.push({ x, y });
    }

    // 1. Draw Conflict Edges
    ctx.lineWidth = 1.5;
    conflictEdges.forEach(edge => {
        const p1 = nodePositions[edge.source];
        const p2 = nodePositions[edge.target];
        if (!p1 || !p2) return;

        ctx.strokeStyle = "rgba(244, 63, 94, 0.35)";
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
    });

    // 2. Draw Nodes
    for (let i = 0; i < n; i++) {
        const pos = nodePositions[i];
        const isSelected = selectedMemberIds.has(i);

        ctx.beginPath();
        if (isSelected) {
            ctx.arc(pos.x, pos.y, 14, 0, 2 * Math.PI);
            ctx.fillStyle = "#10b981";
            ctx.shadowColor = "#10b981";
            ctx.shadowBlur = 15;
            ctx.fill();
            ctx.shadowBlur = 0;

            ctx.lineWidth = 2.5;
            ctx.strokeStyle = "#ffffff";
            ctx.stroke();
        } else {
            ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI);
            ctx.fillStyle = "#334155";
            ctx.fill();
            ctx.lineWidth = 1;
            ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
            ctx.stroke();
        }

        // Node ID Label
        ctx.fillStyle = isSelected ? "#052e16" : "#cbd5e1";
        ctx.font = isSelected ? "bold 10px JetBrains Mono" : "9px JetBrains Mono";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(i.toString(), pos.x, pos.y);
    }
}

function renderStudentTable(filterText = "") {
    const tbody = document.getElementById("poolTableBody");
    tbody.innerHTML = "";

    const query = filterText.toLowerCase().trim();
    const filtered = allStudents.filter(s => {
        if (!query) return true;
        return (
            s.name.toLowerCase().includes(query) ||
            s.skill.toLowerCase().includes(query) ||
            `y${s.year}`.toLowerCase().includes(query) ||
            s.level.toLowerCase().includes(query)
        );
    });

    filtered.forEach(s => {
        const tr = document.createElement("tr");
        const isSelected = selectedMemberIds.has(s.id);
        const conflictsStr = s.conflicts.length > 0 ? s.conflicts.join(", ") : "None";
        const stars = "★".repeat(s.rating) + "☆".repeat(5 - s.rating);
        const skillClass = getSkillBadgeClass(s.skill);

        tr.innerHTML = `
            <td><strong>#${s.id}</strong></td>
            <td><strong>${s.name}</strong></td>
            <td>Y${s.year}</td>
            <td><span class="badge ${s.level === 'Senior' ? 'badge-purple' : 'badge-cyan'}">${s.level}</span></td>
            <td><span class="badge ${skillClass}">${s.skill}</span></td>
            <td><span class="text-amber">${stars} (${s.rating}/5)</span></td>
            <td>${conflictsStr}</td>
            <td>
                ${isSelected 
                    ? '<span class="badge badge-emerald">Selected in Team</span>' 
                    : '<span class="text-muted">Available</span>'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function getSkillBadgeClass(skill) {
    switch (skill) {
        case "Tech": return "badge-cyan";
        case "Design": return "badge-purple";
        case "Sponsorship": return "badge-amber";
        case "Logistics": return "badge-emerald";
        case "Marketing": return "badge-rose";
        default: return "badge-cyan";
    }
}
