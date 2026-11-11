// Turns content/site.json into static HTML at build time (see vite.config.js).
import { barHeight, isUp } from './terrain.js';

const esc = (s = '') =>
  String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

// Escapes text and highlights [TODO: ...] placeholders so they are impossible to miss.
const t = (s) => esc(s).replace(/\[TODO:([^\]]*)\]/g, '<mark class="todo">TODO:$1</mark>');
const isTodo = (s = '') => s.startsWith('[TODO');

const link = ({ label, url }) =>
  isTodo(url)
    ? `<span class="link-todo">${esc(label)}: ${t(url)}</span>`
    : `<a class="text-link" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)} <span aria-hidden="true">↗</span></a>`;

const icon = {
  mail: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M3 6h18v12H3z M3 6l9 7 9-7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
  in: '<svg aria-hidden="true" viewBox="0 0 24 24"><path fill="currentColor" d="M4 9h3.5v11H4zM5.75 3.5a2 2 0 110 4 2 2 0 010-4zM10 9h3.3v1.6c.5-.9 1.7-1.9 3.5-1.9 3.7 0 4.2 2.4 4.2 5.5V20h-3.5v-5.1c0-1.3 0-2.9-1.8-2.9s-2.1 1.4-2.1 2.8V20H10z"/></svg>',
  gh: '<svg aria-hidden="true" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2a10 10 0 00-3.2 19.5c.5.1.7-.2.7-.5v-1.7c-2.8.6-3.4-1.3-3.4-1.3-.4-1.2-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.6 2.4 1.1 3 .8.1-.7.4-1.1.6-1.3-2.2-.3-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.3-.4-1.3.1-2.7 0 0 .8-.3 2.7 1a9.4 9.4 0 015 0c1.9-1.3 2.7-1 2.7-1 .5 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.7 0 3.9-2.4 4.7-4.6 5 .4.3.7.9.7 1.9V21c0 .3.2.6.7.5A10 10 0 0012 2z"/></svg>',
  dl: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 4v11m0 0l-4.5-4.5M12 15l4.5-4.5M5 19h14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
};

function contactLinks(p) {
  return [
    `<a class="btn btn-primary" href="${esc(p.cv)}" download>${icon.dl}Download CV</a>`,
    `<a class="btn" href="mailto:${esc(p.email)}">${icon.mail}<span>${esc(p.email)}</span></a>`,
    `<a class="btn" href="${esc(p.linkedin)}" target="_blank" rel="noopener">${icon.in}LinkedIn</a>`,
    p.github ? `<a class="btn" href="${esc(p.github)}" target="_blank" rel="noopener">${icon.gh}GitHub</a>` : '',
  ].join('');
}

// Isometric bar terrain drawn as SVG: the no-WebGL / reduced-power version of the hero.
export function terrainSvg(cols = 14, rows = 7) {
  const w = 22, h = 11, k = 34; // tile half-width, half-height, height scale
  const ox = rows * w + 10, oy = 120;
  const r = (n) => Math.round(n * 10) / 10;
  const cells = [];
  for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) cells.push([i, j]);
  cells.sort((a, b) => a[0] + a[1] - (b[0] + b[1]));
  const polys = cells.map(([i, j]) => {
    const x = ox + (i - j) * w, y = oy + (i + j) * h, H = barHeight(i, j, cols, rows) * k;
    const up = isUp(i, j, cols, rows) ? 'u' : 'd';
    const top = `${r(x)},${r(y - H - h)} ${r(x + w * 0.8)},${r(y - H)} ${r(x)},${r(y - H + h)} ${r(x - w * 0.8)},${r(y - H)}`;
    const left = `${r(x - w * 0.8)},${r(y - H)} ${r(x)},${r(y - H + h)} ${r(x)},${r(y + h)} ${r(x - w * 0.8)},${r(y)}`;
    const right = `${r(x + w * 0.8)},${r(y - H)} ${r(x)},${r(y - H + h)} ${r(x)},${r(y + h)} ${r(x + w * 0.8)},${r(y)}`;
    return `<polygon class="${up}t" points="${top}"/><polygon class="${up}l" points="${left}"/><polygon class="${up}r" points="${right}"/>`;
  });
  const vw = (cols + rows) * w + 20, vh = oy + (cols + rows) * h + 20;
  return `<svg class="terrain-svg" viewBox="0 0 ${vw} ${vh}" role="img" aria-label="Stylised 3D bar chart resembling a rising price surface">${polys.join('')}</svg>`;
}

function caseRows(rows) {
  return `<dl class="case">${rows
    .filter(([, v]) => v)
    .map(([k, v]) => `<div><dt>${k}</dt><dd>${t(v)}</dd></div>`)
    .join('')}</dl>`;
}

export function renderBody(c) {
  const p = c.person;
  const featured = c.featured
    .map(
      (f) => `
      <article class="card tilt">
        <p class="eyebrow">${t(f.tag)}${f.status ? ` <span class="pill">${esc(f.status)}</span>` : ''}</p>
        <h3>${t(f.title)}</h3>
        ${f.metrics.length ? `<ul class="metrics">${f.metrics.map((m) => `<li><strong>${t(m.value)}</strong><span>${t(m.label)}</span></li>`).join('')}</ul>` : ''}
        ${caseRows([['Problem', f.problem], ['Data', f.data], ['Method', f.method], ['Result', f.result], ['My role', f.role]])}
        <ul class="tags" aria-label="Tools">${f.tools.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>
        <p class="links">${f.links.map(link).join('')}</p>
      </article>`
    )
    .join('');

  const more = c.more
    .map(
      (m) => `
      <article class="card">
        <p class="eyebrow">${t(m.tag)}</p>
        <h3>${t(m.title)}</h3>
        ${caseRows([['Problem', m.problem], ['Data', m.data], ['Approach', m.approach], ['Result', m.result], ['My role', m.role]])}
        ${m.links.length ? `<p class="links">${m.links.map(link).join('')}</p>` : ''}
      </article>`
    )
    .join('');

  return `
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <nav class="wrap nav" aria-label="Main">
    <a class="brand" href="#top"><span class="mono" aria-hidden="true">${esc(p.initials)}</span>${esc(p.name)}</a>
    <ul>
      <li><a href="#about">About</a></li>
      <li><a href="#projects">Projects</a></li>
      <li><a href="#demo">Demo</a></li>
      <li><a href="#skills">Skills</a></li>
      <li><a href="#contact">Contact</a></li>
    </ul>
  </nav>
</header>

<main id="main">
  <section class="hero" id="top" aria-labelledby="hero-title">
    <div class="hero-visual" aria-hidden="true">
      <div class="hero-fallback">${terrainSvg()}</div>
      <div class="hero-canvas"></div>
    </div>
    <div class="wrap hero-text">
      <p class="eyebrow">${esc(p.location)}</p>
      <h1 id="hero-title">${esc(p.name)} <span class="local" lang="vi">${esc(p.nameLocal)}</span></h1>
      <p class="positioning">${t(p.positioning)}</p>
      <div class="actions">${contactLinks(p)}</div>
    </div>
  </section>

  <section id="about" class="wrap section" aria-labelledby="about-title">
    <h2 id="about-title">About</h2>
    <div class="about">${c.about.map((s) => `<p>${t(s)}</p>`).join('')}</div>
  </section>

  <section id="experience" class="wrap section" aria-labelledby="exp-title">
    <h2 id="exp-title">Experience</h2>
    <div class="timeline">${c.experience
      .map(
        (e) => `
      <article class="job">
        <div class="job-head"><h3>${t(e.role)}, ${t(e.org)}</h3><p class="muted">${t(e.place)} · ${t(e.dates)}</p></div>
        <ul>${e.bullets.map((b) => `<li>${t(b)}</li>`).join('')}</ul>
      </article>`
      )
      .join('')}</div>
  </section>

  <section id="projects" class="wrap section" aria-labelledby="proj-title">
    <h2 id="proj-title">Featured projects</h2>
    <p class="lead muted">Finance and data case studies: problem, data, method, result, tools.</p>
    <div class="grid grid-2">${featured}</div>
    <h2 class="sub">More projects</h2>
    <div class="grid">${more}</div>
  </section>

  <section id="demo" class="wrap section" aria-labelledby="demo-title">
    <h2 id="demo-title">Try it: build a portfolio</h2>
    <p class="lead muted">Move the weights. Expected return, volatility and the Sharpe ratio update live; the chart shows where your mix sits against the efficient frontier.</p>
    <div class="demo card" id="demo-root">
      <noscript><p>This interactive demo needs JavaScript.</p></noscript>
    </div>
    <p class="note">${t(c.demo.note)}</p>
  </section>

  <section id="skills" class="wrap section" aria-labelledby="skills-title">
    <h2 id="skills-title">Skills</h2>
    <div class="skills">${c.skills
      .map((g) => `<div class="skill-group"><h3>${esc(g.level)}</h3><ul class="tags">${g.items.map((x) => `<li>${t(x)}</li>`).join('')}</ul></div>`)
      .join('')}</div>
    <h3 class="sub3">Certificates</h3>
    <ul class="certs">${c.certificates
      .map((x) => `<li><strong>${t(x.name)}</strong><span>${t(x.issuer)}${x.date ? ` · ${t(x.date)}` : ''}</span></li>`)
      .join('')}</ul>
    <p class="muted"><strong>Languages:</strong> ${t(c.languages)}</p>
  </section>

  <section id="education" class="wrap section" aria-labelledby="edu-title">
    <h2 id="edu-title">Education</h2>
    <div class="edu">${c.education
      .map(
        (e) => `
      <article><h3>${t(e.degree)}</h3><p class="muted">${t(e.school)} · ${t(e.dates)}</p>${e.details.map((d) => `<p>${t(d)}</p>`).join('')}</article>`
      )
      .join('')}</div>
  </section>

  <section id="beyond" class="wrap section" aria-labelledby="beyond-title">
    <h2 id="beyond-title">Beyond the classroom</h2>
    <ul class="beyond">${c.beyond.map((b) => `<li>${t(b)}</li>`).join('')}</ul>
  </section>

  <section id="contact" class="wrap section contact" aria-labelledby="contact-title">
    <h2 id="contact-title">Contact</h2>
    <p class="lead">Open to finance and analytics roles. The fastest way to reach me is email.</p>
    <div class="actions">${contactLinks(p)}</div>
  </section>
</main>

<footer class="wrap footer"><p class="muted">© ${new Date().getFullYear()} ${esc(p.name)}</p></footer>
<script type="application/json" id="demo-data">${JSON.stringify(c.demo).replace(/</g, '\\u003c')}</script>`;
}

export function renderHead(c) {
  const m = c.meta;
  const img = `${m.url.replace(/\/$/, '')}/${m.ogImage}`;
  return `
<title>${esc(m.title)}</title>
<meta name="description" content="${esc(m.description)}">
<link rel="canonical" href="${esc(m.url)}">
<meta property="og:type" content="website">
<meta property="og:title" content="${esc(m.title)}">
<meta property="og:description" content="${esc(m.description)}">
<meta property="og:url" content="${esc(m.url)}">
<meta property="og:image" content="${esc(img)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="${esc(c.person.name)}: ${esc(c.person.positioning)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(m.title)}">
<meta name="twitter:description" content="${esc(m.description)}">
<meta name="twitter:image" content="${esc(img)}">`;
}
