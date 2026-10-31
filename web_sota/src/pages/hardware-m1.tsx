import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

/**
 * Hardware M1 - Korg M1 (1988) interactive three.js panel.
 * Dimensions from Service Manual Structural Diagram: ~1047 x 340 x 110 mm.
 * Chassis + 61 keys (36 white shown simplified) + 2x40 LCD + Y-matrix buttons.
 * Needs: bun add three @types/three (web_sota dir).
 * No OrbitControls dep - simple drag-to-orbit + wheel zoom.
 */
const INITIAL_MODE = "INT";

export function HardwareM1() {
  const mountRef = useRef<HTMLDivElement>(null);
  const [lcdLine1, setLcdLine1] = useState("KORG M1  MUSIC WORKSTATION");
  const [lcdLine2, setLcdLine2] = useState("INT 00: Universe  I-C00");
  const [selectedMode, setSelectedMode] = useState(INITIAL_MODE);
  const lcdRef = useRef<{ l1: string; l2: string }>({
    l1: lcdLine1,
    l2: lcdLine2,
  });
  lcdRef.current = { l1: lcdLine1, l2: lcdLine2 };

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const W = mount.clientWidth || 900;
    const H = 520;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b0f1a);

    const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
    let theta = 0.6;
    let phi = 1.0;
    let radius = 3.2;
    const updateCam = () => {
      camera.position.set(
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.cos(theta),
      );
      camera.lookAt(0, 0, 0);
    };
    updateCam();

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(W, H);
    mount.appendChild(renderer.domElement);

    // Lights
    scene.add(new THREE.AmbientLight(0x8899bb, 0.7));
    const key = new THREE.DirectionalLight(0xffffff, 1.2);
    key.position.set(2, 4, 3);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0x4466ff, 0.5);
    rim.position.set(-3, 2, -2);
    scene.add(rim);

    const synth = new THREE.Group();
    scene.add(synth);

    // Chassis: 1047mm wide -> 2.4 units
    const chassisMat = new THREE.MeshStandardMaterial({
      color: 0x1a1d24,
      roughness: 0.6,
      metalness: 0.3,
    });
    const chassis = new THREE.Mesh(
      new THREE.BoxGeometry(2.4, 0.22, 0.8),
      chassisMat,
    );
    synth.add(chassis);

    // Top panel strip (control surface)
    const panel = new THREE.Mesh(
      new THREE.BoxGeometry(2.4, 0.02, 0.34),
      new THREE.MeshStandardMaterial({
        color: 0x23262e,
        roughness: 0.5,
        metalness: 0.4,
      }),
    );
    panel.position.set(0, 0.12, -0.22);
    synth.add(panel);

    // LCD: canvas texture, 2x40 chars green-backlit style
    const lcdCanvas = document.createElement("canvas");
    lcdCanvas.width = 512;
    lcdCanvas.height = 96;
    const lcdTex = new THREE.CanvasTexture(lcdCanvas);
    const drawLcd = () => {
      const g = lcdCanvas.getContext("2d");
      if (!g) return;
      g.fillStyle = "#0a2018";
      g.fillRect(0, 0, 512, 96);
      g.fillStyle = "#7dffb0";
      g.font = "20px monospace";
      g.fillText(lcdRef.current.l1.slice(0, 32), 12, 34);
      g.fillText(lcdRef.current.l2.slice(0, 32), 12, 70);
      lcdTex.needsUpdate = true;
    };
    drawLcd();
    const lcd = new THREE.Mesh(
      new THREE.PlaneGeometry(0.62, 0.12),
      new THREE.MeshBasicMaterial({ map: lcdTex }),
    );
    lcd.position.set(-0.55, 0.135, -0.22);
    lcd.rotation.x = -Math.PI / 2 + 0.0;
    // lay flat facing up: rotate plane to horizontal
    lcd.rotation.set(-Math.PI / 2, 0, 0);
    synth.add(lcd);
    const lcdTimer = window.setInterval(drawLcd, 500);

    // Y-matrix buttons: 8 mode keys as small boxes, clickable
    const btnMat = new THREE.MeshStandardMaterial({
      color: 0x39414f,
      roughness: 0.4,
    });
    const btnActive = new THREE.MeshStandardMaterial({
      color: 0x2f7dff,
      roughness: 0.4,
      emissive: 0x1a3faa,
    });
    const modes = [
      "INT",
      "COMBI",
      "PROG",
      "SEQ",
      "GLOBAL",
      "CARD",
      "EDITC",
      "EDITP",
    ];
    const btnMeshes: THREE.Mesh[] = [];
    modes.forEach((m, i) => {
      const b = new THREE.Mesh(
        new THREE.BoxGeometry(0.09, 0.03, 0.06),
        m === INITIAL_MODE ? btnActive : btnMat,
      );
      b.position.set(
        0.05 + (i % 4) * 0.13,
        0.135,
        -0.32 + Math.floor(i / 4) * 0.1,
      );
      b.userData.mode = m;
      synth.add(b);
      btnMeshes.push(b);
    });

    // Keys: 36 white + black pattern (simplified full 61)
    const whiteMat = new THREE.MeshStandardMaterial({
      color: 0xe8e6df,
      roughness: 0.5,
    });
    const blackMat = new THREE.MeshStandardMaterial({
      color: 0x111114,
      roughness: 0.4,
    });
    const keyGroup = new THREE.Group();
    keyGroup.position.set(0, 0.02, 0.22);
    synth.add(keyGroup);
    const whiteCount = 36;
    const ww = 2.3 / whiteCount;
    const pattern = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0]; // C..B black after index?
    let wi = 0;
    for (let n = 0; n < 61; n++) {
      const semis = n % 12;
      const isBlack = [1, 3, 6, 8, 10].includes(semis);
      if (!isBlack) {
        const k = new THREE.Mesh(
          new THREE.BoxGeometry(ww * 0.94, 0.05, 0.32),
          whiteMat,
        );
        k.position.set(-1.15 + wi * ww + ww / 2, 0, 0);
        k.userData.note = n;
        keyGroup.add(k);
        wi++;
      } else {
        const k = new THREE.Mesh(
          new THREE.BoxGeometry(ww * 0.6, 0.07, 0.2),
          blackMat,
        );
        k.position.set(-1.15 + wi * ww, 0.015, -0.06);
        k.userData.note = n;
        keyGroup.add(k);
      }
    }
    void pattern;

    // Interaction: raycast keys + buttons
    const ray = new THREE.Raycaster();
    const ptr = new THREE.Vector2();
    const onClick = (e: MouseEvent) => {
      const r = renderer.domElement.getBoundingClientRect();
      ptr.x = ((e.clientX - r.left) / r.width) * 2 - 1;
      ptr.y = -((e.clientY - r.top) / r.height) * 2 + 1;
      ray.setFromCamera(ptr, camera);
      const hits = ray.intersectObjects([...keyGroup.children, ...btnMeshes]);
      if (hits.length > 0) {
        const o = hits[0].object as THREE.Mesh;
        if (o.userData.mode) {
          const m = o.userData.mode as string;
          setSelectedMode(m);
          btnMeshes.forEach((b) => {
            const mat = b.userData.mode === m ? btnActive : btnMat;
            (b as THREE.Mesh).material = mat;
          });
          lcdRef.current.l1 = `${m} MODE - KORG M1`;
          setLcdLine1(lcdRef.current.l1);
        } else if (typeof o.userData.note === "number") {
          const n = o.userData.note as number;
          // flash key
          const orig = (
            o.material as THREE.MeshStandardMaterial
          ).color.getHex();
          (o.material as THREE.MeshStandardMaterial).color.setHex(0x2f7dff);
          window.setTimeout(
            () => (o.material as THREE.MeshStandardMaterial).color.setHex(orig),
            150,
          );
          lcdRef.current.l2 = `NOTE ${n}  CH1  VEL 100`;
          setLcdLine2(lcdRef.current.l2);
          // TODO: Web MIDI note-on via navigator.requestMIDIAccess -> M1 MIDI IN
        }
      }
    };
    renderer.domElement.addEventListener("click", onClick);

    // drag orbit + wheel zoom
    let dragging = false;
    let px = 0;
    let py = 0;
    const down = (e: MouseEvent) => {
      dragging = true;
      px = e.clientX;
      py = e.clientY;
    };
    const move = (e: MouseEvent) => {
      if (!dragging) return;
      theta -= (e.clientX - px) * 0.005;
      phi = Math.min(1.4, Math.max(0.3, phi - (e.clientY - py) * 0.005));
      px = e.clientX;
      py = e.clientY;
      updateCam();
    };
    const up = () => {
      dragging = false;
    };
    const wheel = (e: WheelEvent) => {
      radius = Math.min(6, Math.max(1.5, radius + e.deltaY * 0.002));
      updateCam();
    };
    renderer.domElement.addEventListener("mousedown", down);
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    renderer.domElement.addEventListener("wheel", wheel);

    const onResize = () => {
      const w = mount.clientWidth || 900;
      renderer.setSize(w, H);
      camera.aspect = w / H;
      camera.updateProjectionMatrix();
    };
    window.addEventListener("resize", onResize);

    let raf = 0;
    const loop = () => {
      raf = requestAnimationFrame(loop);
      renderer.render(scene, camera);
    };
    loop();

    return () => {
      cancelAnimationFrame(raf);
      window.clearInterval(lcdTimer);
      renderer.domElement.removeEventListener("click", onClick);
      renderer.domElement.removeEventListener("mousedown", down);
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
      renderer.domElement.removeEventListener("wheel", wheel);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div className="space-y-4 p-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">
          Korg M1 - Hardware View
        </h1>
        <p className="text-sm text-slate-400">
          three.js panel from Service Manual structural dims. Click mode buttons
          / keys. LCD mirrors HD44780 state. Next: wire Web MIDI SysEx + MAME
          bridge memory view.
        </p>
      </div>
      <div className="flex gap-2 text-xs">
        <span className="rounded border border-slate-700 px-2 py-1 text-slate-300">
          Mode: {selectedMode}
        </span>
        <span className="rounded border border-slate-700 px-2 py-1 text-slate-300">
          LCD: {lcdLine1} | {lcdLine2}
        </span>
      </div>
      <div
        ref={mountRef}
        className="w-full overflow-hidden rounded border border-slate-800"
        style={{ height: 520 }}
      />
      <div className="text-xs text-slate-500">
        Docs: docs/KORG_M1.md | artifacts/korg-m1/*.pdf | MAME driver
        src/mame/korg/korgm1.cpp | ROM map: NVRAM 0x00000, BeeCard 0x50000, IPL
        0xE0000 NEC V50.
      </div>
    </div>
  );
}
