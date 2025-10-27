/* ======= Simple and clear DOM helpers ======= */
const navList = document.getElementById('navList');
const hamburger = document.getElementById('hamburger');
const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('main section[id]');
const header = document.getElementById('siteHeader');
const backToTop = document.getElementById('backToTop');
const yearEl = document.getElementById('yr');

/* Year (footer) */
if (yearEl) yearEl.textContent = new Date().getFullYear();

/* -------------------------
   Mobile menu toggle
   ------------------------- */
hamburger.addEventListener('click', () => {
  const isOpen = navList.classList.toggle('open');
  hamburger.setAttribute('aria-expanded', String(isOpen));
});

/* Close mobile menu when a nav link is clicked (keeps hamburger visible) */
navLinks.forEach(link => {
  link.addEventListener('click', () => {
    navList.classList.remove('open');
    hamburger.setAttribute('aria-expanded', 'false');
  });
});

/* -------------------------
   Smooth scroll with offset for sticky header
   ------------------------- */
const headerHeight = () => header ? header.offsetHeight : 64;

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    if (!href || href === '#') return;
    const target = document.querySelector(href);
    if (!target) return;
    e.preventDefault();

    // Compute top position minus header height and small gap
    const top = target.getBoundingClientRect().top + window.scrollY - headerHeight() - 8;
    window.scrollTo({ top, behavior: 'smooth' });
  });
});

/* -------------------------
   IntersectionObserver to update active nav link
   (improved thresholds so "Works" doesn't highlight "Projects")
   ------------------------- */
// Force "Home" active on load
document.querySelector('.nav-link[href="#home"]').classList.add('active');

const observerOptions = {
  root: null,
  threshold: 0.5, // must be at least 50% visible
};

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    const id = entry.target.id;
    const link = document.querySelector(`.nav-link[href="#${id}"]`);

    if (entry.isIntersecting) {
      document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
      if (link) link.classList.add('active');
    }
  });
}, observerOptions);

sections.forEach(s => observer.observe(s));

/* -------------------------
   Single scroll handler:
   - shows/hides header depending on scroll direction
   - shows back-to-top when scrolled past threshold
   ------------------------- */
let lastScroll = window.pageYOffset || 0;
const showBackToTopThreshold = 300; // px

window.addEventListener('scroll', () => {
  const currentScroll = window.pageYOffset || 0;

  // Back-to-top visibility
  if (currentScroll > showBackToTopThreshold) {
    backToTop.classList.add('show');
  } else {
    backToTop.classList.remove('show');
  }

  // header hide on scroll down, show on scroll up
  if (currentScroll <= 10) {
    // near top: always show header
    header.classList.remove('hide');
  } else if (currentScroll > lastScroll + 10) {
    // scrolling down (with small buffer)
    header.classList.add('hide');
  } else if (currentScroll < lastScroll - 10) {
    // scrolling up
    header.classList.remove('hide');
  }

  lastScroll = currentScroll;
});

/* Accessibility: ensure Back-to-top keyboard focus works */
backToTop.addEventListener('click', (e) => {
  // standard smooth scroll handled by anchor click handler above
});
