import { initDemo } from './demo.js';

const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

initDemo(document.getElementById('demo-root'), JSON.parse(document.getElementById('demo-data').textContent));

// 3D hero: only on capable devices, loaded after the page is usable. `?no3d` forces the 2D version.
function canRun3D() {
  if (new URLSearchParams(location.search).has('no3d')) return false;
  const c = navigator.connection;
  if (c && (c.saveData || /2g/.test(c.effectiveType || ''))) return false;
  if ((navigator.deviceMemory || 8) < 2 || (navigator.hardwareConcurrency || 8) < 2) return false;
  try {
    return !!document.createElement('canvas').getContext('webgl2');
  } catch {
    return false;
  }
}

function load3D() {
  const hero = document.querySelector('.hero');
  import('./hero3d.js')
    .then(({ startHero }) => {
      startHero(hero.querySelector('.hero-canvas'), { still: reduced });
      hero.classList.add('is-3d');
    })
    .catch(() => {}); // keep the SVG fallback
}

if (canRun3D()) {
  const later = window.requestIdleCallback || ((f) => setTimeout(f, 200));
  if (document.readyState === 'complete') later(load3D);
  else addEventListener('load', () => later(load3D), { once: true });
}

// Subtle tilt on featured cards, mouse only.
if (!reduced && matchMedia('(hover: hover) and (pointer: fine)').matches) {
  document.querySelectorAll('.tilt').forEach((card) => {
    card.addEventListener('pointermove', (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty('--ry', `${((e.clientX - r.left) / r.width - 0.5) * 6}deg`);
      card.style.setProperty('--rx', `${((e.clientY - r.top) / r.height - 0.5) * -6}deg`);
    });
    card.addEventListener('pointerleave', () => {
      card.style.setProperty('--rx', '0deg');
      card.style.setProperty('--ry', '0deg');
    });
  });
}
