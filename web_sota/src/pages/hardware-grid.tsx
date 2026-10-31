import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

/**
 * Hardware GRiD — GRiDCase 1520 (1985) rugged portable, open clamshell.
 * 286 AT-class, amber gas-plasma display, Micro Switch ST keyboard.
 * Companion to hardware-m1.tsx — same frankendingus Hardware-view pattern:
 * static geometry + live-state LCD/screen hook + input map from rust-mame-mcp
 * (`mame_gridcase1520_profile`). Needs: three (already in web_sota deps).
 */
const BOOT_LINES = [
  "GRiDCase 1520  BIOS  REV 2.1",
  "640K RAM OK   HDD 40MB READY",
  "Starting MS-DOS ...",
  "C:\\>",
];

export function HardwareGrid() {
  const mountRef = useRef<HTMLDivElement>(null);
  const [screenLines, setScreenLines] = useState<string[]>(BOOT_LINES);
  const [lidAngle, setLidAngle] = useState(105);
  const screenRef = useRef<string[]>(BOOT_LINES);
  screenRef.current = screenLines;
  const lidRef = useRef<THREE.Group | null>(null);
  const lidAngleRef = useRef(lidAngle);
  lidAngleRef.current = lidAngle;

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const W = mount.clientWidth || 900;
    const H = 520;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b0f1a);

    const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
    let theta = 0.55;
    let phi = 1.05;
    let radius = 3.4;
    const updateCam = () => {
      camera.position.set(
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.cos(theta),
      );
      camera.lookAt(0, 0.25, 0);
    };
    updateCam();

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(W, H);
    mount.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0x8899bb, 0.6));
    const key = new THREE.DirectionalLight(0xffd9a0, 1.1);
    key.position.set(2, 4, 3);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0xff6600, 0.35);
    rim.position.set(-3, 2, -2);
    scene.add(rim);

    const machine = new THREE.Group();
    scene.add(machine);

    // Magnesium tub: rugged base, dark die-cast finish.
    const tubMat = new THREE.MeshStandardMaterial({
      color: 0x2b2b2e,
      roughness: 0.55,
      metalness: 0.6,
    });
    const base = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.16, 1.5), tubMat);
    base.position.y = 0.08;
    machine.add(base);

    // Keyboard deck: simplified key field.
    const keyMat = new THREE.MeshStandardMaterial({
      color: 0x3a3a3e,
      roughness: 0.5,
    });
    const deck = new THREE.Group();
    deck.position.set(0, 0.17, 0.35);
    machine.add(deck);
    for (let r = 0; r < 5; r++) {
      for (let c = 0; c < 14; c++) {
        const k = new THREE.Mesh(
          new THREE.BoxGeometry(0.12, 0.03, 0.12),
          keyMat,
        );
        k.position.set(-0.91 + c * 0.14, 0, -0.28 + r * 0.14);
        k.userData.key = `R${r}C${c}`;
        deck.add(k);
      }
    }

    // Lid group hinged at the back edge; angle adjustable from the UI.
    const lid = new THREE.Group();
    lid.position.set(0, 0.16, -0.75);
    machine.add(lid);
    const lidSlab = new THREE.Mesh(
      new THREE.BoxGeometry(2.2, 1.15, 0.1),
      tubMat,
    );
    lidSlab.position.set(0, 0.575, 0);
    lid.add(lidSlab);

    // Plasma screen: canvas texture, amber on near-black, subtle flicker.
    const scrCanvas = document.createElement("canvas");
    scrCanvas.width = 640;
    scrCanvas.height = 200;
    const scrTex = new THREE.CanvasTexture(scrCanvas);
    const drawScreen = (flicker: number) => {
      const g = scrCanvas.getContext("2d");
      if (!g) return;
      g.fillStyle = "#0a0500";
      g.fillRect(0, 0, 640, 200);
      g.fillStyle = `rgba(255,${102 + flicker},0,0.95)`;
      g.font = "20px monospace";
      screenRef.current.slice(0, 8).forEach((line, i) => {
        g.fillText(line.slice(0, 52), 16, 32 + i * 22);
      });
      scrTex.needsUpdate = true;
    };
    drawScreen(0);
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(1.7, 0.53),
      new THREE.MeshBasicMaterial({ map: scrTex }),
    );
    screen.position.set(0, 0.575, 0.051);
    lid.add(screen);
    // Orange point glow spilling from the tube.
    const glow = new THREE.PointLight(0xff6600, 0.8, 3.5);
    glow.position.set(0, 0.6, 0.4);
    lid.add(glow);

    // Lid angle from state: 90deg = vertical slab.
    lidRef.current = lid;
    lid.rotation.x =
      THREE.MathUtils.degToRad(-(lidAngleRef.current - 90)) * 0.9;

    // Interaction: click keys -> terminal echo; drag-orbit + wheel zoom.
    const ray = new THREE.Raycaster();
    const ptr = new THREE.Vector2();
    const onClick = (e: MouseEvent) => {
      const r = renderer.domElement.getBoundingClientRect();
      ptr.x = ((e.clientX - r.left) / r.width) * 2 - 1;
      ptr.y = -((e.clientY - r.top) / r.height) * 2 + 1;
      ray.setFromCamera(ptr, camera);
      const hits = ray.intersectObjects(deck.children);
      if (hits.length > 0) {
        const o = hits[0].object as THREE.Mesh;
        const k = (o.userData.key as string) ?? "?";
        const orig = (o.material as THREE.MeshStandardMaterial).color.getHex();
        (o.material as THREE.MeshStandardMaterial).color.setHex(0xff6600);
        window.setTimeout(
          () => (o.material as THREE.MeshStandardMaterial).color.setHex(orig),
          150,
        );
        setScreenLines((prev) => [...prev.slice(-7), `C:\\> key ${k}`]);
        // TODO: picks up `mame_gridcase1520_profile` boot recipe; on a live
        // 86Box oracle this becomes send-input against the 1520 keyboard.
      }
    };
    renderer.domElement.addEventListener("click", onClick);

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
    let tick = 0;
    const loop = () => {
      raf = requestAnimationFrame(loop);
      tick++;
      if (tick % 20 === 0) drawScreen(Math.floor(Math.random() * 14) - 7);
      renderer.render(scene, camera);
    };
    loop();

    return () => {
      cancelAnimationFrame(raf);
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

  useEffect(() => {
    if (lidRef.current) {
      lidRef.current.rotation.x =
        THREE.MathUtils.degToRad(-(lidAngle - 90)) * 0.9;
    }
  }, [lidAngle]);

  return (
    <div className="space-y-4 p-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">
          GRiDCase 1520 — Hardware View
        </h1>
        <p className="text-sm text-slate-400">
          Rugged 286 portable, open clamshell, amber plasma. Click keys to echo
          to the glass. Profile:{" "}
          <span className="font-mono">mame_gridcase1520_profile</span> — second
          exemplar of the frankendingus Hardware-view pattern (see M1 Synth
          page). Boot recipe + model facts live in rust-mame-mcp.
        </p>
      </div>
      <div className="flex gap-2 text-xs">
        <label className="rounded border border-slate-700 px-2 py-1 text-slate-300">
          Lid angle{" "}
          <input
            type="range"
            min={80}
            max={120}
            value={lidAngle}
            onChange={(e) => setLidAngle(Number(e.target.value))}
            className="ml-2 align-middle"
          />{" "}
          {lidAngle}°
        </label>
        <span className="rounded border border-slate-700 px-2 py-1 text-slate-300">
          80286 @ 10 MHz · MS-DOS · plasma
        </span>
      </div>
      <div
        ref={mountRef}
        className="w-full overflow-hidden rounded border border-slate-800"
        style={{ height: 520 }}
      />
      <div className="text-xs text-slate-500">
        Docs: docs/GRID_REVIVE.md · profile via rust-mame-mcp · next: 86Box
        oracle link for live key send.
      </div>
    </div>
  );
}
