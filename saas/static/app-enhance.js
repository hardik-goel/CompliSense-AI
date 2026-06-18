/* CompliSense-AI — progressive UI enhancements for the app.
   Loaded after Chart.js (where present). All features are guarded and
   non-fatal so they never block the dashboard's own scripts. */
(function () {
  // 1) Dark-theme Chart.js globally to match the design system.
  //    Must run before charts are instantiated.
  try {
    if (window.Chart) {
      var C = window.Chart;
      C.defaults.color = '#94A3B8';
      C.defaults.borderColor = 'rgba(30, 45, 74, 0.55)';
      if (C.defaults.font) C.defaults.font.family = "'Inter', system-ui, -apple-system, sans-serif";
      if (C.defaults.scale) {
        if (C.defaults.scale.grid) {
          C.defaults.scale.grid.color = 'rgba(30, 45, 74, 0.5)';
          C.defaults.scale.grid.borderColor = 'rgba(30, 45, 74, 0.8)';
        }
        if (C.defaults.scale.ticks) C.defaults.scale.ticks.color = '#94A3B8';
      }
      if (C.defaults.plugins) {
        if (C.defaults.plugins.legend && C.defaults.plugins.legend.labels) {
          C.defaults.plugins.legend.labels.color = '#CBD5E1';
          C.defaults.plugins.legend.labels.usePointStyle = true;
        }
        if (C.defaults.plugins.tooltip) {
          var t = C.defaults.plugins.tooltip;
          t.backgroundColor = '#0D1525';
          t.titleColor = '#F1F5F9';
          t.bodyColor = '#94A3B8';
          t.borderColor = '#1E2D4A';
          t.borderWidth = 1;
          t.padding = 10;
          t.cornerRadius = 8;
        }
      }
    }
  } catch (e) { /* non-fatal */ }

  // 2) Cursor-follow spotlight on cards (matches the marketing site).
  document.addEventListener('mousemove', function (e) {
    var card = e.target && e.target.closest
      ? e.target.closest('.card, .stat-card, .report-card, .metric, .card-out, .feature-card')
      : null;
    if (!card) return;
    var r = card.getBoundingClientRect();
    card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    card.style.setProperty('--my', (e.clientY - r.top) + 'px');
  }, { passive: true });
})();

/* 3) Animated count-ups.
   - Dashboard stats are populated asynchronously by the page's own JS, so we
     observe them and animate on value change (never fighting the data fetch).
   - Static summary boxes (e.g. scan results) animate once on load. */
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function ease(p) { return 1 - Math.pow(1 - p, 3); }
  function intFrom(s) { var n = parseInt(String(s).replace(/[^0-9-]/g, ''), 10); return isNaN(n) ? null : n; }

  function animate(el, to) {
    var from = parseInt(el.getAttribute('data-cs-val') || '0', 10);
    if (isNaN(from)) from = 0;
    if (from === to || reduce) { el.setAttribute('data-cs-val', String(to)); el.textContent = String(to); return; }
    var dur = 800, t0 = null;
    el.setAttribute('data-cs-animating', '1');
    function step(ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min((ts - t0) / dur, 1);
      var cur = Math.round(from + (to - from) * ease(p));
      el.setAttribute('data-cs-val', String(cur));
      el.textContent = String(cur);
      if (p < 1) { requestAnimationFrame(step); }
      else { el.removeAttribute('data-cs-animating'); el.setAttribute('data-cs-val', String(to)); el.textContent = String(to); }
    }
    requestAnimationFrame(step);
  }

  function init() {
    ['totalProjects', 'totalScans', 'activeScans', 'completedScans'].forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      var run = function () {
        if (el.getAttribute('data-cs-animating')) return;       // ignore our own writes
        var to = intFrom(el.textContent);
        if (to === null || String(to) === el.getAttribute('data-cs-val')) return;
        animate(el, to);
      };
      new MutationObserver(run).observe(el, { childList: true, characterData: true, subtree: true });
      run();
    });
    document.querySelectorAll('.stat-box .value').forEach(function (el) {
      var to = intFrom(el.textContent);
      if (to === null) return;
      el.setAttribute('data-cs-val', '0');
      if (!reduce) el.textContent = '0';
      animate(el, to);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
