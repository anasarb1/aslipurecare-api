/* ============================================================
   AslipureCare — Main JavaScript
   ============================================================ */

const API_BASE = 'https://aslipurecare-api-1.onrender.com';

/* ── Emoji map for product names ─────────────────────────── */
function productEmoji(name = '') {
  const n = name.toLowerCase();
  if (n.includes('serum'))       return '✨';
  if (n.includes('cleanser'))    return '🫧';
  if (n.includes('moistur'))     return '💧';
  if (n.includes('spf') || n.includes('sunscreen')) return '☀️';
  if (n.includes('toner'))       return '🌿';
  if (n.includes('mask'))        return '🌸';
  if (n.includes('eye'))         return '👁️';
  if (n.includes('oil'))         return '🫙';
  if (n.includes('cream'))       return '🧴';
  return '✦';
}

/* ── Category tag from name ──────────────────────────────── */
function productCategory(name = '') {
  const n = name.toLowerCase();
  if (n.includes('serum'))       return 'Treatment';
  if (n.includes('cleanser'))    return 'Cleanse';
  if (n.includes('moistur') || n.includes('cream')) return 'Hydrate';
  if (n.includes('spf') || n.includes('sunscreen')) return 'Protect';
  if (n.includes('toner'))       return 'Balance';
  if (n.includes('mask'))        return 'Treat';
  return 'Skincare';
}

/* ── Render a product card ───────────────────────────────── */
function renderProductCard(product) {
  const emoji    = productEmoji(product.name);
  const category = productCategory(product.name);
  const price    = Number(product.price).toFixed(2);
  return `
    <article class="product-card" data-id="${product.id}">
      <div class="product-image">
        <span class="product-badge-tag">${category}</span>
        ${emoji}
      </div>
      <div class="product-info">
        <h3>${escapeHtml(product.name)}</h3>
        <p>${escapeHtml(product.description)}</p>
        <div class="product-footer">
          <span class="price">£${price}</span>
          <button class="add-btn" aria-label="Add to bag" title="Add to bag">+</button>
        </div>
      </div>
    </article>`;
}

/* ── Escape HTML ─────────────────────────────────────────── */
function escapeHtml(str) {
  const el = document.createElement('div');
  el.textContent = str;
  return el.innerHTML;
}

/* ── Fetch products and populate grid ───────────────────── */
async function loadProducts(gridId, limit = null) {
  const grid = document.getElementById(gridId);
  if (!grid) return;

  grid.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Loading products…</p>
    </div>`;

  try {
    const res = await fetch(`${API_BASE}/products`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    let products = await res.json();

    if (!products.length) {
      grid.innerHTML = `<div class="error-state"><p>No products found.</p></div>`;
      return;
    }

    if (limit) products = products.slice(0, limit);

    grid.innerHTML = products.map(renderProductCard).join('');

    // Update count badge if present
    const counter = document.getElementById('product-count');
    if (counter) counter.textContent = `${products.length} products`;

    // Add-to-bag interaction
    grid.querySelectorAll('.add-btn').forEach(btn => {
      btn.addEventListener('click', handleAddToBag);
    });

  } catch (err) {
    grid.innerHTML = `
      <div class="error-state">
        <p>⚠️ Couldn't load products — is the API running at <code>${API_BASE}</code>?</p>
        <button class="btn btn-outline" style="margin-top:1rem" onclick="loadProducts('${gridId}', ${limit})">
          Retry
        </button>
      </div>`;
    console.error('Products fetch error:', err);
  }
}

/* ── Add-to-bag feedback ─────────────────────────────────── */
function handleAddToBag(e) {
  const btn  = e.currentTarget;
  const card = btn.closest('.product-card');
  const name = card.querySelector('h3')?.textContent ?? 'Item';

  btn.textContent  = '✓';
  btn.style.background = 'var(--mauve)';
  btn.disabled = true;

  showToast(`${name} added to bag`);

  setTimeout(() => {
    btn.textContent  = '+';
    btn.style.background = '';
    btn.disabled = false;
  }, 2000);
}

/* ── Toast notification ──────────────────────────────────── */
function showToast(msg) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    Object.assign(toast.style, {
      position: 'fixed', bottom: '2rem', right: '2rem', zIndex: '999',
      background: 'var(--dark)', color: '#fff',
      padding: '0.8rem 1.6rem', borderRadius: '50px',
      fontSize: '0.88rem', fontFamily: 'var(--font-body)',
      boxShadow: 'var(--shadow-hover)',
      transform: 'translateY(20px)', opacity: '0',
      transition: '0.3s ease',
    });
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  requestAnimationFrame(() => {
    toast.style.transform = 'translateY(0)';
    toast.style.opacity   = '1';
  });
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.style.transform = 'translateY(20px)';
    toast.style.opacity   = '0';
  }, 2800);
}

/* ── Hamburger menu ──────────────────────────────────────── */
function initHamburger() {
  const btn   = document.querySelector('.hamburger');
  const links = document.querySelector('.nav-links');
  if (!btn || !links) return;
  btn.addEventListener('click', () => {
    links.classList.toggle('open');
    btn.setAttribute('aria-expanded', links.classList.contains('open'));
  });
  // Close on link click
  links.querySelectorAll('a').forEach(a =>
    a.addEventListener('click', () => links.classList.remove('open'))
  );
}

/* ── Contact form ────────────────────────────────────────── */
function initContactForm() {
  const form = document.getElementById('contact-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('[type="submit"]');
    btn.textContent = 'Sending…';
    btn.disabled    = true;

    // Simulate network delay
    await new Promise(r => setTimeout(r, 1200));

    form.style.display = 'none';
    const success = document.getElementById('form-success');
    if (success) success.style.display = 'block';
  });
}

/* ── Active nav link ─────────────────────────────────────── */
function setActiveNav() {
  const path = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href')?.split('/').pop();
    if (href === path) a.classList.add('active');
  });
}

/* ── Scroll-reveal (simple) ──────────────────────────────── */
function initReveal() {
  if (!('IntersectionObserver' in window)) return;
  const els = document.querySelectorAll('.product-card, .value-card, .team-card, .testimonial-card');
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(el => {
      if (el.isIntersecting) {
        el.target.style.opacity   = '1';
        el.target.style.transform = 'translateY(0)';
        obs.unobserve(el.target);
      }
    });
  }, { threshold: 0.1 });

  els.forEach(el => {
    el.style.opacity   = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    obs.observe(el);
  });
}

/* ── Init ────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  setActiveNav();
  initHamburger();
  initContactForm();
  initReveal();

  // Page-specific loaders
  if (document.getElementById('featured-grid')) {
    loadProducts('featured-grid', 3);
  }
  if (document.getElementById('all-products-grid')) {
    loadProducts('all-products-grid');
  }
});
