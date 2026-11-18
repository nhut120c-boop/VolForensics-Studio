/* Decorative analysis canvas and an independent full-screen table view. */
(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const pane = document.getElementById('tab-pane-table');
    const fullscreenButton = document.getElementById('btn-table-fullscreen');
    const visual = document.getElementById('analysis-visual');
    const canvas = document.getElementById('analysis-code-canvas');
    const toggle = document.getElementById('btn-toggle-analysis-fx');
    const clock = document.getElementById('analysis-fx-time');
    const context = canvas.getContext('2d');
    let enabled = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    try {
      const saved = localStorage.getItem('analysisFxEnabled');
      if (saved !== null) enabled = saved === 'true';
    } catch (_) {}
    let running = false;
    let activeTab = 'terminal';
    let started = 0;
    let frame = null;
    let lastPaint = 0;
    let width = 0;
    let height = 0;
    let drops = [];
    let nativeFullscreen = false;
    const glyphs = '0123456789ABCDEF{}[]<>;:+-=/';

    function fitCanvas() {
      const bounds = canvas.getBoundingClientRect();
      if (!bounds.width || !bounds.height || !context) return;
      width = Math.floor(bounds.width);
      height = Math.floor(bounds.height);
      const scale = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = Math.floor(width * scale);
      canvas.height = Math.floor(height * scale);
      context.setTransform(scale, 0, 0, scale, 0, 0);
      context.fillStyle = '#000';
      context.fillRect(0, 0, width, height);
      drops = Array.from({length: Math.min(100, Math.ceil(width / 18))}, () => -Math.random() * height);
    }

    function paint(now) {
      frame = null;
      if (!running || !enabled || activeTab !== 'terminal' || document.hidden || !context) return;
      if (now - lastPaint >= 80) {
        lastPaint = now;
        context.fillStyle = 'rgba(0,0,0,0.17)';
        context.fillRect(0, 0, width, height);
        context.font = '13px Consolas, monospace';
        drops.forEach((y, index) => {
          context.fillStyle = index % 5 === 0 ? '#adffcb' : '#39ff88';
          context.fillText(glyphs[Math.floor(Math.random() * glyphs.length)], index * 18, y);
          drops[index] = y > height + 80 ? -Math.random() * 140 : y + 12 + index % 5;
        });
        const seconds = Math.floor((now - started) / 1000);
        clock.textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
      }
      frame = requestAnimationFrame(paint);
    }

    function updateEffect() {
      if (frame !== null) cancelAnimationFrame(frame);
      frame = null;
      const visible = running && enabled && activeTab === 'terminal' && !document.hidden && Boolean(context);
      visual.hidden = !visible;
      toggle.textContent = `Hiệu ứng: ${enabled ? 'Bật' : 'Tắt'}`;
      toggle.setAttribute('aria-pressed', String(enabled));
      if (visible) {
        fitCanvas();
        lastPaint = 0;
        frame = requestAnimationFrame(paint);
      }
    }

    toggle.addEventListener('click', () => {
      enabled = !enabled;
      try { localStorage.setItem('analysisFxEnabled', String(enabled)); } catch (_) {}
      updateEffect();
    });
    document.addEventListener('analysis-state', event => {
      if (event.detail.running && !running) started = performance.now();
      running = event.detail.running;
      updateEffect();
    });
    document.addEventListener('visibilitychange', updateEffect);
    new ResizeObserver(fitCanvas).observe(canvas);

    function setExpanded(expanded) {
      pane.classList.toggle('table-expanded', expanded);
      document.body.classList.toggle('table-view-expanded', expanded);
      fullscreenButton.textContent = expanded ? 'Thoát toàn màn hình' : 'Toàn màn hình';
      fullscreenButton.setAttribute('aria-pressed', String(expanded));
      fullscreenButton.title = expanded ? 'Nhấn Esc để trở lại giao diện' : 'Phóng bảng dữ liệu; nhấn Esc để thoát';
    }

    async function leaveExpanded() {
      setExpanded(false);
      if (document.fullscreenElement === pane) {
        try { await document.exitFullscreen(); } catch (_) {}
      }
      nativeFullscreen = false;
    }

    fullscreenButton.addEventListener('click', async () => {
      if (pane.classList.contains('table-expanded')) {
        await leaveExpanded();
        fullscreenButton.focus();
        return;
      }
      setExpanded(true);
      // CSS expansion remains available when the browser blocks Fullscreen API.
      if (pane.requestFullscreen) {
        try { await pane.requestFullscreen(); nativeFullscreen = true; } catch (_) {}
      }
    });
    document.addEventListener('fullscreenchange', () => {
      if (document.fullscreenElement === pane) {
        nativeFullscreen = true;
        setExpanded(true);
      } else if (nativeFullscreen) {
        nativeFullscreen = false;
        setExpanded(false);
        fullscreenButton.focus();
      }
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && pane.classList.contains('table-expanded')) {
        void leaveExpanded();
        fullscreenButton.focus();
      }
    });
    document.addEventListener('analysis-view', event => {
      activeTab = event.detail.tab;
      updateEffect();
      if (activeTab !== 'table' && pane.classList.contains('table-expanded')) void leaveExpanded();
    });
    updateEffect();
  });
})();
