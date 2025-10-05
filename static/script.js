// --- WIZARD AND STATE MANAGEMENT ---
const wizardSteps = document.querySelectorAll('.wizard-step');
let userChoices = {};

function showStep(stepNumber) {
    wizardSteps.forEach(step => step.classList.remove('active'));
    document.getElementById(`step-${stepNumber}-activity`)?.classList.add('active');
    document.getElementById(`step-${stepNumber}-date`)?.classList.add('active');
    document.getElementById(`step-${stepNumber}-location`)?.classList.add('active');
    if (stepNumber === 3 && !window.map) { initializeMap(); }
}

document.querySelectorAll('.activity-btn').forEach(btn => {
    btn.addEventListener('click', () => { userChoices.activity = btn.dataset.activity; showStep(2); });
});
document.getElementById('date-next-btn').addEventListener('click', () => {
    userChoices.month = document.getElementById('month-select').value;
    userChoices.day = document.getElementById('day-input').value;
    showStep(3);
});
document.getElementById('date-back-btn').addEventListener('click', () => showStep(1));
document.getElementById('location-back-btn').addEventListener('click', () => showStep(2));

// --- MAP AND DATA LOGIC ---
var map, trendChart;
function initializeMap() {
    window.map = L.map('map').setView([23.8103, 90.4125], 5);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
    }).addTo(map);
    const search = new GeoSearch.GeoSearchControl({ provider: new GeoSearch.OpenStreetMapProvider(), style: 'bar', showMarker: false, autoClose: true });
    map.addControl(search);
    map.on('click', (e) => fetchData(e.latlng.lat, e.latlng.lng));
    map.on('geosearch/showlocation', (e) => fetchData(e.location.y, e.location.x));
}

function fetchData(lat, lon) {
    userChoices.lat = lat; userChoices.lon = lon;
    const { activity, month, day } = userChoices;
    const dashboard = document.getElementById('dashboard');
    dashboard.innerHTML = `<h2><i class="fas fa-satellite-dish"></i> Analyzing 30 Years of NASA Data...</h2><div class="loader"></div>`;
    
    fetch(`/get_weather_stats?lat=${lat}&lon=${lon}&activity=${activity}&month=${month}&day=${day}`)
        .then(response => response.json())
        .then(data => {
            if (!data) { dashboard.innerHTML = '<h2><i class="fas fa-exclamation-triangle"></i> Telemetry Error</h2><p>Could not retrieve data for this location. Please try another spot.</p>'; return; }
            
            const suggestionHTML = data.suggestion ? `<div class="suggestion-card"><h3><i class="fas fa-lightbulb"></i> A Better Idea?</h3><p>${data.suggestion}</p></div>` : '';
            const comfortHTML = data.comfort_index ? `<div class="stat-card"><i class="fas fa-smile-beam comfort"></i><div class="stat-card-info"><h3>Comfort Index</h3><p>${data.comfort_index.score} (${data.comfort_index.label})</p></div></div>` : '';
            const trendChartHTML = data.trend_data ? `<div class="chart-card"><h3>Climate Trend: Chance of Hot Day</h3><canvas id="trend-chart"></canvas></div>` : '';
            
            const dashboardHTML = `
                <div class="recommendation-card">
                    <h3>Climate Report for ${activity.charAt(0).toUpperCase() + activity.slice(1)}</h3>
                    <p>${data.recommendation}</p>
                </div>
                ${suggestionHTML}
                ${comfortHTML}
                <div class="stat-card">
                    <i class="fas fa-temperature-high temp"></i>
                    <div class="stat-card-info"><h3>Chance of Hot Day (>30°C)</h3><p>${data.probabilities.temperature.toFixed(1)}%</p></div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-cloud-showers-heavy precip"></i>
                    <div class="stat-card-info"><h3>Chance of Rainy Day (>1mm)</h3><p>${data.probabilities.precipitation.toFixed(1)}%</p></div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-wind wind"></i>
                    <div class="stat-card-info"><h3>Chance of Windy Day (>25km/h)</h3><p>${data.probabilities.wind.toFixed(1)}%</p></div>
                </div>
                ${trendChartHTML}
                <a href="/download?lat=${lat}&lon=${lon}" class="download-btn"><i class="fas fa-download"></i> Download Full Dataset (CSV)</a>
            `;
            dashboard.innerHTML = dashboardHTML;
            if (data.trend_data) {
                renderTrendChart(data.trend_data);
            }
        })
        .catch(error => {
            console.error('Fetch Error:', error);
            dashboard.innerHTML = '<h2><i class="fas fa-exclamation-triangle"></i> Connection Lost</h2>';
        });
}

function renderTrendChart(trendData) {
    if (trendChart) { trendChart.destroy(); }
    const ctx = document.getElementById('trend-chart')?.getContext('2d');
    if (!ctx) return;
    const years = Object.keys(trendData).map(Number).sort((a,b) => a - b);
    const probs = years.map(year => trendData[year]);
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [{
                label: 'Probability of Hot Day (%)', data: probs,
                borderColor: 'rgba(230, 57, 149, 1)', backgroundColor: 'rgba(230, 57, 149, 0.2)',
                fill: true, tension: 0.4
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, max: 100, ticks: { color: '#c9d1d9', callback: (value) => value + '%' }, grid: { color: '#30363d' } },
                x: { ticks: { color: '#c9d1d9' }, grid: { color: '#30363d' } }
            }
        }
    });
}

showStep(1);