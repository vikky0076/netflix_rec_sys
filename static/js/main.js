// ============================================================
// FlixPulse — Premium Movie Streaming Platform UI Interactivity
// static/js/main.js
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

  // ── 0. Cinematic Netflix Opening Splash Screen ──────────────
  const splash = document.getElementById('netflixSplash');
  if (splash) {
    setTimeout(() => {
      splash.classList.add('fade-out');
      setTimeout(() => splash.remove(), 850);
    }, 1650);
  }

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

    const iconBtns = wrapper.querySelectorAll('.search-icon-btn, .search-icon');
    iconBtns.forEach(iconBtn => {
      iconBtn.addEventListener('click', (e) => {
        const q = searchInput.value.trim();
        if (!q) {
          e.preventDefault();
          searchInput.focus();
        } else {
          const form = searchInput.closest('form');
          if (form) {
            const overlay = document.querySelector('.loading-overlay');
            if (overlay) overlay.classList.remove('hidden');
            form.submit();
          }
        }
      });
    });

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

  // ── 5. Three-Dots Menu Dropdown Toggle ──────────────────────
  const threeDotsBtn = document.getElementById('threeDotsBtn');
  const langDropdownMenu = document.getElementById('langDropdownMenu');
  const langDropdownWrap = document.getElementById('langDropdownWrap');

  if (threeDotsBtn && langDropdownMenu) {
    threeDotsBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isShowing = langDropdownMenu.classList.toggle('show');
      threeDotsBtn.classList.toggle('active', isShowing);
    });

    document.addEventListener('click', (e) => {
      if (langDropdownWrap && !langDropdownWrap.contains(e.target)) {
        langDropdownMenu.classList.remove('show');
        threeDotsBtn.classList.remove('active');
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        langDropdownMenu.classList.remove('show');
        threeDotsBtn.classList.remove('active');
      }
    });
  }

  // ── 6. Fixed Mobile Bottom Nav Triggers ─────────────────────
  const mobileSearchTrigger = document.getElementById('mobileSearchTrigger');
  const mobileLangTrigger = document.getElementById('mobileLangTrigger');
  const mainSearchInput = document.querySelector('.search-input');

  if (mobileSearchTrigger && mainSearchInput) {
    mobileSearchTrigger.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      setTimeout(() => mainSearchInput.focus(), 300);
    });
  }

  if (mobileLangTrigger && threeDotsBtn && langDropdownMenu) {
    mobileLangTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      const isShowing = langDropdownMenu.classList.toggle('show');
      threeDotsBtn.classList.toggle('active', isShowing);
    });
  }

  // ── 7. YouTube-Style Mobile Search Interception & Search Page Logic ──
  const isMobile = () => window.innerWidth <= 768 || ('ontouchstart' in window);
  const isSearchPage = window.location.pathname.startsWith('/search');

  // Intercept touch/focus on regular search inputs when on mobile devices
  if (!isSearchPage) {
    const navbarSearchInputs = document.querySelectorAll('.search-input');
    navbarSearchInputs.forEach(input => {
      ['focus', 'click', 'touchstart'].forEach(evtType => {
        input.addEventListener(evtType, (e) => {
          if (isMobile()) {
            e.preventDefault();
            window.location.href = '/search';
          }
        });
      });
    });
  }

  // YouTube Search Page Real-Time Search & Interactivity
  const ytSearchInput = document.getElementById('ytSearchInput');
  const ytClearInputBtn = document.getElementById('ytClearInputBtn');
  const ytHistorySection = document.getElementById('ytHistorySection');
  const ytPopularSection = document.getElementById('ytPopularSection');
  const ytSuggestionsContainer = document.getElementById('ytSuggestionsContainer');
  const ytClearHistoryBtn = document.getElementById('ytClearHistoryBtn');

  if (ytSearchInput) {
    let ytDebounceTimer;

    const toggleClearBtn = () => {
      if (ytClearInputBtn) {
        if (ytSearchInput.value.trim().length > 0) {
          ytClearInputBtn.classList.remove('hidden');
        } else {
          ytClearInputBtn.classList.add('hidden');
        }
      }
    };

    toggleClearBtn();

    ytSearchInput.addEventListener('input', () => {
      toggleClearBtn();
      clearTimeout(ytDebounceTimer);
      const query = ytSearchInput.value.trim();

      if (query.length < 2) {
        if (ytSuggestionsContainer) ytSuggestionsContainer.classList.add('hidden');
        if (ytHistorySection) ytHistorySection.classList.remove('hidden');
        if (ytPopularSection) ytPopularSection.classList.remove('hidden');
        return;
      }

      ytDebounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
          const data = await res.json();

          if (!data || !data.length) {
            if (ytSuggestionsContainer) {
              ytSuggestionsContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted);">No movies found matching search query.</div>';
              ytSuggestionsContainer.classList.remove('hidden');
            }
            if (ytHistorySection) ytHistorySection.classList.add('hidden');
            if (ytPopularSection) ytPopularSection.classList.add('hidden');
            return;
          }

          if (ytSuggestionsContainer) {
            ytSuggestionsContainer.innerHTML = data.map(m => {
              const thumbHtml = m.poster
                ? `<img src="${m.poster}" class="yt-sug-thumb" alt="${m.title}" />`
                : `<div class="yt-sug-thumb" style="display:flex;align-items:center;justify-content:center;background:#222;font-size:1.4rem;">🎬</div>`;

              return `
                <a href="/recommend?movie=${encodeURIComponent(m.title)}" class="yt-suggestion-item">
                  ${thumbHtml}
                  <div class="yt-sug-details">
                    <div class="yt-sug-title">${m.title}</div>
                    <div class="yt-sug-meta">
                      <span class="lang-badge lang-${m.language.toLowerCase()}">${m.language}</span>
                      <span>${m.release_year}</span>
                      <span>⭐ ${m.rating}</span>
                    </div>
                  </div>
                  <i class="bi bi-chevron-right" style="color: var(--text-muted); font-size: 0.9rem;"></i>
                </a>
              `;
            }).join('');

            ytSuggestionsContainer.classList.remove('hidden');
          }

          if (ytHistorySection) ytHistorySection.classList.add('hidden');
          if (ytPopularSection) ytPopularSection.classList.add('hidden');
        } catch (_) {}
      }, 180);
    });

    if (ytClearInputBtn) {
      ytClearInputBtn.addEventListener('click', () => {
        ytSearchInput.value = '';
        toggleClearBtn();
        if (ytSuggestionsContainer) ytSuggestionsContainer.classList.add('hidden');
        if (ytHistorySection) ytHistorySection.classList.remove('hidden');
        if (ytPopularSection) ytPopularSection.classList.remove('hidden');
        ytSearchInput.focus();
      });
    }

    // Fill search input buttons
    document.querySelectorAll('.yt-hist-fill-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const q = btn.dataset.query;
        if (q) {
          ytSearchInput.value = q;
          ytSearchInput.dispatchEvent(new Event('input'));
          ytSearchInput.focus();
        }
      });
    });

    if (ytClearHistoryBtn) {
      ytClearHistoryBtn.addEventListener('click', async () => {
        try {
          await fetch('/api/history', { method: 'DELETE' });
          if (ytHistorySection) ytHistorySection.remove();
        } catch (_) {}
      });
    }
  }

});
