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


function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

async function logoutUser(event) {
    event.preventDefault();

    const csrftoken = getCookie("csrftoken");

    const response = await fetch("/api/auth/logout/", {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken,
            "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin"
    });

    const data = await response.json();

    if (data.success) {
        window.location.href = data.redirect_url;
    }
}

// --- ADMIN SEARCH HANDLER (Desktop & Mobile with Live Suggestions) ---
document.addEventListener('DOMContentLoaded', () => {
    const searchToggle = document.getElementById('mobile-search-toggle');
    const searchOverlay = document.getElementById('mobile-search-overlay');
    const closeSearch = document.getElementById('close-mobile-search');
    const mobileInput = document.getElementById('mobile-admin-search-input');
    const desktopInput = document.getElementById('desktop-admin-search-input');
    const mobileSuggestions = document.getElementById('adminMobileSearchSuggestions');
    const desktopSuggestions = document.getElementById('adminDesktopSearchSuggestions');
    const mobileSubmitBtn = document.getElementById('mobile-search-submit-btn');
    const desktopSubmitBtn = document.getElementById('desktop-search-submit-btn');

    const SUGGEST_URL = '/search/suggest/';

    // Toggle Mobile Search Overlay
    if (searchToggle && searchOverlay) {
        searchToggle.addEventListener('click', () => {
            searchOverlay.classList.remove('hidden');
            if (mobileInput) {
                mobileInput.focus();
                showQuickNav(mobileSuggestions, '');
            }
        });
    }

    if (closeSearch && searchOverlay) {
        closeSearch.addEventListener('click', () => {
            searchOverlay.classList.add('hidden');
            if (mobileSuggestions) mobileSuggestions.classList.add('hidden');
        });
    }

    // Ctrl + K shortcut
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (window.innerWidth < 768) {
                if (searchOverlay) {
                    searchOverlay.classList.remove('hidden');
                    if (mobileInput) {
                        mobileInput.focus();
                        showQuickNav(mobileSuggestions, '');
                    }
                }
            } else {
                if (desktopInput) {
                    desktopInput.focus();
                    showQuickNav(desktopSuggestions, '');
                }
            }
        }
    });

    const adminPages = [
        { name: 'Products Catalog', url: '/adm/products/', icon: 'ph-package', desc: 'Manage inventory & prices' },
        { name: 'Categories & Signature Sarees', url: '/adm/categories/', icon: 'ph-crown', desc: '5 Signature Sarees showcase' },
        { name: 'Website Builder', url: '/adm/website-builder/', icon: 'ph-paint-brush', desc: 'Hero banners & memories' },
        { name: 'Filters & Colors', url: '/adm/filters/', icon: 'ph-faders', desc: 'Colors, fabrics, prints, tags' },
        { name: 'Customer Reviews', url: '/adm/reviews/', icon: 'ph-star', desc: 'Approve & moderate reviews' },
    ];

    function showQuickNav(container, query) {
        if (!container) return;
        const filteredPages = adminPages.filter(p => p.name.toLowerCase().includes(query.toLowerCase()));
        if (filteredPages.length === 0) return;

        let html = `
            <div class="p-2 border-b border-slate-100 dark:border-dark-border">
                <span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-3">Admin Sections</span>
            </div>
            <div class="p-1 space-y-0.5">
        `;

        filteredPages.forEach(page => {
            html += `
                <a href="${page.url}" class="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-700 dark:text-slate-200 hover:bg-brand-maroon/10 hover:text-brand-maroon dark:hover:text-brand-gold transition-colors text-xs font-medium">
                    <i class="ph ${page.icon} text-base text-brand-maroon dark:text-brand-gold"></i>
                    <div>
                        <div class="font-semibold">${page.name}</div>
                        <div class="text-[10px] text-slate-400">${page.desc}</div>
                    </div>
                </a>
            `;
        });

        html += `</div>`;
        container.innerHTML = html;
        container.classList.remove('hidden');
    }

    function renderAdminSuggestions(container, results, query) {
    if (!container) return;

    // Clear existing suggestions safely
    container.replaceChildren();

    // -----------------------------
    // Matching admin pages
    // -----------------------------
    const matchingPages = adminPages.filter(p =>
        p.name.toLowerCase().includes(query.toLowerCase())
    );

    if (matchingPages.length > 0) {
        const header = document.createElement('div');
        header.className =
            'p-2 border-b border-slate-100 dark:border-dark-border';

        const headerText = document.createElement('span');
        headerText.className =
            'text-[10px] font-bold text-slate-400 uppercase tracking-wider px-3';
        headerText.textContent = 'Quick Navigation';

        header.appendChild(headerText);
        container.appendChild(header);

        const pagesWrapper = document.createElement('div');
        pagesWrapper.className = 'p-1';

        matchingPages.slice(0, 3).forEach(page => {
            const link = document.createElement('a');

            link.href = page.url;
            link.className =
                'flex items-center gap-3 px-3 py-2 rounded-lg ' +
                'text-slate-700 dark:text-slate-200 ' +
                'hover:bg-slate-100 dark:hover:bg-slate-800 ' +
                'transition-colors text-xs font-medium';

            const icon = document.createElement('i');
            icon.className =
                `ph ${page.icon} text-base text-brand-maroon dark:text-brand-gold`;

            const name = document.createElement('span');
            name.textContent = page.name;

            link.append(icon, name);
            pagesWrapper.appendChild(link);
        });

        container.appendChild(pagesWrapper);
    }

    // -----------------------------
    // Matching products
    // -----------------------------
    if (results.length > 0) {
        const productHeader = document.createElement('div');
        productHeader.className =
            'p-2 border-t border-b border-slate-100 dark:border-dark-border';

        const productHeaderText = document.createElement('span');
        productHeaderText.className =
            'text-[10px] font-bold text-slate-400 uppercase tracking-wider px-3';
        productHeaderText.textContent =
            `Matching Products (${results.length})`;

        productHeader.appendChild(productHeaderText);
        container.appendChild(productHeader);

        const productsWrapper = document.createElement('div');
        productsWrapper.className =
            'p-1 divide-y divide-slate-100 dark:divide-dark-border';

        results.forEach(p => {
            const link = document.createElement('a');

            link.href =
                `/adm/products/?search=${encodeURIComponent(
                    String(p.name ?? '')
                )}`;

            link.className =
                'flex items-center gap-3 px-3 py-2.5 ' +
                'hover:bg-brand-maroon/5 dark:hover:bg-slate-800 ' +
                'transition-colors';

            // Product image
            if (p.thumbnail) {
                const img = document.createElement('img');

                img.src = String(p.thumbnail);
                img.alt = String(p.name ?? '');
                img.className =
                    'w-10 h-10 object-cover rounded-lg bg-slate-100 ' +
                    'shrink-0 border border-slate-200 dark:border-slate-700';
                img.loading = 'lazy';

                link.appendChild(img);
            } else {
                const placeholder = document.createElement('div');

                placeholder.className =
                    'w-10 h-10 rounded-lg bg-slate-100 ' +
                    'dark:bg-slate-800 shrink-0 flex items-center ' +
                    'justify-center text-slate-400';

                const icon = document.createElement('i');
                icon.className = 'ph ph-image';

                placeholder.appendChild(icon);
                link.appendChild(placeholder);
            }

            // Product information
            const info = document.createElement('div');
            info.className = 'min-w-0 flex-1';

            const name = document.createElement('div');
            name.className =
                'text-xs font-bold text-slate-800 dark:text-white truncate';
            name.textContent = String(p.name ?? '');

            const category = document.createElement('div');
            category.className = 'text-[10px] text-slate-400';
            category.textContent =
                String(p.category || 'Product');

            info.append(name, category);

            // Price
            const price = document.createElement('div');
            price.className =
                'text-xs font-bold text-brand-maroon dark:text-brand-gold ' +
                'whitespace-nowrap';

            const numericPrice = Number(p.price);

            price.textContent = `₹${
                Number.isFinite(numericPrice)
                    ? Math.round(numericPrice).toLocaleString('en-IN')
                    : '—'
            }`;

            link.append(info, price);
            productsWrapper.appendChild(link);
        });

        container.appendChild(productsWrapper);
    }

    // -----------------------------
    // Search all products
    // -----------------------------
    const searchAllLink = document.createElement('a');

    searchAllLink.href =
        `/adm/products/?search=${encodeURIComponent(query)}`;

    searchAllLink.className =
        'block text-center py-2.5 text-xs font-bold ' +
        'text-brand-maroon dark:text-brand-gold ' +
        'border-t border-slate-100 dark:border-dark-border ' +
        'hover:bg-slate-50 dark:hover:bg-slate-800 ' +
        'transition-colors';

    searchAllLink.textContent =
        `Search all products for "${query}" →`;

    container.appendChild(searchAllLink);

    // Show dropdown
    container.classList.remove('hidden');
}

    function setupAdminSearchInput(inputEl, suggestionsContainer) {
        if (!inputEl || !suggestionsContainer) return;

        let debounceTimer = null;
        let currentController = null;

        inputEl.addEventListener('focus', () => {
            const query = inputEl.value.trim();
            if (query.length < 2) {
                showQuickNav(suggestionsContainer, query);
            }
        });

        inputEl.addEventListener('input', () => {
            const query = inputEl.value.trim();
            clearTimeout(debounceTimer);

            if (query.length < 2) {
                showQuickNav(suggestionsContainer, query);
                return;
            }

            if (currentController) currentController.abort();

            debounceTimer = setTimeout(async () => {
                currentController = new AbortController();
                try {
                    const res = await fetch(`${SUGGEST_URL}?q=${encodeURIComponent(query)}`, {
                        signal: currentController.signal
                    });
                    const data = await res.json();
                    renderAdminSuggestions(suggestionsContainer, data.results || [], query);
                } catch (err) {
                    if (err.name !== 'AbortError') console.error(err);
                }
            }, 250);
        });

        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                suggestionsContainer.classList.add('hidden');
                if (searchOverlay) searchOverlay.classList.add('hidden');
            } else if (e.key === 'Enter') {
                const query = inputEl.value.trim();
                if (query) {
                    window.location.href = `/adm/products/?search=${encodeURIComponent(query)}`;
                }
            }
        });
    }

    setupAdminSearchInput(desktopInput, desktopSuggestions);
    setupAdminSearchInput(mobileInput, mobileSuggestions);

    if (desktopSubmitBtn && desktopInput) {
        desktopSubmitBtn.addEventListener('click', () => {
            const query = desktopInput.value.trim();
            if (query) {
                window.location.href = `/adm/products/?search=${encodeURIComponent(query)}`;
            } else {
                desktopInput.focus();
                showQuickNav(desktopSuggestions, '');
            }
        });
    }

    if (mobileSubmitBtn && mobileInput) {
        mobileSubmitBtn.addEventListener('click', () => {
            const query = mobileInput.value.trim();
            if (query) {
                window.location.href = `/adm/products/?search=${encodeURIComponent(query)}`;
            } else {
                mobileInput.focus();
                showQuickNav(mobileSuggestions, '');
            }
        });
    }

    // Close dropdowns on outside click
    document.addEventListener('click', (e) => {
        if (desktopInput && desktopSuggestions && !desktopInput.contains(e.target) && !desktopSuggestions.contains(e.target)) {
            desktopSuggestions.classList.add('hidden');
        }
        if (mobileInput && mobileSuggestions && !mobileInput.contains(e.target) && !mobileSuggestions.contains(e.target) && searchToggle && !searchToggle.contains(e.target)) {
            mobileSuggestions.classList.add('hidden');
        }
    });
});