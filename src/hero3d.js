import {
  WebGLRenderer, Scene, PerspectiveCamera, HemisphereLight, DirectionalLight, BoxGeometry,
  MeshStandardMaterial, InstancedMesh, Object3D, Color, Group,
} from 'three';
import { barHeight, isUp } from './terrain.js';

// Candlestick-bar terrain: one instanced mesh (a single draw call), slow rotation, light mouse tilt.
export function startHero(container, { still = false } = {}) {
  const small = innerWidth < 760;
  const cols = small ? 18 : 28, rows = small ? 9 : 14;

  const renderer = new WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  container.appendChild(renderer.domElement);

  const scene = new Scene();
  const camera = new PerspectiveCamera(32, 1, 0.1, 100);
  camera.position.set(0, 15, 33);
  camera.lookAt(0, 0.6, 0);
  scene.add(new HemisphereLight(0xdfe7f2, 0x0d1625, 1.4));
  const sun = new DirectionalLight(0xffffff, 2.2);
  sun.position.set(6, 12, 8);
  scene.add(sun);

  const geo = new BoxGeometry(0.72, 1, 0.72).translate(0, 0.5, 0); // grows upward when scaled
  const mesh = new InstancedMesh(geo, new MeshStandardMaterial({ roughness: 0.5, metalness: 0.35 }), cols * rows);
  const group = new Group();
  group.add(mesh);
  scene.add(group);

  const up = new Color(0xc98243), down = new Color(0x66768c), dummy = new Object3D();
  function layout(t) {
    let k = 0;
    for (let j = 0; j < rows; j++)
      for (let i = 0; i < cols; i++, k++) {
        dummy.position.set(i - cols / 2 + 0.5, 0, j - rows / 2 + 0.5);
        dummy.scale.set(1, barHeight(i, j, cols, rows, t) * 1.15, 1);
        dummy.updateMatrix();
        mesh.setMatrixAt(k, dummy.matrix);
        mesh.setColorAt(k, isUp(i, j, cols, rows, t) ? up : down);
      }
    mesh.instanceMatrix.needsUpdate = true;
    mesh.instanceColor.needsUpdate = true;
  }

  const mouse = { x: 0, y: 0 };
  addEventListener('pointermove', (e) => {
    mouse.x = e.clientX / innerWidth - 0.5;
    mouse.y = e.clientY / innerHeight - 0.5;
  }, { passive: true });

  function resize() {
    const { clientWidth: w, clientHeight: h } = container;
    renderer.setSize(w, h, false);
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    if (still) draw(0);
  }

  let rotX = 0, rotY = -0.5;
  function draw(time) {
    const t = time / 1000;
    if (!still) {
      layout(t * 0.25);
      rotY += (-0.5 + Math.sin(t * 0.08) * 0.35 + mouse.x * 0.35 - rotY) * 0.04;
      rotX += (mouse.y * 0.12 - rotX) * 0.04;
    }
    group.rotation.set(rotX, rotY, 0);
    renderer.render(scene, camera);
  }

  layout(0);
  new ResizeObserver(resize).observe(container);
  resize();
  if (still) return;

  // Only animate while the hero is on screen and the tab is visible.
  let visible = true;
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(container);
  renderer.setAnimationLoop((time) => { if (visible && !document.hidden) draw(time); });
}
