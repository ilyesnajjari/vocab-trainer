// app.js: theme toggle, hero animation, and list search/pagination
document.addEventListener('DOMContentLoaded', function () {
  // compute navbar height and expose as CSS variable so content isn't overlapped
  (function(){
    try{
      var nav = document.querySelector('.navbar');
      function updateNavHeight(){
        if(!nav) return;
        var h = nav.offsetHeight || 64;
        document.documentElement.style.setProperty('--nav-height', h + 'px');
        var app = document.querySelector('.app-content');
        if(app) app.style.paddingTop = 'calc(' + h + 'px + 8px)';
      }
      updateNavHeight();
      window.addEventListener('resize', function(){ setTimeout(updateNavHeight, 120); });
    }catch(e){/* ignore */}
  })();
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
  // Nav items are real anchors now; no JS navigation required.
  // ensure delete forms inside rows don't trigger the row click navigation
  document.querySelectorAll('.delete-form').forEach(f => {
    f.addEventListener('click', function(e){
      e.stopPropagation();
    });
    // also stop propagation on the submit button to be safe
    f.querySelectorAll('button').forEach(b => b.addEventListener('click', function(e){ e.stopPropagation(); }));
  });
  // make table rows clickable
  document.querySelectorAll('tr[data-href]').forEach(r => {
    r.style.cursor = 'pointer';
    // ensure keyboard can activate row (Enter/Space)
    r.addEventListener('click', () => {
      const href = r.getAttribute('data-href');
      if (href) window.location.href = href;
    });
    r.addEventListener('keydown', function(e){
      var key = (e.key || '').toLowerCase();
      if(key === 'enter' || key === ' ' || key === 'spacebar'){
        e.preventDefault();
        const href = this.getAttribute('data-href');
        if(href) window.location.href = href;
      }
    });
  });

  // Global keyboard shortcuts for accessibility
  document.addEventListener('keydown', function(e){
    // ignore when typing in inputs or textareas
    var tag = document.activeElement && document.activeElement.tagName && document.activeElement.tagName.toLowerCase();
    var key = (e.key || '').toLowerCase();
    if(tag === 'input' || tag === 'textarea') return;

    try{
      if(key === 's') { document.getElementById('show-btn')?.click(); }
      else if(key === 'k') { document.getElementById('skip-btn')?.click(); }
      else if(key === 'f') { document.getElementById('flip-btn')?.click(); }
      else if(key === 'n') { document.getElementById('next-btn')?.click(); }
      else if(key === 'r') { document.getElementById('retry-btn')?.click(); }
      else if(key === 'h') { document.getElementById('home-btn')?.click(); }
      else if(key === '/') { // focus search box on list page
        var q = document.querySelector('input[name="q"]');
        if(q){ e.preventDefault(); q.focus(); }
      }
      // Arrow key navigation: up/down to move between rows, left/right for pagination or next/retry
      else if(key === 'arrowdown' || key === 'down') {
        e.preventDefault();
        const rows = Array.from(document.querySelectorAll('tr[data-href]'));
        if(rows.length === 0) return;
        const idx = rows.indexOf(document.activeElement);
        const next = (idx === -1) ? rows[0] : rows[Math.min(rows.length-1, idx+1)];
        next.focus(); next.scrollIntoView({block:'nearest', behavior:'smooth'});
      }
      else if(key === 'arrowup' || key === 'up') {
        e.preventDefault();
        const rows = Array.from(document.querySelectorAll('tr[data-href]'));
        if(rows.length === 0) return;
        const idx = rows.indexOf(document.activeElement);
        const prev = (idx === -1) ? rows[rows.length-1] : rows[Math.max(0, idx-1)];
        prev.focus(); prev.scrollIntoView({block:'nearest', behavior:'smooth'});
      }
      else if(key === 'arrowright' || key === 'right') {
        // try result 'Next' button first, then pagination next
        const nextBtn = document.getElementById('next-btn');
        if(nextBtn){ nextBtn.click(); }
        else {
          const nextLink = Array.from(document.querySelectorAll('.pagination .page-link')).find(a => /next/i.test(a.textContent));
          if(nextLink) nextLink.click();
        }
      }
      else if(key === 'arrowleft' || key === 'left') {
        // try result 'Retry' or 'Previous' pagination
        const retryBtn = document.getElementById('retry-btn');
        if(retryBtn){ retryBtn.click(); }
        else {
          const prevLink = Array.from(document.querySelectorAll('.pagination .page-link')).find(a => /previous/i.test(a.textContent));
          if(prevLink) prevLink.click();
        }
      }
    }catch(err){ /* ignore */ }
  });
});
