/* ==========================================================================
   Portfolio interactivity
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {

  const navList = document.getElementById('navList');
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = document.querySelectorAll('main section[id]');
  const header = document.getElementById('siteHeader');
  const backToTop = document.getElementById('backToTop');
  const yearEl = document.getElementById('yr');
  const heroSection = document.querySelector('[data-animate-hero]');

  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* trigger hero corner/tag entrance */
  if (heroSection) {
    requestAnimationFrame(() => heroSection.classList.add('loaded'));
  }

  /* -------------------------
     Mobile menu toggle
     ------------------------- */
  if (hamburger && navList) {
    hamburger.addEventListener('click', () => {
      const isOpen = navList.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', String(isOpen));
      hamburger.classList.toggle('is-open', isOpen);
    });

    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        navList.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* -------------------------
     Smooth scroll with header offset
     ------------------------- */
  const headerHeight = () => header ? header.offsetHeight : 72;

  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (!href || href === '#') return;
      const target = document.querySelector(href);
      if (!target) return;
      e.preventDefault();
      const top = target.getBoundingClientRect().top + window.scrollY - headerHeight() - 8;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });

  /* -------------------------
     Active nav link on scroll
     (rootMargin band near the top of the viewport, rather than
     requiring 50% of a section's area to be visible — tall sections
     like Featured Projects never reach that threshold otherwise)
     ------------------------- */
  if (sections.length) {
    const firstLink = document.querySelector('.nav-link[href="#home"]');
    if (firstLink) firstLink.classList.add('active');

    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        const id = entry.target.id;
        const link = document.querySelector(`.nav-link[href="#${id}"]`);
        if (entry.isIntersecting) {
          document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
          if (link) link.classList.add('active');
        }
      });
    }, { root: null, rootMargin: `-${headerHeight() + 20}px 0px -55% 0px`, threshold: 0 });

    sections.forEach(s => observer.observe(s));
  }

  /* -------------------------
     Header hide/show + back-to-top
     ------------------------- */
  let lastScroll = window.pageYOffset || 0;
  const showBackToTopThreshold = 300;

  window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset || 0;

    if (backToTop) {
      if (currentScroll > showBackToTopThreshold) backToTop.classList.add('show');
      else backToTop.classList.remove('show');
    }

    if (header) {
      if (currentScroll <= 10) header.classList.remove('hide');
      else if (currentScroll > lastScroll + 10) header.classList.add('hide');
      else if (currentScroll < lastScroll - 10) header.classList.remove('hide');
    }

    lastScroll = currentScroll;
  });

  /* -------------------------
     Scroll-triggered reveal animations
     ------------------------- */
  const revealEls = document.querySelectorAll('.reveal');
  if (revealEls.length) {
    const revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(el => revealObserver.observe(el));
  }

  /* stagger project cards specifically */
  document.querySelectorAll('.project-card.reveal').forEach((card, i) => {
    card.style.transitionDelay = `${i * 90}ms`;
  });

  /* -------------------------
     GitHub live stats (public API, no auth)
     ------------------------- */
  const ghRepos = document.getElementById('ghRepos');
  const ghSince = document.getElementById('ghSince');

  if (ghRepos) {
    fetch('https://api.github.com/users/onyedikachinzute')
      .then(res => {
        if (!res.ok) throw new Error('GitHub API request failed');
        return res.json();
      })
      .then(data => {
        animateCount(ghRepos, data.public_repos ?? 0);
        if (ghSince && data.created_at) {
          ghSince.textContent = new Date(data.created_at).getFullYear();
        }
      })
      .catch(() => {
        [ghRepos, ghSince].forEach(el => {
          if (el) el.textContent = '—';
        });
      });
  }

  function animateCount(el, target) {
    if (!el) return;
    const duration = 900;
    const start = performance.now();
    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  /* -------------------------
     Light / dark theme toggle
     (initial theme is already applied by the inline head script
     to avoid a flash of the wrong theme; this just wires the button)
     ------------------------- */
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const root = document.documentElement;
      const current = root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      const next = current === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) { /* storage unavailable */ }
      themeToggle.setAttribute('aria-label', next === 'light' ? 'Switch to dark mode' : 'Switch to light mode');
    });
  }

  /* -------------------------
     Extension-agnostic image resolution
     Given a base path with no extension (e.g. "projects/screenshots/x/01"),
     try each candidate extension in order and resolve with the first one
     that actually loads. Lets screenshots be a mix of .png/.jpg/.jpeg/.webp
     without any per-project configuration.
     If the given path already has a recognized extension, it's tried as-is
     first (so old-style hardcoded paths with an extension still work).
     ------------------------- */
  const SHOT_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webp'];

  function resolveImage(basePath) {
    return new Promise(resolve => {
      const hasExt = /\.(png|jpe?g|webp|gif)$/i.test(basePath);
      const candidates = hasExt
        ? [basePath, ...SHOT_EXTENSIONS.map(ext => `${basePath}.${ext}`)]
        : SHOT_EXTENSIONS.map(ext => `${basePath}.${ext}`);

      let i = 0;
      function tryNext() {
        if (i >= candidates.length) { resolve(null); return; }
        const src = candidates[i++];
        const img = new Image();
        img.onload = () => resolve(src);
        img.onerror = tryNext;
        img.src = src;
      }
      tryNext();
    });
  }

  /* -------------------------
     Featured card screenshots
     Each project-card can carry data-shot="projects/screenshots/<slug>/01"
     (extension omitted — resolveImage figures out which format exists).
     If nothing loads, the original icon placeholder is left untouched.
     ------------------------- */
  document.querySelectorAll('.pc-visual[data-shot]').forEach(visual => {
    const base = visual.getAttribute('data-shot');
    if (!base) return;
    resolveImage(base).then(src => {
      if (!src) return; /* no screenshot in any format yet — keep the icon */
      visual.classList.add('has-shot');
      const shotEl = document.createElement('img');
      shotEl.src = src;
      shotEl.alt = '';
      shotEl.className = 'pc-shot';
      const fade = document.createElement('div');
      fade.className = 'pc-shot-fade';
      visual.prepend(fade);
      visual.prepend(shotEl);
      requestAnimationFrame(() => shotEl.classList.add('loaded'));
    });
  });

  /* -------------------------
     Screenshot gallery + lightbox (project detail pages)
     Gallery container: <div class="shot-gallery" data-shots='["projects/screenshots/x/01", ...]'>
     Base paths with no extension are resolved against several formats;
     missing files (no format found) are silently skipped. If none load,
     the section stays hidden via the "empty" class.
     ------------------------- */
  const galleries = document.querySelectorAll('.shot-gallery[data-shots]');
  if (galleries.length) {
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.innerHTML = `
      <button class="lightbox-close" aria-label="Close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
      <button class="lightbox-nav prev" aria-label="Previous image"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg></button>
      <img src="" alt="" />
      <button class="lightbox-nav next" aria-label="Next image"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg></button>
    `;
    document.body.appendChild(lightbox);
    const lbImg = lightbox.querySelector('img');
    const closeBtn = lightbox.querySelector('.lightbox-close');
    const prevBtn = lightbox.querySelector('.lightbox-nav.prev');
    const nextBtn = lightbox.querySelector('.lightbox-nav.next');
    let activeShots = [];
    let activeIndex = 0;

    function openLightbox(shots, index) {
      activeShots = shots;
      activeIndex = index;
      lbImg.src = activeShots[activeIndex];
      lightbox.classList.add('open');
      document.body.style.overflow = 'hidden';
    }
    function closeLightbox() {
      lightbox.classList.remove('open');
      document.body.style.overflow = '';
    }
    function showDelta(delta) {
      activeIndex = (activeIndex + delta + activeShots.length) % activeShots.length;
      lbImg.src = activeShots[activeIndex];
    }
    closeBtn.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });
    prevBtn.addEventListener('click', () => showDelta(-1));
    nextBtn.addEventListener('click', () => showDelta(1));
    document.addEventListener('keydown', e => {
      if (!lightbox.classList.contains('open')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') showDelta(-1);
      if (e.key === 'ArrowRight') showDelta(1);
    });

    galleries.forEach(gallery => {
      let shots = [];
      try { shots = JSON.parse(gallery.getAttribute('data-shots')); } catch (e) { shots = []; }
      if (!shots.length) return;

      Promise.all(shots.map(resolveImage)).then(resolved => {
        const loadedShots = resolved.filter(Boolean);
        renderGallery(loadedShots);
      });

      function renderGallery(loadedShots) {
        if (!loadedShots.length) { gallery.classList.add('empty'); return; }
        gallery.classList.remove('empty');
        loadedShots.forEach((src, i) => {
          const thumb = document.createElement('div');
          thumb.className = 'shot-thumb';
          thumb.innerHTML = `
            <img src="${src}" alt="Screenshot ${i + 1}" />
            <span class="zoom-hint"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 21l-4.35-4.35M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16z"/></svg></span>
          `;
          const imgEl = thumb.querySelector('img');
          imgEl.addEventListener('load', () => imgEl.classList.add('loaded'));
          if (imgEl.complete) imgEl.classList.add('loaded');
          thumb.addEventListener('click', () => openLightbox(loadedShots, i));
          gallery.appendChild(thumb);
        });
      }
    });
  }

});