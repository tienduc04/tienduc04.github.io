import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import { renderBody, renderHead } from './src/render.js';

const contentFile = fileURLToPath(new URL('./content/site.json', import.meta.url));

// Renders content/site.json into index.html, so the page is plain HTML before any JavaScript runs.
const contentPlugin = {
  name: 'site-content',
  transformIndexHtml(html) {
    const content = JSON.parse(readFileSync(contentFile, 'utf8'));
    return html.replace('<!--head-->', renderHead(content)).replace('<!--app-->', renderBody(content));
  },
  configureServer(server) {
    server.watcher.add(contentFile);
    server.watcher.on('change', (f) => resolve(f) === contentFile && server.ws.send({ type: 'full-reload' }));
  },
};

export default defineConfig({ base: './', plugins: [contentPlugin] });
