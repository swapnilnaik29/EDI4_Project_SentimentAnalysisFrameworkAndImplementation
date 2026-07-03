document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide Icons
    lucide.createIcons();

    // Chart Registry to prevent canvas overlap exceptions
    const chartRegistry = {};

    // App State
    const state = {
        currentPage: 1,
        limit: 10,
        filters: {
            search: "",
            topic_id: "",
            severity: "",
            user_type: "",
            source: "",
            date_start: "",
            date_end: ""
        },
        selectedTopicId: null,
        webSocket: null,
        sortBy: "date",
        sortOrder: "desc",
        currentComplaints: []
    };

    // DOM Elements
    const themeToggle = document.getElementById("themeToggle");
    const tabButtons = document.querySelectorAll(".nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const feedPulseDot = document.querySelector(".pulse-dot");

    // Metrics DOM
    const metricTotal = document.getElementById("metricTotal");
    const metricLive = document.getElementById("metricLive");
    const metricIntensity = document.getElementById("metricIntensity");
    const intensityProgressBar = document.getElementById("intensityProgressBar");
    const anomalyStatus = document.getElementById("anomalyStatus");
    const spikeAlertBanner = document.getElementById("spikeAlertBanner");

    // Filter Controls
    const filterSearch = document.getElementById("filterSearch");
    const filterTopic = document.getElementById("filterTopic");
    const filterSeverity = document.getElementById("filterSeverity");
    const filterUserType = document.getElementById("filterUserType");
    const filterSource = document.getElementById("filterSource");
    const resetFiltersBtn = document.getElementById("resetFiltersBtn");

    // Action Buttons
    const exportCsvBtn = document.getElementById("exportCsvBtn");
    const retrainBtn = document.getElementById("retrainBtn");

    // Table Ledger DOM
    const ledgerTableBody = document.getElementById("ledgerTableBody");
    const ledgerCountText = document.getElementById("ledgerCountText");
    const prevPageBtn = document.getElementById("prevPageBtn");
    const nextPageBtn = document.getElementById("nextPageBtn");
    const pageIndicator = document.getElementById("pageIndicator");

    // Modal DOM
    const detailModal = document.getElementById("detailModal");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const modalTopicBadge = document.getElementById("modalTopicBadge");
    const modalTitle = document.getElementById("modalTitle");
    const modalOriginalText = document.getElementById("modalOriginalText");
    const modalUserType = document.getElementById("modalUserType");
    const modalSource = document.getElementById("modalSource");
    const modalDate = document.getElementById("modalDate");
    const modalTime = document.getElementById("modalTime");
    const modalLocation = document.getElementById("modalLocation");
    const modalID = document.getElementById("modalID");
    const modalSentimentIcon = document.getElementById("modalSentimentIcon");
    const modalSentimentLabel = document.getElementById("modalSentimentLabel");
    const modalSentimentScore = document.getElementById("modalSentimentScore");
    const modalIntensityValue = document.getElementById("modalIntensityValue");
    const modalIntensityBar = document.getElementById("modalIntensityBar");
    const modalSeverityCard = document.getElementById("modalSeverityCard");
    const modalSeverityLabelText = document.getElementById("modalSeverityLabelText");
    const modalAISummary = document.getElementById("modalAISummary");
    const modalRootCause = document.getElementById("modalRootCause");
    const modalRecommendedDept = document.getElementById("modalRecommendedDept");
    const modalEscalationPriority = document.getElementById("modalEscalationPriority");
    const modalSolvingSteps = document.getElementById("modalSolvingSteps");

    // Live Feed Logs
    const liveStreamLogs = document.getElementById("liveStreamLogs");

    // Drilldown DOM
    const drilldownTopicsList = document.getElementById("drilldownTopicsList");
    const drilldownDetailsContainer = document.getElementById("drilldownDetailsContainer");

    // ---------------------------------------------------------
    // 1. Theme Configuration
    // ---------------------------------------------------------
    themeToggle.addEventListener("change", () => {
        const theme = themeToggle.checked ? "dark" : "light";
        document.body.setAttribute("data-theme", theme);
    });

    // ---------------------------------------------------------
    // 2. Navigation Tabs Configuration
    // ---------------------------------------------------------
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabName = btn.getAttribute("data-tab");
            
            // Toggle buttons
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            // Toggle panes
            tabPanes.forEach(pane => {
                pane.classList.remove("active");
                if (pane.id === `tab-${tabName}`) {
                    pane.classList.add("active");
                }
            });

            // If entering feed, hide the unread pulse dot
            if (tabName === "feed") {
                feedPulseDot.style.display = "none";
            }
            
            // Refresh specific pane structures if needed
            if (tabName === "drilldown") {
                loadDrilldownTopics();
            }
        });
    });

    // ---------------------------------------------------------
    // 3. API Load Data: Analytics & Table
    // ---------------------------------------------------------
    async function loadAnalytics() {
        const queryStr = getFilterQueryString();
        try {
            const response = await fetch(`/api/analytics?${queryStr}`);
            if (!response.ok) throw new Error("Failed to load metrics");
            
            const metrics = await response.json();
            
            // Set basic numbers
            metricTotal.textContent = metrics.total_complaints;
            metricLive.textContent = metrics.live_count;
            metricIntensity.textContent = metrics.intensity_average;
            intensityProgressBar.style.width = `${metrics.intensity_average * 100}%`;
            
            // Spike Monitor Status
            if (metrics.recent_spikes) {
                anomalyStatus.className = "anomaly-status spiking";
                anomalyStatus.innerHTML = `<i data-lucide="zap"></i> <span>VOLUME SPIKE DETECTED</span>`;
                spikeAlertBanner.style.display = "block";
            } else {
                anomalyStatus.className = "anomaly-status normal";
                anomalyStatus.innerHTML = `<i data-lucide="check-circle-2"></i> <span>No anomaly detected</span>`;
                spikeAlertBanner.style.display = "none";
            }
            lucide.createIcons();

            // AI Insights List
            const insightsHtml = metrics.ai_insights.map(ins => `<li>${ins}</li>`).join("");
            document.getElementById("insightsList").innerHTML = insightsHtml;

            // Render Chart.js visual data
            renderCharts(metrics);
        } catch (error) {
            console.error(error);
        }
    }

    function renderLedgerTable(items) {
        let tableHtml = "";
        items.forEach(c => {
            const dateStr = c.complaint_date || "Unknown";
            const topic = c.topic_label || "Uncategorized";
            const abstract = c.ai_summary || c.complaint_text.substring(0, 50) + "...";
            
            // Severity tag styling
            const sevClass = c.severity || "medium";
            
            // Intensity text styling
            let intStyle = "low";
            if (c.intensity_score >= 0.8) intStyle = "high";
            else if (c.intensity_score >= 0.4) intStyle = "mid";

            tableHtml += `
                <tr>
                    <td class="text-bold">${dateStr}</td>
                    <td class="capitalize">${c.user_type}</td>
                    <td><span class="capitalize text-bold">${topic}</span></td>
                    <td><div class="text-snippet" title="${c.complaint_text}">${abstract}</div></td>
                    <td><span class="badge-sev ${sevClass}">${c.severity}</span></td>
                    <td><span class="intensity-badge ${intStyle}">${c.intensity_score.toFixed(2)}</span></td>
                    <td class="actions-header">
                        <button class="analyze-btn" data-id="${c.complaint_id}">
                            <i data-lucide="eye"></i> Analyze
                        </button>
                    </td>
                </tr>
            `;
        });
        
        ledgerTableBody.innerHTML = tableHtml;
        lucide.createIcons();
        
        // Add click events to analyze buttons
        document.querySelectorAll(".analyze-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                openDetailModal(btn.getAttribute("data-id"));
            });
        });
    }

    function sortComplaints(items, sortBy, sortOrder) {
        const direction = sortOrder === "asc" ? 1 : -1;
        
        return items.sort((a, b) => {
            let valA, valB;
            
            switch (sortBy) {
                case "date":
                    valA = new Date(a.timestamp || a.created_at || 0);
                    valB = new Date(b.timestamp || b.created_at || 0);
                    return (valA - valB) * direction;
                case "user_type":
                    valA = a.user_type || "";
                    valB = b.user_type || "";
                    return valA.localeCompare(valB) * direction;
                case "topic_label":
                    valA = a.topic_label || "";
                    valB = b.topic_label || "";
                    return valA.localeCompare(valB) * direction;
                case "ai_summary":
                    valA = a.ai_summary || a.complaint_text || "";
                    valB = b.ai_summary || b.complaint_text || "";
                    return valA.localeCompare(valB) * direction;
                case "severity":
                    const severityWeight = { low: 1, medium: 2, high: 3, critical: 4 };
                    valA = severityWeight[a.severity] || 0;
                    valB = severityWeight[b.severity] || 0;
                    return (valA - valB) * direction;
                case "intensity_score":
                    valA = a.intensity_score || 0;
                    valB = b.intensity_score || 0;
                    return (valA - valB) * direction;
                default:
                    // default sort by timestamp desc
                    valA = new Date(a.timestamp || a.created_at || 0);
                    valB = new Date(b.timestamp || b.created_at || 0);
                    return (valA - valB) * -1;
            }
        });
    }

    function updateSortIcons() {
        document.querySelectorAll("th.sortable").forEach(th => {
            const col = th.getAttribute("data-sort-by");
            const icon = th.querySelector(".sort-btn i");
            if (icon) {
                if (state.sortBy === col) {
                    icon.setAttribute("data-lucide", state.sortOrder === "asc" ? "arrow-up" : "arrow-down");
                    icon.classList.add("active");
                } else {
                    icon.setAttribute("data-lucide", "arrow-up-down");
                    icon.classList.remove("active");
                }
            }
        });
        lucide.createIcons();
    }

    async function loadLedgerTable() {
        renderTableSkeleton();
        const queryStr = getFilterQueryString() + `&page=${state.currentPage}&limit=${state.limit}`;
        
        try {
            const response = await fetch(`/api/complaints?${queryStr}`);
            if (!response.ok) throw new Error("Failed to fetch complaints ledger");
            
            const data = await response.json();
            state.currentComplaints = data.items || [];
            
            if (state.currentComplaints.length === 0) {
                ledgerTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--color-text-muted);">No complaints found matching filters.</td></tr>`;
                ledgerCountText.textContent = "Showing 0 complaints";
                prevPageBtn.disabled = true;
                nextPageBtn.disabled = true;
                return;
            }

            ledgerCountText.textContent = `Showing ${(state.currentPage-1)*state.limit + 1} - ${Math.min(state.currentPage*state.limit, data.total)} of ${data.total} complaints`;
            
            // Sort cached list
            sortComplaints(state.currentComplaints, state.sortBy, state.sortOrder);
            
            // Render table
            renderLedgerTable(state.currentComplaints);
            
            // Update sort UI icons
            updateSortIcons();

            // Pagination state
            prevPageBtn.disabled = state.currentPage === 1;
            nextPageBtn.disabled = state.currentPage >= data.pages;
            pageIndicator.textContent = `Page ${state.currentPage} of ${Math.max(1, data.pages)}`;
        } catch (error) {
            console.error(error);
            ledgerTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--color-danger);">Failed to load database ledger.</td></tr>`;
        }
    }

    async function fetchTopicsDropdown() {
        try {
            const response = await fetch("/api/analytics/topics");
            if (!response.ok) throw new Error();
            const topics = await response.json();
            
            // Cache current selected topic id
            const currentSelected = filterTopic.value;
            
            let dropdownHtml = '<option value="">All Dynamic Topics</option>';
            topics.forEach(t => {
                if (t.topic_id !== -1) {
                    dropdownHtml += `<option value="${t.topic_id}">${t.topic_label} (${t.complaint_count})</option>`;
                }
            });
            filterTopic.innerHTML = dropdownHtml;
            filterTopic.value = currentSelected;
        } catch (error) {
            console.error("Failed to load topics list dropdown");
        }
    }

    function renderTableSkeleton() {
        ledgerTableBody.innerHTML = `
            <tr class="skeleton-row"><td colspan="7"></td></tr>
            <tr class="skeleton-row"><td colspan="7"></td></tr>
            <tr class="skeleton-row"><td colspan="7"></td></tr>
        `;
    }

    // ---------------------------------------------------------
    // 4. Charts Configurations (Chart.js wrapper)
    // ---------------------------------------------------------
    async function loadTrendChart() {
        try {
            const response = await fetch("/api/analytics/trends?days=7");
            if (!response.ok) throw new Error();
            const trendData = await response.json();
            
            const labels = trendData.map(p => p.date);
            const counts = trendData.map(p => p.count);
            
            createOrUpdateChart("trendChart", "line", {
                labels: labels,
                datasets: [{
                    label: "Complaints Count",
                    data: counts,
                    borderColor: "#3b82f6",
                    backgroundColor: "rgba(59, 130, 246, 0.05)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: "#3b82f6"
                }]
            }, {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: "rgba(150, 150, 150, 0.8)" },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    },
                    x: {
                        ticks: { color: "rgba(150, 150, 150, 0.8)" },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    }
                }
            });
        } catch (error) {
            console.error("Failed to generate trend chart: " + error);
        }
    }

    function renderCharts(metrics) {
        // Line Trend
        loadTrendChart();

        // 1. Horizontal bar: Topics distribution
        const topicLabels = Object.keys(metrics.topic_distribution);
        const topicCounts = Object.values(metrics.topic_distribution);
        createOrUpdateChart("topicsChart", "bar", {
            labels: topicLabels,
            datasets: [{
                data: topicCounts,
                backgroundColor: "rgba(13, 148, 136, 0.65)",
                borderColor: "#0d9488",
                borderWidth: 1,
                borderRadius: 4
            }]
        }, {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, color: "rgba(150, 150, 150, 0.8)" },
                    grid: { color: "rgba(255,255,255,0.05)" }
                },
                y: {
                    ticks: { color: "rgba(150, 150, 150, 0.8)" },
                    grid: { display: false }
                }
            }
        });

        // 2. Donut: Sentiment
        const sentLabels = Object.keys(metrics.sentiment_distribution);
        const sentCounts = Object.values(metrics.sentiment_distribution);
        const sentColors = sentLabels.map(l => {
            if (l === "NEGATIVE") return "#ef4444";
            if (l === "POSITIVE") return "#10b981";
            return "#3b82f6";
        });
        createOrUpdateChart("sentimentChart", "doughnut", {
            labels: sentLabels,
            datasets: [{
                data: sentCounts,
                backgroundColor: sentColors,
                borderWidth: 0,
                hoverOffset: 4
            }]
        }, {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: "rgba(200, 200, 200, 0.8)", boxWidth: 12 }
                }
            }
        });

        // 3. Bar/Doughnut: Severity
        const sevLabels = Object.keys(metrics.severity_distribution).map(k => k.toUpperCase());
        const sevCounts = Object.values(metrics.severity_distribution);
        const sevColors = sevLabels.map(l => {
            if (l === "CRITICAL") return "#7f1d1d";
            if (l === "HIGH") return "#f59e0b";
            if (l === "MEDIUM") return "#3b82f6";
            return "#10b981";
        });
        createOrUpdateChart("severityChart", "bar", {
            labels: sevLabels,
            datasets: [{
                data: sevCounts,
                backgroundColor: sevColors,
                borderWidth: 0,
                borderRadius: 4
            }]
        }, {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: "rgba(150, 150, 150, 0.8)" },
                    grid: { color: "rgba(255,255,255,0.05)" }
                },
                x: {
                    ticks: { color: "rgba(150, 150, 150, 0.8)" },
                    grid: { display: false }
                }
            }
        });

        // 4. Donut: Source Channels
        const srcLabels = Object.keys(metrics.source_distribution).map(k => k.toUpperCase());
        const srcCounts = Object.values(metrics.source_distribution);
        createOrUpdateChart("sourceChart", "doughnut", {
            labels: srcLabels,
            datasets: [{
                data: srcCounts,
                backgroundColor: ["#3b82f6", "#0d9488", "#f59e0b", "#8b5cf6", "#ec4899"],
                borderWidth: 0
            }]
        }, {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: "rgba(200, 200, 200, 0.8)", boxWidth: 12 }
                }
            }
        });
    }

    function createOrUpdateChart(canvasId, type, data, options) {
        if (chartRegistry[canvasId]) {
            chartRegistry[canvasId].destroy();
        }
        const ctx = document.getElementById(canvasId).getContext("2d");
        chartRegistry[canvasId] = new Chart(ctx, {
            type: type,
            data: data,
            options: options
        });
    }

    // ---------------------------------------------------------
    // 5. Dynamic Filtering Logic
    // ---------------------------------------------------------
    function getFilterQueryString() {
        const params = new URLSearchParams();
        for (const [key, value] of Object.entries(state.filters)) {
            if (value !== "") {
                params.append(key, value);
            }
        }
        return params.toString();
    }

    function handleFilterChange() {
        state.currentPage = 1;
        loadAnalytics();
        loadLedgerTable();
    }

    // Bind event listeners with small debouncing for search
    let searchDebounceTimer;
    filterSearch.addEventListener("input", () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            state.filters.search = filterSearch.value.trim();
            handleFilterChange();
        }, 400);
    });

    filterTopic.addEventListener("change", () => {
        state.filters.topic_id = filterTopic.value;
        handleFilterChange();
    });

    filterSeverity.addEventListener("change", () => {
        state.filters.severity = filterSeverity.value;
        handleFilterChange();
    });

    filterUserType.addEventListener("change", () => {
        state.filters.user_type = filterUserType.value;
        handleFilterChange();
    });

    filterSource.addEventListener("change", () => {
        state.filters.source = filterSource.value;
        handleFilterChange();
    });

    resetFiltersBtn.addEventListener("click", () => {
        filterSearch.value = "";
        filterTopic.value = "";
        filterSeverity.value = "";
        filterUserType.value = "";
        filterSource.value = "";
        
        state.currentPage = 1;
        state.filters = {
            search: "",
            topic_id: "",
            severity: "",
            user_type: "",
            source: "",
            date_start: "",
            date_end: ""
        };
        
        loadAnalytics();
        loadLedgerTable();
    });

    // Pagination
    prevPageBtn.addEventListener("click", () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            loadLedgerTable();
        }
    });

    nextPageBtn.addEventListener("click", () => {
        state.currentPage++;
        loadLedgerTable();
    });

    // ---------------------------------------------------------
    // 6. CSV Export and Retraining logic
    // ---------------------------------------------------------
    exportCsvBtn.addEventListener("click", () => {
        const queryStr = getFilterQueryString();
        window.open(`/api/complaints/export/csv?${queryStr}`, "_blank");
    });

    retrainBtn.addEventListener("click", async () => {
        retrainBtn.disabled = true;
        const spinner = retrainBtn.querySelector("i");
        spinner.style.animation = "spin 1s linear infinite";
        retrainBtn.querySelector("span").textContent = "Clustering Topics...";

        try {
            const response = await fetch("/api/complaints/retrain", { method: "POST" });
            if (response.ok) {
                // Show notification, the WS will update dropdowns when tasks finished
                alert("Topic model retraining started in backend. This might take a moment. Dashboard will update automatically.");
            } else {
                alert("Failed to start topic retraining.");
                retrainBtn.disabled = false;
                spinner.style.animation = "none";
                retrainBtn.querySelector("span").textContent = "Retrain AI Topics";
            }
        } catch (error) {
            console.error(error);
            alert("Connection error triggering retraining.");
            retrainBtn.disabled = false;
            spinner.style.animation = "none";
            retrainBtn.querySelector("span").textContent = "Retrain AI Topics";
        }
    });

    // ---------------------------------------------------------
    // 7. Immersive Details Modal Mapping
    // ---------------------------------------------------------
    async function openDetailModal(complaintId) {
        try {
            const response = await fetch(`/api/complaints/${complaintId}`);
            if (!response.ok) throw new Error("Could not load details");
            const c = await response.json();
            
            // Map Metadata
            modalTitle.textContent = "AI Analysis Report";
            modalTopicBadge.textContent = c.topic_label || "Uncategorized";
            modalOriginalText.textContent = c.complaint_text;
            modalUserType.textContent = c.user_type;
            modalSource.textContent = c.complaint_source;
            modalDate.textContent = c.complaint_date;
            modalTime.textContent = c.complaint_time;
            modalLocation.textContent = c.location || "Online";
            modalID.textContent = c.complaint_id;
            
            // Sentiment Gauge mapping
            const sLabel = c.sentiment_label || "NEUTRAL";
            modalSentimentLabel.textContent = sLabel;
            modalSentimentScore.textContent = `Confidence Score: ${(c.sentiment_score * 100).toFixed(0)}%`;
            modalSentimentIcon.className = `gauge-face-icon ${sLabel.toLowerCase()}`;
            
            let faceIcon = "smile";
            if (sLabel === "NEGATIVE") faceIcon = "frown";
            else if (sLabel === "NEUTRAL") faceIcon = "meh";
            modalSentimentIcon.innerHTML = `<i data-lucide="${faceIcon}"></i>`;
            
            // Intensity gauge mapping
            modalIntensityValue.textContent = `${c.intensity_score.toFixed(2)} / 1.0`;
            modalIntensityBar.style.width = `${c.intensity_score * 100}%`;
            
            // Severity card mapping
            const sev = c.severity || "medium";
            modalSeverityCard.className = `severity-badge-large ${sev}`;
            modalSeverityLabelText.textContent = sev.toUpperCase();
            
            // AI Texts
            modalAISummary.textContent = c.ai_summary || "No summary generated.";
            modalRootCause.textContent = c.root_cause || "No root cause detected.";
            modalRecommendedDept.textContent = c.recommended_department || "General Operations";
            
            const escPriority = c.escalation_priority || "low";
            modalEscalationPriority.textContent = escPriority.toUpperCase();
            modalEscalationPriority.className = `dept-val ${escPriority}`;
            
            // Resolution steps list mapping
            let steps = [];
            if (c.solving_steps) {
                try {
                    steps = JSON.parse(c.solving_steps);
                } catch (e) {
                    steps = [c.solving_steps];
                }
            }
            
            if (steps.length > 0) {
                modalSolvingSteps.innerHTML = steps.map(step => `<li>${step}</li>`).join("");
            } else {
                modalSolvingSteps.innerHTML = "<li>No specific resolution steps generated.</li>";
            }
            
            detailModal.style.display = "flex";
            lucide.createIcons();
        } catch (error) {
            console.error(error);
            alert("Error rendering complaint details");
        }
    }

    closeModalBtn.addEventListener("click", () => {
        detailModal.style.display = "none";
    });

    // Close on outside click
    detailModal.addEventListener("click", (e) => {
        if (e.target === detailModal) {
            detailModal.style.display = "none";
        }
    });

    // ---------------------------------------------------------
    // 8. WebSocket Stream Integration
    // ---------------------------------------------------------
    function initWebSocket() {
        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
        
        state.webSocket = new WebSocket(wsUrl);
        
        state.webSocket.onopen = () => {
            console.log("WebSocket connected to real-time events pipeline.");
            document.getElementById("systemStatusText").textContent = "Real-time Monitoring Active (Secure WS Connected)";
        };
        
        state.webSocket.onclose = () => {
            console.warn("WebSocket disconnected. Retrying connection in 5 seconds...");
            document.getElementById("systemStatusText").textContent = "WS Disconnected - Reconnecting...";
            setTimeout(initWebSocket, 5000);
        };
        
        state.webSocket.onerror = (err) => {
            console.error("WebSocket connection encountered an error.", err);
        };
        
        state.webSocket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                
                if (message.event === "new_complaint") {
                    handleNewComplaintEvent(message.data);
                } else if (message.event === "topics_updated") {
                    handleTopicsUpdatedEvent(message.data);
                }
            } catch (error) {
                console.error("Error parsing WS event message data: ", error);
            }
        };
    }

    function handleNewComplaintEvent(complaint) {
        // 1. Show notification dot on Tab menu if not on Stream tab
        const activeTab = document.querySelector(".nav-item.active").getAttribute("data-tab");
        if (activeTab !== "feed") {
            feedPulseDot.style.display = "block";
        }

        // 2. Injects card into Tab 3 list
        const streamLogs = document.getElementById("liveStreamLogs");
        const emptyState = streamLogs.querySelector(".log-empty-state");
        if (emptyState) emptyState.remove();

        const card = document.createElement("div");
        const abstract = complaint.ai_summary || complaint.complaint_text.substring(0, 75) + "...";
        const timeStr = complaint.complaint_time || "Now";
        const dateStr = complaint.complaint_date || "";
        const severity = complaint.severity || "medium";

        card.className = `stream-card ${severity}`;
        card.setAttribute("data-id", complaint.complaint_id);
        card.innerHTML = `
            <div class="stream-card-meta">
                <span class="text-bold capitalize">${complaint.user_type} • ${complaint.complaint_source}</span>
                <span>${dateStr} ${timeStr}</span>
            </div>
            <div class="stream-card-content">
                <strong>[${complaint.topic_label}]</strong> ${abstract}
            </div>
            <div class="stream-card-meta" style="margin-top: 0.25rem;">
                <span>Intensity: ${complaint.intensity_score.toFixed(2)}</span>
                <span class="badge-sev ${severity}">${severity.toUpperCase()}</span>
            </div>
        `;
        
        // Prepended list insert
        streamLogs.insertBefore(card, streamLogs.firstChild);
        
        // Add click listener to open modal
        card.addEventListener("click", () => {
            openDetailModal(complaint.complaint_id);
        });

        // 3. Reload current ledger list and analytical metrics
        loadAnalytics();
        loadLedgerTable();
        fetchTopicsDropdown();
    }

    function handleTopicsUpdatedEvent(data) {
        console.log("Topic model retraining finished. Refreshing configurations.");
        // Re-enable button
        retrainBtn.disabled = false;
        const spinner = retrainBtn.querySelector("i");
        spinner.style.animation = "none";
        retrainBtn.querySelector("span").textContent = "Retrain AI Topics";

        // Refresh widgets
        fetchTopicsDropdown();
        loadAnalytics();
        loadLedgerTable();
        
        // If tab is drilldown, reload list
        const activeTab = document.querySelector(".nav-item.active").getAttribute("data-tab");
        if (activeTab === "drilldown") {
            loadDrilldownTopics();
        }
    }

    // ---------------------------------------------------------
    // 9. Tab 2: Topics Drilldown Logic
    // ---------------------------------------------------------
    async function loadDrilldownTopics() {
        drilldownTopicsList.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--color-text-muted);">Loading clusters...</div>`;
        try {
            const response = await fetch("/api/analytics/topics");
            if (!response.ok) throw new Error();
            const topics = await response.json();
            
            if (topics.length === 0) {
                drilldownTopicsList.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--color-text-muted);">No topic clusters calculated. Press 'Retrain AI Topics' to generate.</div>`;
                return;
            }
            
            let listHtml = "";
            topics.forEach(t => {
                const kws = t.keywords.slice(0, 3).join(", ");
                const selectedClass = state.selectedTopicId === t.topic_id ? "selected" : "";
                
                listHtml += `
                    <button class="topic-list-item ${selectedClass}" data-id="${t.topic_id}">
                        <div class="topic-list-info">
                            <span class="topic-list-title capitalize">${t.topic_label}</span>
                            <span class="topic-list-kws">Keywords: ${kws}</span>
                        </div>
                        <span class="topic-list-count">${t.complaint_count}</span>
                    </button>
                `;
            });
            drilldownTopicsList.innerHTML = listHtml;
            
            // Add click handlers
            document.querySelectorAll(".topic-list-item").forEach(item => {
                item.addEventListener("click", () => {
                    document.querySelectorAll(".topic-list-item").forEach(i => i.classList.remove("selected"));
                    item.classList.add("selected");
                    
                    const tId = parseInt(item.getAttribute("data-id"));
                    state.selectedTopicId = tId;
                    loadTopicDrilldownDetails(tId, topics.find(x => x.topic_id === tId));
                });
            });

            // Maintain selection or select first
            if (state.selectedTopicId !== null) {
                const activeItem = document.querySelector(`.topic-list-item[data-id="${state.selectedTopicId}"]`);
                if (activeItem) {
                    activeItem.click();
                } else {
                    document.querySelector(".topic-list-item")?.click();
                }
            } else {
                document.querySelector(".topic-list-item")?.click();
            }
        } catch (error) {
            console.error(error);
            drilldownTopicsList.innerHTML = `<div style="color:var(--color-danger);">Failed to load topics list.</div>`;
        }
    }

    async function loadTopicDrilldownDetails(topicId, topicData) {
        drilldownDetailsContainer.innerHTML = `<div style="text-align:center; padding:3rem; color:var(--color-text-muted);">Fetching cluster documents...</div>`;
        
        try {
            const response = await fetch(`/api/complaints?topic_id=${topicId}&limit=100`);
            if (!response.ok) throw new Error();
            const data = await response.json();
            
            let keywordBadges = topicData.keywords.map(kw => `<span class="keyword-badge">${kw}</span>`).join("");
            
            let complaintsHtml = "";
            data.items.forEach(c => {
                const abstract = c.ai_summary || c.complaint_text.substring(0, 100) + "...";
                complaintsHtml += `
                    <div class="topic-complaint-card" data-id="${c.complaint_id}">
                        <div class="topic-complaint-card-header">
                            <span class="capitalize font-bold">${c.user_type} • ${c.complaint_source} • ${c.location}</span>
                            <span>${c.complaint_date} ${c.complaint_time}</span>
                        </div>
                        <p style="font-size:0.9rem; line-height:1.4;">${abstract}</p>
                        <div class="stream-card-meta" style="margin-top:0.5rem; justify-content:flex-end;">
                            <span class="badge-sev ${c.severity}">${c.severity.toUpperCase()}</span>
                        </div>
                    </div>
                `;
            });
            
            drilldownDetailsContainer.innerHTML = `
                <div class="drilldown-results">
                    <h2>Topic Cluster: <span class="capitalize" style="color:var(--color-accent);">${topicData.topic_label}</span></h2>
                    
                    <h3 class="card-lbl" style="margin-top:1.25rem;">Extracted Core Vocabulary Keywords</h3>
                    <div class="keyword-badge-container">${keywordBadges}</div>
                    
                    <div class="horizontal-divider"></div>
                    
                    <h3>Matching Customer Support Ledger (${data.items.length} Tickets)</h3>
                    <div class="topic-complaints-list">${complaintsHtml}</div>
                </div>
            `;
            
            // Add click listeners to cards
            document.querySelectorAll(".topic-complaint-card").forEach(card => {
                card.addEventListener("click", () => {
                    openDetailModal(card.getAttribute("data-id"));
                });
            });
        } catch (error) {
            console.error(error);
            drilldownDetailsContainer.innerHTML = `<div style="color:var(--color-danger);">Failed to load cluster details.</div>`;
        }
    }

    // ---------------------------------------------------------
    // 10. Startup Inits
    // ---------------------------------------------------------
    // Bind table headers for sorting
    document.querySelectorAll("th.sortable").forEach(th => {
        th.addEventListener("click", () => {
            const sortBy = th.getAttribute("data-sort-by");
            if (state.sortBy === sortBy) {
                state.sortOrder = state.sortOrder === "asc" ? "desc" : "asc";
            } else {
                state.sortBy = sortBy;
                state.sortOrder = "asc";
            }
            
            // Sort in-memory
            sortComplaints(state.currentComplaints, state.sortBy, state.sortOrder);
            // Render table
            renderLedgerTable(state.currentComplaints);
            // Update icons
            updateSortIcons();
        });
    });

    fetchTopicsDropdown();
    loadAnalytics();
    loadLedgerTable();
    initWebSocket();
});
