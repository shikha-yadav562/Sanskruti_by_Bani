// --- LOCAL DATA STORE (MOCK DATABASE) ---
let productsDB = [];
let categoriesDB = []; // Old complex categories (can be removed later if not used)
let offersDB = [];
let blogDB = [];

// New Simple Collections
let simpleCategoriesDB = [];
let colorsDB = [];
let fabricsDB = [];
let printsDB = [];

function initDatabase() {
    const savedProducts = localStorage.getItem('sbb_products');
    productsDB = savedProducts ? JSON.parse(savedProducts) : [
        { id: 1, name: 'Royal Maroon Paithani', code: 'SBB-PT-001', category: 'Paithani', price: 24500, stock: 14, description: 'Pure silk authentic handwoven paithani', image_path: '../assets/slide11.png' },
        { id: 2, name: 'Emerald Banarasi', code: 'SBB-BN-042', category: 'Banarasi', price: 18900, stock: 2, description: 'Zari work premium banarasi saree', image_path: '' }
    ];

    const savedOffers = localStorage.getItem('sbb_offers');
    offersDB = savedOffers ? JSON.parse(savedOffers) : [
        { id: 1, code: 'DIWALI20', desc: '20% Off on entire store', expiry: '2026-10-31' }
    ];

    const savedBlog = localStorage.getItem('sbb_blog');
    blogDB = savedBlog ? JSON.parse(savedBlog) : [];

    const savedSC = localStorage.getItem('sbb_simple_categories');
    simpleCategoriesDB = savedSC ? JSON.parse(savedSC) : [];

    const savedColors = localStorage.getItem('sbb_colors');
    colorsDB = savedColors ? JSON.parse(savedColors) : [];

    const savedFabrics = localStorage.getItem('sbb_fabrics');
    fabricsDB = savedFabrics ? JSON.parse(savedFabrics) : [];

    const savedPrints = localStorage.getItem('sbb_prints');
    printsDB = savedPrints ? JSON.parse(savedPrints) : [];

    saveDatabase();
}

function saveDatabase() {
    localStorage.setItem('sbb_products', JSON.stringify(productsDB));
    localStorage.setItem('sbb_offers', JSON.stringify(offersDB));
    localStorage.setItem('sbb_blog', JSON.stringify(blogDB));
    localStorage.setItem('sbb_simple_categories', JSON.stringify(simpleCategoriesDB));
    localStorage.setItem('sbb_colors', JSON.stringify(colorsDB));
    localStorage.setItem('sbb_fabrics', JSON.stringify(fabricsDB));
    localStorage.setItem('sbb_prints', JSON.stringify(printsDB));
}

// --- INITIALIZATION ---

document.addEventListener('DOMContentLoaded', () => {
    initDatabase();
    
    // --- THEME TOGGLE (Light/Dark Mode) ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const html = document.documentElement;

    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        html.classList.add('dark');
    } else {
        html.classList.remove('dark');
    }

    themeToggleBtn.addEventListener('click', () => {
        html.classList.toggle('dark');
        if (html.classList.contains('dark')) {
            localStorage.theme = 'dark';
        } else {
            localStorage.theme = 'light';
        }
        if(window.revenueChartInstance) {
            updateChartTheme();
        }
    });

    // --- MOBILE SIDEBAR TOGGLE ---
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    function toggleSidebar() {
        sidebar.classList.toggle('-translate-x-full');
        sidebarOverlay.classList.toggle('hidden');
    }

    mobileMenuBtn.addEventListener('click', toggleSidebar);
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', toggleSidebar);
    }

    // --- SPA VIEW SWITCHING ---
    const navItems = document.querySelectorAll('.nav-item');
    const viewSections = document.querySelectorAll('.view-section');
    const pageTitle = document.getElementById('page-title');

    window.switchView = function(targetId) {
        const targetNav = Array.from(navItems).find(nav => nav.dataset.target === targetId);
        
        viewSections.forEach(section => {
            section.classList.add('hidden');
            section.classList.remove('flex'); 
        });

        navItems.forEach(nav => {
            nav.classList.remove('active', 'bg-brand-maroon/5', 'dark:bg-brand-maroon/20', 'text-brand-maroon', 'dark:text-brand-gold');
            nav.classList.add('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-50', 'dark:hover:bg-slate-800/50', 'hover:text-brand-maroon', 'dark:hover:text-brand-gold');
        });

        const targetView = document.getElementById(`view-${targetId}`);
        if (targetView) {
            if (targetView.id === 'view-coming-soon') {
                targetView.classList.remove('hidden');
                targetView.classList.add('flex');
            } else {
                targetView.classList.remove('hidden');
            }
        } else {
            const comingSoon = document.getElementById('view-coming-soon');
            comingSoon.classList.remove('hidden');
            comingSoon.classList.add('flex');
        }

        if (targetNav) {
            targetNav.classList.add('active', 'bg-brand-maroon/5', 'dark:bg-brand-maroon/20', 'text-brand-maroon', 'dark:text-brand-gold');
            targetNav.classList.remove('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-50', 'dark:hover:bg-slate-800/50', 'hover:text-brand-maroon', 'dark:hover:text-brand-gold');
            const titleSpan = targetNav.querySelector('span').innerText.split('\n')[0];
            pageTitle.innerText = titleSpan;
        }

        if (window.innerWidth < 768 && !sidebar.classList.contains('-translate-x-full')) {
            toggleSidebar();
        }
    };

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.dataset.target;
            if(targetId) {
                switchView(targetId);
                loadAllData();
            }
        });
    });

    initChart();
    loadAllData();
});

// --- DATA FUNCTIONS ---

function loadAllData() {
    renderProductsTable(productsDB);
    renderOffers(offersDB);
    renderBlog(blogDB);
    
    // New collections
    renderSC();
    renderColors();
    renderFabrics();
    renderPrints();
}

function renderProductsTable(products) {
    const tableBody = document.querySelector('#view-products tbody');
    if (!tableBody) return;
    tableBody.innerHTML = '';
    
    if (products.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="p-8 text-center text-slate-500">No products found. Click "Add Product" to create one.</td></tr>';
        return;
    }
    
    products.forEach(product => {
        const price = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(product.price);
        
        let stockBadge = '';
        if (product.stock > 10) {
            stockBadge = `<span class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> ${product.stock} in stock</span>`;
        } else if (product.stock > 0) {
            stockBadge = `<span class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-800"><span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span> ${product.stock} low stock</span>`;
        } else {
            stockBadge = `<span class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400 border border-red-200 dark:border-red-800"><span class="w-1.5 h-1.5 rounded-full bg-red-500"></span> Out of stock</span>`;
        }
        
        const imgHtml = product.image_path 
            ? `<img src="${product.image_path}" class="w-full h-full object-cover" alt="${product.name}" onerror="this.src='https://placehold.co/100x150?text=No+Image'">`
            : `<i class="ph ph-image text-2xl text-slate-400"></i>`;
            
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors group';
        tr.innerHTML = `
            <td class="p-4"><input type="checkbox" class="rounded border-slate-300 text-brand-maroon focus:ring-brand-maroon"></td>
            <td class="p-4">
                <div class="flex items-center gap-3">
                    <div class="w-12 h-16 rounded bg-slate-100 dark:bg-slate-800 overflow-hidden flex items-center justify-center">${imgHtml}</div>
                    <div>
                        <p class="text-sm font-semibold text-slate-800 dark:text-white group-hover:text-brand-maroon transition-colors cursor-pointer">${product.name}</p>
                        <p class="text-xs text-slate-500 w-48 truncate">${product.description || 'No description'}</p>
                    </div>
                </div>
            </td>
            <td class="p-4 text-sm text-slate-600 dark:text-slate-300 font-mono text-xs">${product.code}</td>
            <td class="p-4 text-sm text-slate-600 dark:text-slate-300"><span class="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-xs uppercase tracking-wider">${product.category}</span></td>
            <td class="p-4 text-sm font-medium text-slate-800 dark:text-white">${price}</td>
            <td class="p-4">${stockBadge}</td>
            <td class="p-4 text-right">
                <button onclick="deleteProduct(${product.id})" class="text-slate-400 hover:text-red-500 p-1"><i class="ph ph-trash text-lg"></i></button>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}


function renderOffers(offers) {
    const container = document.getElementById('offers-container');
    if (!container) return;
    container.innerHTML = '';
    
    offers.forEach(offer => {
        const div = document.createElement('div');
        div.className = 'bg-gradient-to-br from-brand-maroon to-brand-maroonLight p-6 rounded-2xl text-white shadow-lg relative overflow-hidden group';
        div.innerHTML = `
            <i class="ph ph-ticket absolute -right-6 -bottom-6 text-9xl opacity-10 group-hover:scale-110 transition-transform duration-500"></i>
            <div class="relative z-10">
                <div class="flex justify-between items-start mb-4">
                    <span class="bg-white/20 px-3 py-1 rounded-full text-xs font-semibold tracking-wider uppercase inline-block">Active</span>
                    <button onclick="deleteOffer(${offer.id})" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                        <i class="ph ph-trash"></i>
                    </button>
                </div>
                <h3 class="text-3xl font-bold mb-1">${offer.code}</h3>
                <p class="text-brand-gold font-medium mb-4">${offer.desc}</p>
                <p class="text-sm text-white/80"><i class="ph ph-clock mr-1"></i> Valid until ${offer.expiry}</p>
            </div>
        `;
        container.appendChild(div);
    });
}

function renderBlog(posts) {
    const container = document.getElementById('blog-container');
    if (!container) return;
    container.innerHTML = '';
    
    if (posts.length === 0) {
        container.parentElement.innerHTML += `
            <div id="empty-blog" class="bg-white dark:bg-dark-panel p-16 rounded-2xl border border-slate-100 dark:border-dark-border shadow-sm text-center">
                <div class="w-20 h-20 rounded-full bg-brand-maroon/5 flex items-center justify-center text-brand-maroon mx-auto mb-4">
                    <i class="ph ph-article text-3xl"></i>
                </div>
                <h3 class="text-xl font-bold text-slate-800 dark:text-white mb-2">No Blog Posts Yet</h3>
                <p class="text-slate-500 max-w-md mx-auto mb-6">Start writing about fashion trends, saree care tips, or your brand story to drive organic traffic.</p>
                <button onclick="openAddBlogModal()" class="px-6 py-2.5 bg-brand-maroon text-white rounded-xl font-medium shadow-md hover:bg-brand-maroonLight transition-colors">Create First Post</button>
            </div>
        `;
        return;
    }
    
    const emptyState = document.getElementById('empty-blog');
    if (emptyState) emptyState.remove();

    posts.forEach(post => {
        const div = document.createElement('div');
        div.className = 'bg-white dark:bg-dark-panel p-6 rounded-2xl border border-slate-100 dark:border-dark-border shadow-sm group hover:border-brand-maroon/30 transition-all flex flex-col h-full';
        div.innerHTML = `
            <div class="flex-1">
                <div class="text-xs text-brand-maroon font-semibold uppercase tracking-wider mb-2">${post.date}</div>
                <h3 class="text-xl font-bold text-slate-800 dark:text-white mb-3 line-clamp-2">${post.title}</h3>
                <p class="text-slate-500 dark:text-slate-400 text-sm line-clamp-3 mb-4">${post.content}</p>
            </div>
            <div class="flex justify-between items-center border-t border-slate-100 dark:border-dark-border pt-4 mt-auto">
                <button class="text-brand-maroon font-medium text-sm hover:underline">Edit Post</button>
                <button onclick="deleteBlog(${post.id})" class="text-slate-400 hover:text-red-500 p-1"><i class="ph ph-trash text-lg"></i></button>
            </div>
        `;
        container.appendChild(div);
    });
}

// --- MODAL & FORM HANDLING ---

// Product
window.openAddProductModal = function() {
    document.getElementById('addProductModal').classList.remove('hidden');
    document.getElementById('addProductModal').classList.add('flex');
};
window.closeAddProductModal = function() {
    document.getElementById('addProductModal').classList.add('hidden');
    document.getElementById('addProductModal').classList.remove('flex');
    document.getElementById('addProductForm').reset();
};
window.submitNewProduct = function() {
    const form = document.getElementById('addProductForm');
    if (!form.checkValidity()) { form.reportValidity(); return; }
    
    const newProduct = {
        id: Date.now(),
        name: document.getElementById('prodName').value,
        code: document.getElementById('prodCode').value,
        category: document.getElementById('prodCategory').value,
        price: parseFloat(document.getElementById('prodPrice').value),
        stock: parseInt(document.getElementById('prodStock').value),
        description: document.getElementById('prodDesc').value,
        image_path: ''
    };
    
    productsDB.unshift(newProduct);
    saveDatabase();
    closeAddProductModal();
    loadAllData();
    alert("Product saved successfully!");
};
window.deleteProduct = function(id) {
    if(confirm("Delete this product?")) {
        productsDB = productsDB.filter(p => p.id !== id);
        saveDatabase();
        loadAllData();
    }
};


// Offer
window.openAddOfferModal = function() {
    document.getElementById('addOfferModal').classList.remove('hidden');
    document.getElementById('addOfferModal').classList.add('flex');
};
window.closeAddOfferModal = function() {
    document.getElementById('addOfferModal').classList.add('hidden');
    document.getElementById('addOfferModal').classList.remove('flex');
    document.getElementById('addOfferForm').reset();
};
window.submitNewOffer = function() {
    const form = document.getElementById('addOfferForm');
    if (!form.checkValidity()) { form.reportValidity(); return; }
    
    const newOffer = {
        id: Date.now(),
        code: document.getElementById('offerCode').value.toUpperCase(),
        desc: document.getElementById('offerDesc').value,
        expiry: document.getElementById('offerExpiry').value
    };
    
    offersDB.push(newOffer);
    saveDatabase();
    closeAddOfferModal();
    loadAllData();
};
window.deleteOffer = function(id) {
    if(confirm("Delete this offer?")) {
        offersDB = offersDB.filter(o => o.id !== id);
        saveDatabase();
        loadAllData();
    }
};

// Blog
window.openAddBlogModal = function() {
    document.getElementById('addBlogModal').classList.remove('hidden');
    document.getElementById('addBlogModal').classList.add('flex');
};
window.closeAddBlogModal = function() {
    document.getElementById('addBlogModal').classList.add('hidden');
    document.getElementById('addBlogModal').classList.remove('flex');
    document.getElementById('addBlogForm').reset();
};
window.submitNewBlog = function() {
    const form = document.getElementById('addBlogForm');
    if (!form.checkValidity()) { form.reportValidity(); return; }
    
    const date = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    
    const newBlog = {
        id: Date.now(),
        title: document.getElementById('blogTitle').value,
        content: document.getElementById('blogContent').value,
        date: date
    };
    
    blogDB.unshift(newBlog);
    saveDatabase();
    closeAddBlogModal();
    loadAllData();
};
window.deleteBlog = function(id) {
    if(confirm("Delete this post?")) {
        blogDB = blogDB.filter(b => b.id !== id);
        saveDatabase();
        loadAllData();
    }
};

// --- CHART HANDLING ---

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
                        label: function(context) {
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
                        callback: function(value) { return '₹' + (value / 1000) + 'k'; }
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

// ==========================================
// SIMPLE CATEGORIES LOGIC
// ==========================================
function renderSC() {
    const tbody = document.getElementById("scTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (simpleCategoriesDB.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="p-8 text-center text-slate-500 italic">No categories found. Add your first above!</td></tr>`;
        return;
    }

    simpleCategoriesDB.forEach((category, index) => {
        const row = document.createElement("tr");
        row.className = "hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors group border-b border-slate-100 dark:border-dark-border last:border-0";
        row.innerHTML = `
            <td class="p-4 font-bold text-slate-800 dark:text-white">${index + 1}</td>
            <td class="p-4 text-slate-700 dark:text-slate-300">${category}</td>
            <td class="p-4">
                <div class="flex justify-center gap-3">
                    <button onclick="editSC(${index})" class="px-3 py-1.5 rounded-lg bg-amber-50 text-amber-600 hover:bg-amber-100 dark:bg-amber-500/10 dark:hover:bg-amber-500/20 font-medium text-xs transition-colors">Edit</button>
                    <button onclick="deleteSC(${index})" class="px-3 py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-500/10 dark:hover:bg-red-500/20 font-medium text-xs transition-colors">Delete</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

window.handleSCSubmit = function(e) {
    e.preventDefault();
    const inputField = document.getElementById("scName");
    const editIdx = parseInt(document.getElementById("scEditIndex").value);
    const value = inputField.value.trim();

    if (!value) return;

    if (editIdx === -1) {
        if (simpleCategoriesDB.map(c => c.toLowerCase()).includes(value.toLowerCase())) {
            alert("This category already exists!");
            return;
        }
        simpleCategoriesDB.push(value);
    } else {
        if (simpleCategoriesDB.map((c, i) => i !== editIdx ? c.toLowerCase() : null).includes(value.toLowerCase())) {
            alert("Another category shares this name!");
            return;
        }
        simpleCategoriesDB[editIdx] = value;
    }

    saveDatabase();
    resetSCForm();
    renderSC();
};

window.editSC = function(index) {
    document.getElementById("scName").value = simpleCategoriesDB[index];
    document.getElementById("scEditIndex").value = index;
    document.getElementById("scFormTitle").textContent = "Modify Category Entry";
    document.getElementById("scSubmitBtn").innerHTML = "Update Category";
    document.getElementById("scCancelBtn").classList.remove("hidden");
    document.getElementById("scName").focus();
};

window.deleteSC = function(index) {
    if (confirm(`Are you sure you want to delete "${simpleCategoriesDB[index]}"?`)) {
        simpleCategoriesDB.splice(index, 1);
        saveDatabase();
        resetSCForm();
        renderSC();
    }
};

window.resetSCForm = function() {
    document.getElementById("scName").value = "";
    document.getElementById("scEditIndex").value = "-1";
    document.getElementById("scFormTitle").textContent = "Create New Category";
    document.getElementById("scSubmitBtn").innerHTML = '<i class="ph ph-plus"></i> Add Category';
    document.getElementById("scCancelBtn").classList.add("hidden");
};


// ==========================================
// FILTERS: COLORS LOGIC
// ==========================================
window.updateColorPreview = function() {
    const hex = document.getElementById("colorPicker").value;
    document.getElementById("colorPreview").style.backgroundColor = hex;
};

function renderColors() {
    const tbody = document.getElementById("colorTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";
    if (colorsDB.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="p-8 text-center text-slate-500 italic">No colors added yet. Add your first above!</td></tr>`;
        return;
    }
    colorsDB.forEach((c, i) => {
        const row = document.createElement("tr");
        row.className = "hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors group border-b border-slate-100 dark:border-dark-border last:border-0";
        row.innerHTML = `
            <td class="p-4 font-bold text-slate-800 dark:text-white">${i + 1}</td>
            <td class="p-4"><div class="w-8 h-8 rounded-full border border-slate-200 shadow-sm" style="background-color:${c.hex};"></div></td>
            <td class="p-4 text-slate-700 dark:text-slate-300">${c.name}</td>
            <td class="p-4">
                <div class="flex justify-center gap-3">
                    <button onclick="editColor(${i})" class="px-3 py-1.5 rounded-lg bg-amber-50 text-amber-600 hover:bg-amber-100 dark:bg-amber-500/10 dark:hover:bg-amber-500/20 font-medium text-xs transition-colors">Edit</button>
                    <button onclick="deleteColor(${i})" class="px-3 py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-500/10 dark:hover:bg-red-500/20 font-medium text-xs transition-colors">Delete</button>
                </div>
            </td>`;
        tbody.appendChild(row);
    });
}

window.handleColorSubmit = function(e) {
    e.preventDefault();
    const name = document.getElementById("colorName").value.trim();
    const hex = document.getElementById("colorPicker").value;
    const idx = parseInt(document.getElementById("colorEditIndex").value);
    
    if (!name) return;

    if (idx === -1) {
        if (colorsDB.some(c => c.name.toLowerCase() === name.toLowerCase())) {
            alert("This color already exists!"); return;
        }
        colorsDB.push({ name, hex });
    } else {
        if (colorsDB.some((c, i) => i !== idx && c.name.toLowerCase() === name.toLowerCase())) {
            alert("Another color shares this name!"); return;
        }
        colorsDB[idx] = { name, hex };
    }
    saveDatabase();
    resetColorForm();
    renderColors();
};

window.editColor = function(i) {
    document.getElementById("colorName").value = colorsDB[i].name;
    document.getElementById("colorPicker").value = colorsDB[i].hex;
    updateColorPreview();
    document.getElementById("colorEditIndex").value = i;
    document.getElementById("colorFormTitle").textContent = "Modify Color Entry";
    document.getElementById("colorSubmitBtn").innerHTML = "Update Color";
    document.getElementById("colorCancelBtn").classList.remove("hidden");
    document.getElementById("colorName").focus();
};

window.deleteColor = function(i) {
    if (confirm(`Delete "${colorsDB[i].name}"?`)) {
        colorsDB.splice(i, 1);
        saveDatabase();
        resetColorForm();
        renderColors();
    }
};

window.resetColorForm = function() {
    document.getElementById("colorName").value = "";
    document.getElementById("colorPicker").value = "#c0392b";
    updateColorPreview();
    document.getElementById("colorEditIndex").value = "-1";
    document.getElementById("colorFormTitle").textContent = "Add New Color";
    document.getElementById("colorSubmitBtn").innerHTML = '<i class="ph ph-plus"></i> Add Color';
    document.getElementById("colorCancelBtn").classList.add("hidden");
};


// ==========================================
// FILTERS: FABRICS LOGIC
// ==========================================
function renderFabrics() {
    const tbody = document.getElementById("fabricTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";
    if (fabricsDB.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="p-8 text-center text-slate-500 italic">No fabrics added yet. Add your first above!</td></tr>`;
        return;
    }
    fabricsDB.forEach((f, i) => {
        const row = document.createElement("tr");
        row.className = "hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors group border-b border-slate-100 dark:border-dark-border last:border-0";
        row.innerHTML = `
            <td class="p-4 font-bold text-slate-800 dark:text-white">${i + 1}</td>
            <td class="p-4 text-slate-700 dark:text-slate-300">${f}</td>
            <td class="p-4">
                <div class="flex justify-center gap-3">
                    <button onclick="editFabric(${i})" class="px-3 py-1.5 rounded-lg bg-amber-50 text-amber-600 hover:bg-amber-100 dark:bg-amber-500/10 dark:hover:bg-amber-500/20 font-medium text-xs transition-colors">Edit</button>
                    <button onclick="deleteFabric(${i})" class="px-3 py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-500/10 dark:hover:bg-red-500/20 font-medium text-xs transition-colors">Delete</button>
                </div>
            </td>`;
        tbody.appendChild(row);
    });
}

window.handleFabricSubmit = function(e) {
    e.preventDefault();
    const name = document.getElementById("fabricName").value.trim();
    const idx = parseInt(document.getElementById("fabricEditIndex").value);
    
    if (!name) return;

    if (idx === -1) {
        if (fabricsDB.some(f => f.toLowerCase() === name.toLowerCase())) {
            alert("This fabric already exists!"); return;
        }
        fabricsDB.push(name);
    } else {
        if (fabricsDB.some((f, i) => i !== idx && f.toLowerCase() === name.toLowerCase())) {
            alert("Another fabric shares this name!"); return;
        }
        fabricsDB[idx] = name;
    }
    saveDatabase();
    resetFabricForm();
    renderFabrics();
};

window.editFabric = function(i) {
    document.getElementById("fabricName").value = fabricsDB[i];
    document.getElementById("fabricEditIndex").value = i;
    document.getElementById("fabricFormTitle").textContent = "Modify Fabric Entry";
    document.getElementById("fabricSubmitBtn").innerHTML = "Update Fabric";
    document.getElementById("fabricCancelBtn").classList.remove("hidden");
    document.getElementById("fabricName").focus();
};

window.deleteFabric = function(i) {
    if (confirm(`Delete "${fabricsDB[i]}"?`)) {
        fabricsDB.splice(i, 1);
        saveDatabase();
        resetFabricForm();
        renderFabrics();
    }
};

window.resetFabricForm = function() {
    document.getElementById("fabricName").value = "";
    document.getElementById("fabricEditIndex").value = "-1";
    document.getElementById("fabricFormTitle").textContent = "Add New Fabric";
    document.getElementById("fabricSubmitBtn").innerHTML = '<i class="ph ph-plus"></i> Add Fabric';
    document.getElementById("fabricCancelBtn").classList.add("hidden");
};


// ==========================================
// FILTERS: PRINTS LOGIC
// ==========================================
function renderPrints() {
    const tbody = document.getElementById("printTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";
    if (printsDB.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="p-8 text-center text-slate-500 italic">No prints added yet. Add your first above!</td></tr>`;
        return;
    }
    printsDB.forEach((p, i) => {
        const row = document.createElement("tr");
        row.className = "hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors group border-b border-slate-100 dark:border-dark-border last:border-0";
        row.innerHTML = `
            <td class="p-4 font-bold text-slate-800 dark:text-white">${i + 1}</td>
            <td class="p-4 text-slate-700 dark:text-slate-300">${p}</td>
            <td class="p-4">
                <div class="flex justify-center gap-3">
                    <button onclick="editPrint(${i})" class="px-3 py-1.5 rounded-lg bg-amber-50 text-amber-600 hover:bg-amber-100 dark:bg-amber-500/10 dark:hover:bg-amber-500/20 font-medium text-xs transition-colors">Edit</button>
                    <button onclick="deletePrint(${i})" class="px-3 py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-500/10 dark:hover:bg-red-500/20 font-medium text-xs transition-colors">Delete</button>
                </div>
            </td>`;
        tbody.appendChild(row);
    });
}

window.handlePrintSubmit = function(e) {
    e.preventDefault();
    const name = document.getElementById("printName").value.trim();
    const idx = parseInt(document.getElementById("printEditIndex").value);
    
    if (!name) return;

    if (idx === -1) {
        if (printsDB.some(p => p.toLowerCase() === name.toLowerCase())) {
            alert("This print already exists!"); return;
        }
        printsDB.push(name);
    } else {
        if (printsDB.some((p, i) => i !== idx && p.toLowerCase() === name.toLowerCase())) {
            alert("Another print shares this name!"); return;
        }
        printsDB[idx] = name;
    }
    saveDatabase();
    resetPrintForm();
    renderPrints();
};

window.editPrint = function(i) {
    document.getElementById("printName").value = printsDB[i];
    document.getElementById("printEditIndex").value = i;
    document.getElementById("printFormTitle").textContent = "Modify Print Entry";
    document.getElementById("printSubmitBtn").innerHTML = "Update Print";
    document.getElementById("printCancelBtn").classList.remove("hidden");
    document.getElementById("printName").focus();
};

window.deletePrint = function(i) {
    if (confirm(`Delete "${printsDB[i]}"?`)) {
        printsDB.splice(i, 1);
        saveDatabase();
        resetPrintForm();
        renderPrints();
    }
};

window.resetPrintForm = function() {
    document.getElementById("printName").value = "";
    document.getElementById("printEditIndex").value = "-1";
    document.getElementById("printFormTitle").textContent = "Add New Print";
    document.getElementById("printSubmitBtn").innerHTML = '<i class="ph ph-plus"></i> Add Print';
    document.getElementById("printCancelBtn").classList.add("hidden");
};
