// app.js: theme toggle, hero animation, and list search/pagination
document.addEventListener('DOMContentLoaded', function () {
  // Theme toggle (keeps behavior)
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = document.getElementById('theme-icon');
  const preferred = localStorage.getItem('vocab-theme') || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  setTheme(preferred);
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const next = document.documentElement.classList.contains('dark-mode') ? 'light' : 'dark';
      setTheme(next);
      localStorage.setItem('vocab-theme', next);
    });
  }

  function setTheme(name) {
    if (name === 'dark') {
      document.documentElement.classList.add('dark-mode');
      if (themeIcon) themeIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>';
      const label = document.getElementById('theme-label');
      if (label) label.textContent = 'Bonne nuit';
      if (themeToggle) themeToggle.setAttribute('aria-pressed','true');
    } else {
      document.documentElement.classList.remove('dark-mode');
      if (themeIcon) themeIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M6.76 4.84l-1.8-1.79L3.17 4.84l1.79 1.8 1.8-1.8zM1 13h3v-2H1v2zm10 8h2v-3h-2v3zm7.83-16.17l-1.79 1.79 1.8 1.8 1.79-1.79-1.8-1.8zM20 11v2h3v-2h-3zM4.24 19.16l1.79-1.8-1.8-1.79-1.79 1.8 1.8 1.79zM12 6a6 6 0 100 12 6 6 0 000-12z"/></svg>';
      const label = document.getElementById('theme-label');
      if (label) label.textContent = 'Bonne journée';
      if (themeToggle) themeToggle.setAttribute('aria-pressed','false');
    }
  }

  // Hero fade-in
  const hero = document.querySelector('.hero');
  if (hero) {
    setTimeout(() => hero.classList.add('visible'), 60);
  }
  // make nav buttons work
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const href = btn.getAttribute('data-href');
      if (href) window.location.href = href;
    });
  });
  // make table rows clickable
  document.querySelectorAll('tr[data-href]').forEach(r => {
    r.style.cursor = 'pointer';
    r.addEventListener('click', () => {
      const href = r.getAttribute('data-href');
      if (href) window.location.href = href;
    });
  });
});
