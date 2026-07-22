document.addEventListener('DOMContentLoaded', () => {
    // --- THEME TOGGLE (Light/Dark Mode) ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const html = document.documentElement;

    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        html.classList.add('dark');
    } else {
        html.classList.remove('dark');
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            html.classList.toggle('dark');
            if (html.classList.contains('dark')) {
                localStorage.theme = 'dark';
            } else {
                localStorage.theme = 'light';
            }
            if (window.revenueChartInstance) {
                updateChartTheme();
            }
        });
    }

    // --- MOBILE SIDEBAR TOGGLE ---
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    function toggleSidebar() {
        sidebar.classList.toggle('-translate-x-full');
        sidebarOverlay.classList.toggle('hidden');
    }

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', toggleSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', toggleSidebar);
    }

    // --- DASHBOARD CHART (only runs if the chart canvas exists on this page) ---
    initChart();

    // --- Let any page-specific module run its own init, if it defined one ---
    if (typeof initPageModule === 'function') {
        initPageModule();
    }
});

// --- CHART HANDLING ---
// Guarded internally: does nothing on pages without a #revenueChart canvas
// (i.e. every page except the dashboard).

function initChart() {
    const ctx = document.getElementById('revenueChart');
    if (!ctx) return;

    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const data = [12000, 19000, 15000, 25000, 22000, 30000, 45230];

    const isDark = document.documentElement.classList.contains('dark');
    const gridColor = isDark ? '#334155' : '#f1f5f9';
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const brandColor = isDark ? '#e7c27a' : '#71041a';

    window.revenueChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue (₹)',
                data: data,
                borderColor: brandColor,
                backgroundColor: isDark ? 'rgba(231, 194, 122, 0.1)' : 'rgba(113, 4, 26, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: brandColor,
                pointBorderColor: isDark ? '#1e293b' : '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: isDark ? '#0f172a' : '#fff',
                    titleColor: isDark ? '#fff' : '#0f172a',
                    bodyColor: isDark ? '#cbd5e1' : '#475569',
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) { label += ': '; }
                            if (context.parsed.y !== null) { label += '₹' + context.parsed.y.toLocaleString(); }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: gridColor, drawBorder: false },
                    ticks: {
                        color: textColor,
                        callback: function (value) { return '₹' + (value / 1000) + 'k'; }
                    }
                },
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { color: textColor }
                }
            }
        }
    });
}

function updateChartTheme() {
    if (!window.revenueChartInstance) return;

    const isDark = document.documentElement.classList.contains('dark');
    const gridColor = isDark ? '#334155' : '#f1f5f9';
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const brandColor = isDark ? '#e7c27a' : '#71041a';

    const chart = window.revenueChartInstance;

    chart.data.datasets[0].borderColor = brandColor;
    chart.data.datasets[0].backgroundColor = isDark ? 'rgba(231, 194, 122, 0.1)' : 'rgba(113, 4, 26, 0.1)';
    chart.data.datasets[0].pointBackgroundColor = brandColor;
    chart.data.datasets[0].pointBorderColor = isDark ? '#1e293b' : '#fff';

    chart.options.scales.x.ticks.color = textColor;
    chart.options.scales.y.ticks.color = textColor;
    chart.options.scales.y.grid.color = gridColor;

    chart.options.plugins.tooltip.backgroundColor = isDark ? '#0f172a' : '#fff';
    chart.options.plugins.tooltip.titleColor = isDark ? '#fff' : '#0f172a';
    chart.options.plugins.tooltip.bodyColor = isDark ? '#cbd5e1' : '#475569';
    chart.options.plugins.tooltip.borderColor = isDark ? '#334155' : '#e2e8f0';

    chart.update();
}