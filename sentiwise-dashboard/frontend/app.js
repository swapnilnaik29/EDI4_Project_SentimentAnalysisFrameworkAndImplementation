const API_BASE = "http://127.0.0.1:8000/api";

let allReviewsData = [];

// DOM Elements
const kpiTotal = document.getElementById('kpi-total');
const kpiRating = document.getElementById('kpi-rating');
const kpiPositive = document.getElementById('kpi-positive');
const kpiIssue = document.getElementById('kpi-issue');
const reviewsTableBody = document.getElementById('reviews-table-body');
const modal = document.getElementById('reviewModal');
const modalContent = document.getElementById('reviewModalContent');
const filterBu = document.getElementById('filter-bu');
const filterSentiment = document.getElementById('filter-sentiment');

// Init
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await Promise.all([
            fetchDashboardStats(),
            fetchReviews(),
            fetchSummary(false)
        ]);
        
        // Hide loading screen
        const loadingScreen = document.getElementById('loading-screen');
        loadingScreen.classList.add('opacity-0');
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 500);
    } catch (e) {
        console.error("Initialization failed", e);
        document.getElementById('loading-text').innerText = "Failed to load data. Ensure backend is running.";
    }
});

// Sidebar Toggle for Mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar.classList.contains('-translate-x-full')) {
        sidebar.classList.remove('-translate-x-full');
    } else {
        sidebar.classList.add('-translate-x-full');
    }
}

// Fetch Stats
async function fetchDashboardStats() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/stats`);
        const data = await res.json();
        
        // Update KPIs
        kpiTotal.innerText = data.total_reviews.toLocaleString();
        kpiRating.innerText = parseFloat(data.avg_rating).toFixed(1) + " / 5.0";
        
        let posCount = data.sentiment_distribution["Positive"] || 0;
        let pct = ((posCount / data.total_reviews) * 100).toFixed(1);
        kpiPositive.innerText = pct + "%";
        
        if (data.top_products.length > 0) {
            kpiIssue.innerText = data.top_products[0].product;
        }

        renderSentimentChart(data.sentiment_distribution);
        renderTrendChart(data.time_series);
        
    } catch (e) {
        console.error("Error fetching stats", e);
    }
}

// Fetch Reviews
async function fetchReviews() {
    const bu = filterBu.value;
    const sentiment = filterSentiment.value;
    
    let url = `${API_BASE}/reviews`;
    let params = [];
    if (bu) params.push(`bu=${encodeURIComponent(bu)}`);
    if (sentiment) params.push(`sentiment=${encodeURIComponent(sentiment)}`);
    if (params.length > 0) url += '?' + params.join('&');
    
    try {
        reviewsTableBody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-slate-500">Loading...</td></tr>`;
        const res = await fetch(url);
        const data = await res.json();
        allReviewsData = data.data;
        
        reviewsTableBody.innerHTML = '';
        if (allReviewsData.length === 0) {
            reviewsTableBody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-slate-500">No reviews found.</td></tr>`;
            return;
        }

        allReviewsData.forEach((review, index) => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-800/50 transition-colors cursor-pointer";
            tr.onclick = () => openModal(index);
            
            const sentColor = review.ai_sentiment === 'Positive' ? 'text-green-400' : (review.ai_sentiment === 'Negative' ? 'text-red-400' : 'text-yellow-400');
            const toxValue = parseFloat(review.ai_toxicity);
            const toxDisplay = isNaN(toxValue) ? "0.00" : toxValue.toFixed(2);
            const toxColor = toxValue > 0.5 ? 'text-red-500 font-bold' : 'text-slate-400';

            tr.innerHTML = `
                <td class="py-3 px-6 whitespace-nowrap">${review.date}</td>
                <td class="py-3 px-6"><span class="bg-primary/20 text-primary text-xs px-2 py-1 rounded">${review.business_unit}</span></td>
                <td class="py-3 px-6 max-w-xs truncate" title="${review.review_text}">${review.review_text}</td>
                <td class="py-3 px-6">
                    <div class="flex items-center">
                        <span class="text-yellow-400 mr-1">★</span> ${review.rating}
                    </div>
                </td>
                <td class="py-3 px-6 font-medium ${sentColor}">${review.ai_sentiment || review.sentiment_label || 'Pending'}</td>
                <td class="py-3 px-6 ${toxColor}">${toxDisplay}</td>
            `;
            reviewsTableBody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error fetching reviews", e);
    }
}

// Fetch AI Summary
async function fetchSummary(force = false) {
    const summaryContainer = document.getElementById('ai-summary');
    summaryContainer.innerHTML = `
        <div class="animate-pulse flex space-x-2 w-full">
            <div class="h-2 bg-slate-600 rounded w-full"></div>
            <div class="h-2 bg-slate-600 rounded w-5/6"></div>
        </div>
    `;
    
    try {
        const bu = filterBu.value;
        const res = await fetch(`${API_BASE}/insights/summary`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ bu: bu || null, force_refresh: force })
        });
        const data = await res.json();
        summaryContainer.innerHTML = `<p>${data.summary}</p>`;
    } catch (e) {
        summaryContainer.innerHTML = `<p class="text-red-400">Failed to generate AI summary. Ensure Ollama is running.</p>`;
    }
}

// Process Batch
async function processBatch() {
    const btn = document.getElementById('processBtn');
    btn.innerText = "Processing...";
    btn.disabled = true;
    try {
        await fetch(`${API_BASE}/process_batch`, { method: 'POST' });
        alert("Batch processing started. Check terminal for model loading progress.");
        setTimeout(() => {
            fetchDashboardStats();
            fetchReviews();
            btn.innerText = "Run NLP Pipeline";
            btn.disabled = false;
        }, 5000);
    } catch (e) {
        alert("Error starting batch process.");
        btn.innerText = "Run NLP Pipeline";
        btn.disabled = false;
    }
}

// Charts
function renderSentimentChart(dist) {
    const chartDom = document.getElementById('chart-sentiment');
    const myChart = echarts.init(chartDom, 'dark', { renderer: 'svg' });
    
    const data = Object.keys(dist).map(key => ({
        name: key,
        value: dist[key]
    }));

    const option = {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item' },
        legend: { top: 'bottom', textStyle: { color: '#cbd5e1' } },
        series: [
            {
                name: 'Sentiment',
                type: 'pie',
                radius: ['40%', '70%'],
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#1e293b',
                    borderWidth: 2
                },
                label: { show: false },
                data: data,
                color: ['#4ade80', '#f87171', '#fbbf24', '#818cf8', '#f472b6']
            }
        ]
    };
    myChart.setOption(option);
    window.addEventListener('resize', () => myChart.resize());
}

function renderTrendChart(timeSeries) {
    const months = timeSeries.map(ts => ts.month);
    const counts = timeSeries.map(ts => ts.count);

    const trace = {
        x: months,
        y: counts,
        type: 'scatter',
        mode: 'lines+markers',
        line: { shape: 'spline', color: '#6366f1', width: 3 },
        marker: { size: 8, color: '#8b5cf6' },
        fill: 'tozeroy',
        fillcolor: 'rgba(99, 102, 241, 0.1)'
    };

    const layout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#94a3b8' },
        margin: { t: 10, r: 10, l: 40, b: 40 },
        xaxis: { showgrid: false, zeroline: false },
        yaxis: { gridcolor: '#334155', zeroline: false }
    };

    Plotly.newPlot('chart-trend', [trace], layout, { displayModeBar: false, responsive: true });
}

// Modal
function openModal(index) {
    const review = allReviewsData[index];
    if(!review) return;

    document.getElementById('modal-text').innerText = `"${review.review_text}"`;
    document.getElementById('modal-customer').innerText = `${review.reviewer_name} (${review.reviewer_type})`;
    document.getElementById('modal-product').innerText = `${review.product_or_service} [${review.business_unit}]`;
    
    document.getElementById('modal-sentiment').innerText = review.ai_sentiment || review.sentiment_label || 'Pending';
    document.getElementById('modal-sentiment').className = `font-bold ${getSentimentColor(review.ai_sentiment || review.sentiment_label)}`;
    
    document.getElementById('modal-emotion').innerText = review.ai_emotion || 'Pending';
    document.getElementById('modal-intent').innerText = review.ai_intent || 'Pending';
    const toxValue = parseFloat(review.ai_toxicity);
    const toxDisplay = isNaN(toxValue) ? "0.00" : toxValue.toFixed(2);
    document.getElementById('modal-toxicity').innerText = toxDisplay;
    document.getElementById('modal-toxicity').className = `font-bold ${toxValue > 0.5 ? 'text-red-500' : 'text-slate-300'}`;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => {
        modalContent.classList.remove('scale-95');
        modalContent.classList.add('scale-100');
    }, 10);
}

function closeModal() {
    modalContent.classList.remove('scale-100');
    modalContent.classList.add('scale-95');
    setTimeout(() => {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
    }, 300);
}

function getSentimentColor(sent) {
    if(sent === 'Positive') return 'text-green-400';
    if(sent === 'Negative' || sent === 'Toxic') return 'text-red-400';
    return 'text-yellow-400';
}
