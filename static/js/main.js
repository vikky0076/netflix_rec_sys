// ============================================================
// FlixPulse — Premium Movie Streaming Platform UI Interactivity
// static/js/main.js
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

  // ── 1. Scroll-Aware Navbar ──────────────────────────────────
  const nav = document.querySelector('.stream-nav');
  if (nav) {
    const updateNav = () => {
      nav.classList.toggle('scrolled', window.scrollY > 20);
    };
    window.addEventListener('scroll', updateNav, { passive: true });
    updateNav();
  }

  // ── 2. Rich Search Autocomplete with Poster Thumbnails ──────
  const searchInputs = document.querySelectorAll('.search-input');
  
  searchInputs.forEach(searchInput => {
    let acList = null;
    let acIndex = -1;
    let debounceTimer;

    const wrapper = searchInput.closest('.search-box-wrap') || searchInput.parentElement;
    if (!wrapper) return;

    acList = document.createElement('div');
    acList.className = 'autocomplete-list';
    acList.style.display = 'none';
    wrapper.appendChild(acList);

    const getSelectedLang = () => {
      const activePill = document.querySelector('.filter-pill.active');
      return activePill ? activePill.dataset.lang || 'All' : 'All';
    };

    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      const q = searchInput.value.trim();
      if (q.length < 2) { hideAC(); return; }

      debounceTimer = setTimeout(() => fetchSuggestions(q, getSelectedLang()), 200);
    });

    searchInput.addEventListener('keydown', (e) => {
      const items = acList.querySelectorAll('.autocomplete-item');
      if (!items.length) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        acIndex = Math.min(acIndex + 1, items.length - 1);
        updateACActive(items);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        acIndex = Math.max(acIndex - 1, -1);
        updateACActive(items);
      } else if (e.key === 'Enter' && acIndex >= 0) {
        e.preventDefault();
        searchInput.value = items[acIndex].dataset.title;
        hideAC();
        searchInput.closest('form')?.submit();
      } else if (e.key === 'Escape') {
        hideAC();
      }
    });

    async function fetchSuggestions(query, lang) {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&lang=${encodeURIComponent(lang)}`);
        const data = await res.json();
        showAC(data, query);
      } catch (_) {
        hideAC();
      }
    }

    function showAC(movies, query) {
      if (!acList || !movies.length) { hideAC(); return; }
      acIndex = -1;
      
      acList.innerHTML = movies.map(m => {
        const thumbHtml = m.poster
          ? `<img src="${m.poster}" class="ac-thumb" alt="${m.title}" />`
          : `<div class="ac-thumb" style="display:flex;align-items:center;justify-content:center;font-size:1.2rem;">🎬</div>`;

        return `
          <div class="autocomplete-item" data-title="${m.title}">
            ${thumbHtml}
            <div class="ac-info">
              <div class="ac-title">${m.title}</div>
              <div class="ac-meta">
                <span class="lang-badge lang-${m.language.toLowerCase()}">${m.language}</span>
                <span>${m.release_year}</span>
                <span>⭐ ${m.rating}</span>
              </div>
            </div>
          </div>
        `;
      }).join('');

      acList.querySelectorAll('.autocomplete-item').forEach(item => {
        item.addEventListener('mousedown', (e) => {
          e.preventDefault();
          searchInput.value = item.dataset.title;
          hideAC();
          searchInput.closest('form')?.submit();
        });
      });

      acList.style.display = 'block';
    }

    function hideAC() {
      if (acList) acList.style.display = 'none';
      acIndex = -1;
    }

    function updateACActive(items) {
      items.forEach((el, i) => el.classList.toggle('active', i === acIndex));
      if (acIndex >= 0) searchInput.value = items[acIndex].dataset.title;
    }

    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target)) hideAC();
    });
  });

  // ── 3. Search History Modal Interactivity ──────────────────
  const historyBtn = document.getElementById('historyBtn');
  const historyModal = document.getElementById('historyModal');
  const closeHistoryModal = document.getElementById('closeHistoryModal');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');

  if (historyBtn && historyModal) {
    historyBtn.addEventListener('click', () => {
      historyModal.classList.remove('hidden');
    });
  }

  if (closeHistoryModal && historyModal) {
    closeHistoryModal.addEventListener('click', () => {
      historyModal.classList.add('hidden');
    });
  }

  if (historyModal) {
    historyModal.addEventListener('click', (e) => {
      if (e.target === historyModal) historyModal.classList.add('hidden');
    });
  }

  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', async () => {
      try {
        await fetch('/api/history', { method: 'DELETE' });
        window.location.reload();
      } catch (_) {}
    });
  }

  // ── 4. Loading Overlay on Form Submit ──────────────────────
  const forms = document.querySelectorAll('form');
  const overlay = document.querySelector('.loading-overlay');

  forms.forEach(form => {
    form.addEventListener('submit', () => {
      const q = form.querySelector('input[name="movie"]')?.value?.trim();
      if (!q) return;
      if (overlay) overlay.classList.remove('hidden');
    });
  });

  window.addEventListener('pageshow', () => {
    if (overlay) overlay.classList.add('hidden');
  });

});
