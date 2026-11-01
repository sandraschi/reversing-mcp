import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import {
  Cpu,
  HardDrive,
  Monitor,
  Shield,
  Sun,
  Terminal,
  BookOpen,
  Radio,
  CheckCircle2,
  AlertTriangle,
  Maximize2,
  Minimize2,
} from "lucide-react";

/**
 * Hardware GRiD — GRiDCase 1520 (1985) rugged portable, open clamshell.
 * 286 AT-class, amber gas-plasma display, Micro Switch ST keyboard.
 * Companion to hardware-m1.tsx — frankendingus Hardware-view pattern:
 * static geometry + live-state LCD/screen hook + input map from rust-mame-mcp
 * (`mame_gridcase1520_profile`).
 */
const BOOT_LINES = [
  "GRiDCase 1520  BIOS  REV 2.1",
  "640K RAM OK   HDD 40MB READY",
  "Starting MS-DOS 3.3 ...",
  "C:\\> VER",
  "MS-DOS Version 3.30 (GRiD-OEM)",
  "C:\\> _",
];

type DisplayMode = "plasma" | "lcd";

export function HardwareGrid() {
  const mountRef = useRef<HTMLDivElement>(null);
  const [screenLines, setScreenLines] = useState<string[]>(BOOT_LINES);
  const [lidAngle, setLidAngle] = useState(105);
  const [spotlightIntensity, setSpotlightIntensity] = useState(5.5);
  const [ambientIntensity, setAmbientIntensity] = useState(1.4);
  const [displayMode, setDisplayMode] = useState<DisplayMode>("plasma");
  const [commandInput, setCommandInput] = useState("");
  const [activeTab, setActiveTab] = useState<"specs" | "revive" | "history">("specs");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const stageContainerRef = useRef<HTMLDivElement>(null);

  const screenRef = useRef<string[]>(BOOT_LINES);
  screenRef.current = screenLines;
  const currentPromptRef = useRef<string>("");

  const toggleFullscreen = () => {
    if (!stageContainerRef.current) return;
    if (!document.fullscreenElement) {
      stageContainerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  useEffect(() => {
    const onFsChange = () => setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  const runCommandDirect = (cmdText: string) => {
    const cmd = cmdText.trim().toUpperCase();
    const newLines = [...screenRef.current];
    if (newLines[newLines.length - 1]?.startsWith("C:\\> ")) {
      newLines[newLines.length - 1] = `C:\\> ${cmdText}`;
    } else {
      newLines.push(`C:\\> ${cmdText}`);
    }

    if (cmd === "DIR") {
      newLines.push(
        "COMMAND  COM    25307  03-18-87",
        "FW       EXE   198420  09-12-86",
        "FRED     LIB    48210  09-12-86",
        "POWERPLT FW     64120  11-04-87",
        "KERMIT   EXE    89420  11-04-86",
        "GRIDUTIL EXE    41290  08-20-87",
        "6 File(s)   38,124,800 bytes free",
      );
    } else if (cmd === "FW" || cmd === "FRAMEWORK" || cmd === "POWERPLT" || cmd === "RUN POWERPLT") {
      newLines.push(
        "--- Ashton-Tate Framework II (v1.10) ---",
        "Apps  Disk  Create  Edit  Locate  Frames  Words  Numbers  Print",
        "┌─[ KRAFTWERK-WIEN: TURBINEN & TELEMETRIE ]─────────────────────────┐",
        "│ BLOCK  SOLL_MW  IST_MW   TEMP_C  DRUCK_BAR  STATUS                │",
        "│ T1      240.0   238.4    542°C    164.2     NOMINAL               │",
        "│ T2      240.0   241.1    538°C    165.0     NOMINAL               │",
        "│ G3      120.0   119.8    495°C    120.5     NETZEINSPEISUNG       │",
        "└───────────────────────────────────────────────────────────────────┘",
        "┌─[ ENERGIE-TAGESBILANZ (Spreadsheet) ]─────────────────────────────┐",
        "│ ZEIT   ERZEUGUNG_MWH  VERBRAUCH_MWH  NETZ-SALDO   FRED-FORMEL    │",
        "│ 08:00     598.2           540.0        +58.2      @SUM(B1:B3)    │",
        "│ 09:00     612.4           585.1        +27.3      @DELTA(SALDO)  │",
        "└───────────────────────────────────────────────────────────────────┘",
        "[FRED]: @SUM(Turbinen.IST_MW) -> 599.3 MW NOMINAL (15 Jahre Betrieb)",
        "Framework running. Type 'EXIT' or 'DOS' to exit to prompt.",
      );
    } else if (cmd === "EXIT" || cmd === "QUIT" || cmd === "DOS") {
      newLines.push("Exiting Framework II ...", "Back to MS-DOS.");
    } else if (cmd.startsWith("@") || cmd.startsWith("FRED")) {
      newLines.push(
        `[FRED Eval]: ${cmd}`,
        `Result: OK. Formula compiled into active Frame. Calculated: 599.3 MW`,
      );
    } else if (cmd === "VER") {
      newLines.push("MS-DOS Version 3.30 (GRiD-OEM 1520)");
    } else if (cmd === "MEM") {
      newLines.push(
        "  655360 bytes total conventional memory",
        "  589824 bytes available to MS-DOS",
        " 1048576 bytes total EMS/XMS RAM",
      );
    } else if (cmd === "HELP") {
      newLines.push("Supported: DIR, FW (Framework II), POWERPLT, VER, MEM, KERMIT, CLS");
    } else if (cmd === "CLS") {
      setScreenLines(["C:\\> _"]);
      currentPromptRef.current = "";
      return;
    } else if (cmd === "REVIVE" || cmd === "KERMIT") {
      newLines.push(
        "KERMIT-MS v2.29 Connecting COM1 19200 8-N-1...",
        "Carrier detected. Pi 5 implant connected.",
      );
    } else if (cmd) {
      newLines.push(`Bad command or file name: ${cmd}`);
    }

    newLines.push("C:\\> _");
    setScreenLines(newLines.slice(-12));
    currentPromptRef.current = "";
  };

  // PC Keyboard capture for real hardware typing
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        runCommandDirect(currentPromptRef.current);
      } else if (e.key === "Backspace") {
        e.preventDefault();
        currentPromptRef.current = currentPromptRef.current.slice(0, -1);
        setScreenLines((old) => {
          const copy = [...old];
          copy[copy.length - 1] = `C:\\> ${currentPromptRef.current}_`;
          return copy;
        });
      } else if (e.key === "Escape") {
        e.preventDefault();
        currentPromptRef.current = "";
        setScreenLines((old) => {
          const copy = [...old];
          copy[copy.length - 1] = "C:\\> _";
          return copy;
        });
      } else if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
        e.preventDefault();
        currentPromptRef.current += e.key.toUpperCase();
        setScreenLines((old) => {
          const copy = [...old];
          copy[copy.length - 1] = `C:\\> ${currentPromptRef.current}_`;
          return copy;
        });
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
  const displayModeRef = useRef<DisplayMode>("plasma");
  displayModeRef.current = displayMode;
  const lidRef = useRef<THREE.Group | null>(null);
  const lidAngleRef = useRef(lidAngle);
  lidAngleRef.current = lidAngle;

  const spotLightRef = useRef<THREE.SpotLight | null>(null);
  const fillSpotRef = useRef<THREE.SpotLight | null>(null);
  const ambientLightRef = useRef<THREE.AmbientLight | null>(null);
  const setCamViewRef = useRef<((t: number, p: number, r: number) => void) | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const W = mount.clientWidth || 900;
    const H = 540;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f172a); // Rich slate-900 studio backdrop

    const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
    let theta = 0.55;
    let phi = 1.05;
    let radius = 3.3;

    const updateCam = () => {
      camera.position.set(
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.cos(theta),
      );
      camera.lookAt(0, 0.25, 0);
    };
    updateCam();

    setCamViewRef.current = (t: number, p: number, r: number) => {
      theta = t;
      phi = p;
      radius = r;
      updateCam();
    };

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    mount.appendChild(renderer.domElement);

    // Studio ground grid
    const gridHelper = new THREE.GridHelper(10, 24, 0xf59e0b, 0x1e293b);
    gridHelper.position.y = -0.005;
    scene.add(gridHelper);

    // Shadow ground plane
    const groundGeo = new THREE.PlaneGeometry(12, 12);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      roughness: 0.9,
      metalness: 0.1,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.01;
    ground.receiveShadow = true;
    scene.add(ground);

    // Primary Ambient Light (Bright and even)
    const ambient = new THREE.AmbientLight(0xd4e2f5, ambientIntensity);
    ambientLightRef.current = ambient;
    scene.add(ambient);

    // Dedicated Top-Front Key Spotlight (The requested studio spotlight!)
    const spot = new THREE.SpotLight(0xfff6ea, spotlightIntensity);
    spot.position.set(1.2, 5.2, 3.4);
    spot.angle = Math.PI / 3.8;
    spot.penumbra = 0.45;
    spot.decay = 1.2;
    spot.distance = 25;
    spot.castShadow = true;
    spot.shadow.mapSize.width = 1024;
    spot.shadow.mapSize.height = 1024;
    spot.shadow.camera.near = 0.5;
    spot.shadow.camera.far = 25;
    spotLightRef.current = spot;

    // Fill Spotlight from high left to illuminate clamshell interior & keyboard
    const fillSpot = new THREE.SpotLight(0xffeedd, spotlightIntensity * 0.55);
    fillSpot.position.set(-2.8, 4.4, 2.2);
    fillSpot.angle = Math.PI / 3.2;
    fillSpot.penumbra = 0.6;
    fillSpot.decay = 1.2;
    fillSpot.distance = 20;
    fillSpotRef.current = fillSpot;

    // Directional Key & Rim Lights
    const dirKey = new THREE.DirectionalLight(0xfff8ee, 1.8);
    dirKey.position.set(2.5, 4.5, 3.5);
    scene.add(dirKey);

    const dirFill = new THREE.DirectionalLight(0x94b4dd, 1.0);
    dirFill.position.set(-3.5, 3.0, 1.5);
    scene.add(dirFill);

    const dirRim = new THREE.DirectionalLight(0xff9944, 0.75);
    dirRim.position.set(0, 2.8, -3.8);
    scene.add(dirRim);

    const machine = new THREE.Group();
    scene.add(machine);

    spot.target = machine;
    fillSpot.target = machine;
    scene.add(spot);
    scene.add(spot.target);
    scene.add(fillSpot);
    scene.add(fillSpot.target);

    // --- REALISTIC DIE-CAST MAGNESIUM CHASSIS (AZ91D ALLOY) ---
    // Service specs: ~292 W x 381 D x 58 H mm (Wedge profile tapering towards front)
    const tubMat = new THREE.MeshStandardMaterial({
      color: 0x363940, // Authentic matte dark-anthracite cast magnesium
      roughness: 0.50,
      metalness: 0.36,
    });
    const tubAccentMat = new THREE.MeshStandardMaterial({
      color: 0x27292f, // Darker recessed perimeter bevels
      roughness: 0.60,
      metalness: 0.25,
    });
    const rubberMat = new THREE.MeshStandardMaterial({
      color: 0x141518, // Neoprene shock-absorber rubber feet & bumpers
      roughness: 0.88,
      metalness: 0.05,
    });
    const metalPortMat = new THREE.MeshStandardMaterial({
      color: 0xc4c8d0, // Machined tin / nickel D-sub connectors & screws
      roughness: 0.28,
      metalness: 0.82,
    });
    const goldMat = new THREE.MeshStandardMaterial({
      color: 0xd4af37, // Gold-plated edge connectors
      roughness: 0.25,
      metalness: 0.90,
    });

    // 1. Lower Tub Chassis with Tapered Rake
    // Main lower belly
    const lowerBelly = new THREE.Mesh(new THREE.BoxGeometry(2.18, 0.07, 1.48), tubAccentMat);
    lowerBelly.position.set(0, 0.035, 0);
    lowerBelly.castShadow = true;
    lowerBelly.receiveShadow = true;
    machine.add(lowerBelly);

    // Upper wedge deck (thicker towards the rear battery compartment)
    const upperDeck = new THREE.Mesh(new THREE.BoxGeometry(2.20, 0.09, 1.50), tubMat);
    upperDeck.position.set(0, 0.105, 0);
    upperDeck.castShadow = true;
    upperDeck.receiveShadow = true;
    machine.add(upperDeck);

    // Front palm-rest bevel (ergonomic wrist rake)
    const palmRest = new THREE.Mesh(new THREE.BoxGeometry(2.18, 0.02, 0.26), tubMat);
    palmRest.position.set(0, 0.155, 0.62);
    palmRest.receiveShadow = true;
    machine.add(palmRest);

    // Four rugged bottom neoprene shock feet
    const footGeo = new THREE.CylinderGeometry(0.045, 0.045, 0.025, 16);
    const footPositions = [
      [-0.95, 0.01, -0.62],
      [0.95, 0.01, -0.62],
      [-0.95, 0.01, 0.62],
      [0.95, 0.01, 0.62],
    ];
    footPositions.forEach(([fx, fy, fz]) => {
      const foot = new THREE.Mesh(footGeo, rubberMat);
      foot.position.set(fx, fy, fz);
      machine.add(foot);
    });

    // Dual front mechanical slide latches (spring-loaded lid lock)
    const latchTrack = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.035, 0.03), tubAccentMat);
    latchTrack.position.set(0, 0.11, 0.76);
    machine.add(latchTrack);

    const latchSliderLeft = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.045, 0.04), rubberMat);
    latchSliderLeft.position.set(-0.16, 0.11, 0.765);
    machine.add(latchSliderLeft);

    const latchSliderRight = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.045, 0.04), rubberMat);
    latchSliderRight.position.set(0.16, 0.11, 0.765);
    machine.add(latchSliderRight);

    // --- LEFT FLANK: EXHAUST COOLING LOUVERS & POWER SWITCH ---
    for (let ventIdx = 0; ventIdx < 7; ventIdx++) {
      const ventSlat = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.012, 0.28), tubAccentMat);
      ventSlat.position.set(-1.105, 0.08 + ventIdx * 0.016, -0.35);
      machine.add(ventSlat);
    }
    // Rocker Power Switch [ | / O ]
    const switchBezel = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.04, 0.06), rubberMat);
    switchBezel.position.set(-1.105, 0.10, -0.10);
    machine.add(switchBezel);
    const rockerSwitch = new THREE.Mesh(
      new THREE.BoxGeometry(0.025, 0.025, 0.04),
      new THREE.MeshStandardMaterial({ color: 0xb91c1c, roughness: 0.4 }), // Red safety rocker
    );
    rockerSwitch.position.set(-1.11, 0.10, -0.10);
    machine.add(rockerSwitch);

    // --- RIGHT FLANK: 3.5" CITIZEN FLOPPY & CONNER 40MB HDD ACCESS ---
    // 3.5" Floppy Drive Bezel
    const fddBezel = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.065, 0.38), tubAccentMat);
    fddBezel.position.set(1.105, 0.095, -0.15);
    machine.add(fddBezel);

    // Floppy disk slot flap
    const fddSlot = new THREE.Mesh(
      new THREE.BoxGeometry(0.015, 0.012, 0.32),
      new THREE.MeshStandardMaterial({ color: 0x0a0b0d, roughness: 0.9 }),
    );
    fddSlot.position.set(1.112, 0.105, -0.15);
    machine.add(fddSlot);

    // Floppy eject push button
    const fddEject = new THREE.Mesh(new THREE.BoxGeometry(0.025, 0.018, 0.05), tubMat);
    fddEject.position.set(1.112, 0.08, -0.28);
    machine.add(fddEject);

    // Floppy green activity LED
    const fddLed = new THREE.Mesh(
      new THREE.SphereGeometry(0.008, 8, 8),
      new THREE.MeshStandardMaterial({ color: 0x10b981, emissive: 0x059669, emissiveIntensity: 0.6 }),
    );
    fddLed.position.set(1.112, 0.08, -0.02);
    machine.add(fddLed);

    // --- REAR I/O CONNECTOR BULKHEAD ---
    // Cast metal back plate
    const rearPlate = new THREE.Mesh(new THREE.BoxGeometry(1.85, 0.08, 0.02), tubAccentMat);
    rearPlate.position.set(0, 0.085, -0.755);
    machine.add(rearPlate);

    // DB-25 RS-232 Serial Port (Metal D-sub with screw jacks)
    const serialPort = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.038, 0.03), metalPortMat);
    serialPort.position.set(-0.55, 0.085, -0.765);
    machine.add(serialPort);

    // Centronics Parallel Printer Port (36-pin)
    const parallelPort = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.038, 0.03), metalPortMat);
    parallelPort.position.set(-0.15, 0.085, -0.765);
    machine.add(parallelPort);

    // 9-pin CGA External Video Port
    const videoPort = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.038, 0.03), metalPortMat);
    videoPort.position.set(0.22, 0.085, -0.765);
    machine.add(videoPort);

    // 19V DC Power Coaxial Barrel Socket
    const dcJack = new THREE.Mesh(
      new THREE.CylinderGeometry(0.02, 0.02, 0.03, 16),
      new THREE.MeshStandardMaterial({ color: 0x111317, roughness: 0.6 }),
    );
    dcJack.rotation.x = Math.PI / 2;
    dcJack.position.set(0.48, 0.085, -0.765);
    machine.add(dcJack);

    // Heavy-duty knurled brass grounding post
    const groundStud = new THREE.Mesh(
      new THREE.CylinderGeometry(0.015, 0.015, 0.035, 12),
      new THREE.MeshStandardMaterial({ color: 0xb45309, metalness: 0.9, roughness: 0.2 }),
    );
    groundStud.rotation.x = Math.PI / 2;
    groundStud.position.set(0.65, 0.085, -0.765);
    machine.add(groundStud);

    // --- DUAL TOP GRiDROM CARTRIDGE SLOTS ---
    // Located on top deck behind keyboard
    const romBayRecess = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.02, 0.22), tubAccentMat);
    romBayRecess.position.set(0, 0.155, -0.42);
    romBayRecess.receiveShadow = true;
    machine.add(romBayRecess);

    // Slot A & Slot B receptacles
    [-0.24, 0.24].forEach((rx, idx) => {
      const romSlot = new THREE.Mesh(
        new THREE.BoxGeometry(0.34, 0.025, 0.14),
        new THREE.MeshStandardMaterial({ color: 0x14161a, roughness: 0.8 }),
      );
      romSlot.position.set(rx, 0.158, -0.42);
      machine.add(romSlot);

      // Gold-plated edge connector pins inside
      const romPins = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.008, 0.03), goldMat);
      romPins.position.set(rx, 0.165, -0.42);
      machine.add(romPins);

      // Cartridge slot label plate
      const labelCanvas = document.createElement("canvas");
      labelCanvas.width = 256;
      labelCanvas.height = 64;
      const lg = labelCanvas.getContext("2d");
      if (lg) {
        lg.fillStyle = "#27292f";
        lg.fillRect(0, 0, 256, 64);
        lg.fillStyle = "#e2e8f0";
        lg.font = "bold 28px sans-serif";
        lg.fillText(`GRiDROM ${idx === 0 ? "A" : "B"}`, 24, 44);
      }
      const labelTex = new THREE.CanvasTexture(labelCanvas);
      const labelMesh = new THREE.Mesh(
        new THREE.PlaneGeometry(0.22, 0.045),
        new THREE.MeshStandardMaterial({ map: labelTex, roughness: 0.5 }),
      );
      labelMesh.rotation.x = -Math.PI / 2;
      labelMesh.position.set(rx, 0.168, -0.32);
      machine.add(labelMesh);
    });

    // GRiDCase 1520 Identification Plate between ROM slots and hinge
    const idCanvas = document.createElement("canvas");
    idCanvas.width = 512;
    idCanvas.height = 128;
    const idG = idCanvas.getContext("2d");
    if (idG) {
      idG.fillStyle = "#1e2025";
      idG.fillRect(0, 0, 512, 128);
      idG.fillStyle = "#f8fafc";
      idG.font = "bold 56px sans-serif";
      idG.fillText("GRiD", 24, 76);
      idG.font = "bold 34px sans-serif";
      idG.fillStyle = "#d97706";
      idG.fillText("Case 1520", 175, 74);
      idG.fillStyle = "#94a3b8";
      idG.font = "20px monospace";
      idG.fillText("TEMPEST LEVEL II · 10 MHz 80286", 26, 112);
    }
    const idTex = new THREE.CanvasTexture(idCanvas);
    const idBadge = new THREE.Mesh(
      new THREE.PlaneGeometry(0.42, 0.105),
      new THREE.MeshStandardMaterial({ map: idTex, roughness: 0.4, metalness: 0.3 }),
    );
    idBadge.rotation.x = -Math.PI / 2;
    idBadge.position.set(-0.72, 0.158, -0.42);
    machine.add(idBadge);

    // --- KEYBOARD DECK: MICRO SWITCH ST CAPACITIVE KEYBOARD ---
    // Sculpted keyboard well with beveled inner surround
    const deckMat = new THREE.MeshStandardMaterial({
      color: 0x22242a,
      roughness: 0.55,
      metalness: 0.2,
    });
    const deckRecess = new THREE.Mesh(new THREE.BoxGeometry(2.02, 0.025, 0.72), deckMat);
    deckRecess.position.set(0, 0.155, 0.14);
    deckRecess.receiveShadow = true;
    machine.add(deckRecess);

    // Two-tone keycap materials (authentic Micro Switch PBT caps)
    const keyAlphaMat = new THREE.MeshStandardMaterial({
      color: 0x282a31, // Dark charcoal alphanumeric caps
      roughness: 0.40,
      metalness: 0.15,
    });
    const keyModMat = new THREE.MeshStandardMaterial({
      color: 0x40444f, // Battleship slate modifier caps (Ctrl, Alt, Esc, Fn, Enter)
      roughness: 0.42,
      metalness: 0.18,
    });

    const deck = new THREE.Group();
    deck.position.set(0, 0.170, 0.14);
    machine.add(deck);

    // Key layout: 5 rows with authentic function & modifier groupings
    for (let r = 0; r < 5; r++) {
      for (let c = 0; c < 14; c++) {
        const isSpace = r === 4 && c >= 4 && c <= 8;
        if (r === 4 && c > 4 && c <= 8) continue; // single wide spacebar

        const isModifier = c === 0 || c === 13 || r === 0 || (r === 4 && (c < 4 || c > 8));
        const currentKeyMat = isModifier ? keyModMat.clone() : keyAlphaMat.clone();

        const width = isSpace ? 0.72 : (c === 0 && r > 0) || (c === 13 && r > 0) ? 0.16 : 0.115;
        const xPos = isSpace ? 0 : -0.88 + c * 0.136;
        const zPos = -0.26 + r * 0.13;

        // Stepped key cap with slight spherical dish top
        const k = new THREE.Mesh(new THREE.BoxGeometry(width, 0.038, 0.11), currentKeyMat);
        k.position.set(xPos, 0, zPos);
        k.userData.key = isSpace ? "SPACE" : `R${r}C${c}`;
        k.castShadow = true;
        k.receiveShadow = true;
        deck.add(k);
      }
    }

    // Status Indicator LEDs at top-left of keyboard deck
    const powerLed = new THREE.Mesh(
      new THREE.SphereGeometry(0.009, 12, 12),
      new THREE.MeshStandardMaterial({ color: 0x22c55e, emissive: 0x16a34a, emissiveIntensity: 0.9 }),
    );
    powerLed.position.set(-0.92, 0.165, -0.21);
    machine.add(powerLed);

    const hddLed = new THREE.Mesh(
      new THREE.SphereGeometry(0.009, 12, 12),
      new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xd97706, emissiveIntensity: 0.7 }),
    );
    hddLed.position.set(-0.87, 0.165, -0.21);
    machine.add(hddLed);

    // --- DUAL MACHINED CYLINDRICAL BARREL HINGES ---
    // Connected to the back chassis, establishing the pivoting clamshell axis
    const hingeAxisZ = -0.73;
    const hingeAxisY = 0.17;

    const hingeMat = new THREE.MeshStandardMaterial({
      color: 0x3b3e47,
      roughness: 0.40,
      metalness: 0.50,
    });
    const hingeKnuckleGeo = new THREE.CylinderGeometry(0.048, 0.048, 0.38, 20);

    const leftHinge = new THREE.Mesh(hingeKnuckleGeo, hingeMat);
    leftHinge.rotation.z = Math.PI / 2;
    leftHinge.position.set(-0.75, hingeAxisY, hingeAxisZ);
    leftHinge.castShadow = true;
    machine.add(leftHinge);

    const rightHinge = new THREE.Mesh(hingeKnuckleGeo, hingeMat);
    rightHinge.rotation.z = Math.PI / 2;
    rightHinge.position.set(0.75, hingeAxisY, hingeAxisZ);
    rightHinge.castShadow = true;
    machine.add(rightHinge);

    // Central cable conduit passing display HV lines
    const cableConduit = new THREE.Mesh(
      new THREE.CylinderGeometry(0.024, 0.024, 0.42, 16),
      rubberMat,
    );
    cableConduit.rotation.z = Math.PI / 2;
    cableConduit.position.set(0, hingeAxisY, hingeAxisZ);
    machine.add(cableConduit);

    // --- SCULPTED CLAMSHELL LID (Bill Moggridge Fluted Magnesium Housing) ---
    const lid = new THREE.Group();
    lid.position.set(0, hingeAxisY, hingeAxisZ);
    machine.add(lid);

    // Outer magnesium lid shell with stepped perimeter bevel
    const lidSlab = new THREE.Mesh(new THREE.BoxGeometry(2.20, 1.18, 0.08), tubMat);
    lidSlab.position.set(0, 0.59, 0);
    lidSlab.castShadow = true;
    lidSlab.receiveShadow = true;
    lid.add(lidSlab);

    // Outer decorative fluted ribs on rear of lid (Bill Moggridge iconic motif)
    for (let ribIdx = -3; ribIdx <= 3; ribIdx++) {
      const rib = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.98, 0.015), tubAccentMat);
      rib.position.set(ribIdx * 0.26, 0.59, -0.045);
      lid.add(rib);
    }

    // Outer embossed "GRiD" brand badge on the outside of lid
    const outerLogoCanvas = document.createElement("canvas");
    outerLogoCanvas.width = 512;
    outerLogoCanvas.height = 128;
    const olg = outerLogoCanvas.getContext("2d");
    if (olg) {
      olg.fillStyle = "#27292f";
      olg.fillRect(0, 0, 512, 128);
      olg.fillStyle = "#f1f5f9";
      olg.font = "bold 72px sans-serif";
      olg.fillText("GRiD", 160, 88);
    }
    const outerLogoTex = new THREE.CanvasTexture(outerLogoCanvas);
    const outerLogoMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(0.48, 0.12),
      new THREE.MeshStandardMaterial({ map: outerLogoTex, roughness: 0.4, metalness: 0.3 }),
    );
    outerLogoMesh.rotation.y = Math.PI; // Faces rear when open
    outerLogoMesh.position.set(0, 0.59, -0.048);
    lid.add(outerLogoMesh);

    // Inner display bezel framing the flat panel
    const bezelMat = new THREE.MeshStandardMaterial({
      color: 0x2e3037,
      roughness: 0.55,
      metalness: 0.22,
    });
    const innerBezel = new THREE.Mesh(new THREE.BoxGeometry(1.98, 0.82, 0.025), bezelMat);
    innerBezel.position.set(0, 0.60, 0.045);
    innerBezel.receiveShadow = true;
    lid.add(innerBezel);

    // Dual Rotary Thumbwheels on Right Bezel (Brightness & Contrast Controls)
    const dialMat = new THREE.MeshStandardMaterial({ color: 0x18191d, roughness: 0.35, metalness: 0.7 });
    const dialGeo = new THREE.CylinderGeometry(0.018, 0.018, 0.035, 16);

    const brightDial = new THREE.Mesh(dialGeo, dialMat);
    brightDial.rotation.z = Math.PI / 2;
    brightDial.position.set(0.92, 0.70, 0.052);
    brightDial.castShadow = true;
    lid.add(brightDial);

    const contrastDial = new THREE.Mesh(dialGeo, dialMat);
    contrastDial.rotation.z = Math.PI / 2;
    contrastDial.position.set(0.92, 0.54, 0.052);
    contrastDial.castShadow = true;
    lid.add(contrastDial);

    // Inner "GRiD 1520" silk-screen logo beneath screen
    const innerLogoCanvas = document.createElement("canvas");
    innerLogoCanvas.width = 512;
    innerLogoCanvas.height = 96;
    const ilg = innerLogoCanvas.getContext("2d");
    if (ilg) {
      ilg.fillStyle = "#2e3037";
      ilg.fillRect(0, 0, 512, 96);
      ilg.fillStyle = "#f8fafc";
      ilg.font = "bold 38px sans-serif";
      ilg.fillText("GRiD", 20, 60);
      ilg.fillStyle = "#d97706";
      ilg.font = "bold 26px sans-serif";
      ilg.fillText("1520", 130, 58);
      ilg.fillStyle = "#94a3b8";
      ilg.font = "18px monospace";
      ilg.fillText("AMBER GAS-PLASMA 640x400", 250, 58);
    }
    const innerLogoTex = new THREE.CanvasTexture(innerLogoCanvas);
    const innerLogoMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(0.95, 0.08),
      new THREE.MeshStandardMaterial({ map: innerLogoTex, roughness: 0.5 }),
    );
    innerLogoMesh.position.set(-0.25, 0.24, 0.055);
    lid.add(innerLogoMesh);

    // Plasma / LCD screen canvas texture
    const scrCanvas = document.createElement("canvas");
    scrCanvas.width = 640;
    scrCanvas.height = 400;
    const scrTex = new THREE.CanvasTexture(scrCanvas);

    const drawScreen = (flicker: number) => {
      const g = scrCanvas.getContext("2d");
      if (!g) return;

      const isPlasma = displayModeRef.current === "plasma";
      if (isPlasma) {
        // Deep amber neon gas-plasma glow
        g.fillStyle = "#0c0601";
        g.fillRect(0, 0, 640, 400);

        // Subtle CRT/plasma scanlines
        g.fillStyle = "rgba(0,0,0,0.18)";
        for (let y = 0; y < 400; y += 3) {
          g.fillRect(0, y, 640, 1);
        }

        g.fillStyle = `rgba(255, ${120 + flicker}, 15, 0.96)`;
        g.shadowColor = "#ff7700";
        g.shadowBlur = 4;
      } else {
        // Reflective LCD mode
        g.fillStyle = "#8fa382";
        g.fillRect(0, 0, 640, 400);
        g.fillStyle = "#1e2b19";
        g.shadowBlur = 0;
      }

      g.font = "bold 24px 'Courier New', monospace";
      screenRef.current.slice(-12).forEach((line, i) => {
        g.fillText(line.slice(0, 46), 24, 42 + i * 28);
      });
      scrTex.needsUpdate = true;
    };
    drawScreen(0);

    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(1.68, 0.58),
      new THREE.MeshBasicMaterial({ map: scrTex }),
    );
    screen.position.set(-0.06, 0.62, 0.058);
    lid.add(screen);

    // Warm amber glow spilling from the gas-plasma tube onto keyboard deck
    const glow = new THREE.PointLight(0xff6600, 1.5, 4.2);
    glow.position.set(0, 0.62, 0.4);
    lid.add(glow);

    // Lid angle setup
    lidRef.current = lid;
    lid.rotation.x = THREE.MathUtils.degToRad(-(lidAngleRef.current - 90)) * 0.9;

    // Interactive key clicks
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
        (o.material as THREE.MeshStandardMaterial).color.setHex(0xf59e0b);
        window.setTimeout(() => (o.material as THREE.MeshStandardMaterial).color.setHex(orig), 140);
        setScreenLines((prev) => [...prev.slice(-11), `C:\\> key ${k}`]);
      }
    };
    renderer.domElement.addEventListener("click", onClick);

    // Orbit & Zoom controls
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
      theta -= (e.clientX - px) * 0.006;
      phi = Math.min(1.45, Math.max(0.2, phi - (e.clientY - py) * 0.006));
      px = e.clientX;
      py = e.clientY;
      updateCam();
    };
    const up = () => {
      dragging = false;
    };
    const wheel = (e: WheelEvent) => {
      radius = Math.min(6.5, Math.max(1.4, radius + e.deltaY * 0.002));
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
      if (tick % 24 === 0) {
        drawScreen(Math.floor(Math.random() * 12) - 6);
      }
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

  // Update lid rotation when lidAngle changes
  useEffect(() => {
    if (lidRef.current) {
      lidRef.current.rotation.x = THREE.MathUtils.degToRad(-(lidAngle - 90)) * 0.9;
    }
  }, [lidAngle]);

  // Update spotlight intensity dynamically
  useEffect(() => {
    if (spotLightRef.current) {
      spotLightRef.current.intensity = spotlightIntensity;
    }
    if (fillSpotRef.current) {
      fillSpotRef.current.intensity = spotlightIntensity * 0.55;
    }
  }, [spotlightIntensity]);

  // Update ambient light intensity
  useEffect(() => {
    if (ambientLightRef.current) {
      ambientLightRef.current.intensity = ambientIntensity;
    }
  }, [ambientIntensity]);

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandInput.trim()) return;
    runCommandDirect(commandInput);
    setCommandInput("");
  };

  const setCameraPreset = (name: "perspective" | "front" | "top" | "side") => {
    if (!setCamViewRef.current) return;
    switch (name) {
      case "perspective":
        setCamViewRef.current(0.55, 1.05, 3.3);
        break;
      case "front":
        setCamViewRef.current(0.0, 1.15, 2.7);
        break;
      case "top":
        setCamViewRef.current(0.0, 0.22, 3.1);
        break;
      case "side":
        setCamViewRef.current(1.57, 1.1, 3.2);
        break;
    }
  };

  return (
    <div className="space-y-6 p-4 max-w-7xl mx-auto">
      {/* Title Header with Badges */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              GRiDCase 1520
            </h1>
            <span className="rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-400 border border-amber-500/30">
              Hardware Station
            </span>
            <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-mono text-slate-300 border border-slate-700">
              1985 · AT-Class 286
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-400 max-w-3xl">
            Ruggedized die-cast magnesium clamshell with 10" amber gas-plasma flat panel display.
            NASA Space Shuttle orbital workhorse, military TEMPEST specification, and pioneer of the modern folding laptop.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/20">
            <Radio className="w-3.5 h-3.5 animate-pulse" /> Profile: mame_gridcase1520_profile
          </span>
        </div>
      </div>

      {/* 3D Viewport Controls Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 bg-slate-900/90 border border-slate-800 p-3 rounded-lg text-xs">
        {/* Lid Angle Control */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-slate-300 font-medium">
            <span>Clamshell Lid: {lidAngle}°</span>
            <span className="text-slate-500">{lidAngle === 0 ? "Closed" : lidAngle <= 95 ? "Typist" : "Open"}</span>
          </div>
          <input
            type="range"
            min={0}
            max={120}
            value={lidAngle}
            onChange={(e) => setLidAngle(Number(e.target.value))}
            className="w-full accent-amber-500 cursor-pointer"
          />
          <div className="flex gap-1 pt-1">
            <button onClick={() => setLidAngle(0)} className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px]">Closed</button>
            <button onClick={() => setLidAngle(95)} className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px]">95° Typist</button>
            <button onClick={() => setLidAngle(105)} className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px]">105° Normal</button>
            <button onClick={() => setLidAngle(120)} className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px]">120° Wide</button>
          </div>
        </div>

        {/* Studio Spotlight Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-slate-300 font-medium">
            <span className="flex items-center gap-1"><Sun className="w-3.5 h-3.5 text-amber-400" /> Spot: {spotlightIntensity.toFixed(1)}x</span>
            <span className="text-slate-400">Amb: {ambientIntensity.toFixed(1)}x</span>
          </div>
          <input
            type="range"
            min={0}
            max={10}
            step={0.5}
            value={spotlightIntensity}
            onChange={(e) => setSpotlightIntensity(Number(e.target.value))}
            className="w-full accent-amber-500 cursor-pointer"
          />
          <div className="flex justify-between items-center pt-1">
            <div className="flex gap-1">
              <button onClick={() => setSpotlightIntensity(2.0)} className="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px]">Low</button>
              <button onClick={() => setSpotlightIntensity(5.5)} className="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 text-[10px]">Optimal</button>
              <button onClick={() => setSpotlightIntensity(9.0)} className="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px]">High</button>
            </div>
            <button
              onClick={() => setAmbientIntensity((prev) => (prev >= 1.4 ? 0.8 : 1.6))}
              className="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 text-[10px]"
            >
              Toggle Amb
            </button>
          </div>
        </div>

        {/* Camera Angle Presets */}
        <div className="space-y-1.5">
          <span className="text-slate-300 font-medium block">Camera Viewpoint</span>
          <div className="grid grid-cols-2 gap-1 pt-0.5">
            <button onClick={() => setCameraPreset("perspective")} className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-left">Isometric</button>
            <button onClick={() => setCameraPreset("front")} className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-left">Cockpit Front</button>
            <button onClick={() => setCameraPreset("top")} className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-left">Deck Top</button>
            <button onClick={() => setCameraPreset("side")} className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-left">Profile Side</button>
          </div>
        </div>

        {/* Display Mode & Ambient Control */}
        <div className="space-y-1.5">
          <span className="text-slate-300 font-medium block">Display Emulation</span>
          <div className="flex gap-2">
            <button
              onClick={() => setDisplayMode("plasma")}
              className={`flex-1 py-1 rounded font-medium ${displayMode === "plasma" ? "bg-amber-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
            >
              Amber Gas-Plasma
            </button>
            <button
              onClick={() => setDisplayMode("lcd")}
              className={`flex-1 py-1 rounded font-medium ${displayMode === "lcd" ? "bg-emerald-700 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
            >
              LCD Contrast
            </button>
          </div>
          <div className="text-[10px] text-slate-500 pt-1">
            Drag to orbit · Scroll to zoom · Click keys to echo
          </div>
        </div>
      </div>

      {/* Main 3D Stage Viewport */}
      <div
        ref={stageContainerRef}
        className={`relative rounded-xl border border-slate-800 overflow-hidden bg-slate-950 shadow-2xl ${
          isFullscreen ? "h-screen w-screen border-none rounded-none" : ""
        }`}
      >
        <div
          ref={mountRef}
          className="w-full cursor-grab active:cursor-grabbing"
          style={{ height: isFullscreen ? "100vh" : 540 }}
        />

        {/* Floating Fullscreen Button inside Canvas */}
        <button
          onClick={toggleFullscreen}
          className="absolute top-3 right-3 z-20 rounded-lg bg-slate-900/90 border border-slate-700 p-2 text-slate-300 hover:text-white shadow-lg backdrop-blur"
          title={isFullscreen ? "Exit Fullscreen" : "Toggle Fullscreen View"}
        >
          {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </button>

        {/* Physical PC Keyboard Status Pill */}
        <div className="absolute top-3 left-3 z-20 rounded-lg bg-amber-950/80 border border-amber-500/40 px-3 py-1.5 text-xs text-amber-200 backdrop-blur shadow flex items-center gap-2">
          <Terminal className="h-3.5 w-3.5 text-amber-400" />
          <span>Physical Keyboard: <strong>ACTIVE</strong> (Type on your PC keyboard to enter DOS commands)</span>
        </div>

        {/* Overlay HUD overlay: Terminal Quick-Sender */}
        <div className="absolute bottom-3 left-3 right-3 z-20 bg-slate-900/80 backdrop-blur-md border border-slate-700/60 p-2.5 rounded-lg flex flex-col sm:flex-row items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-mono text-amber-400 shrink-0">
            <Terminal className="w-4 h-4 text-amber-500" />
            <span>Interactive Plasma Terminal:</span>
          </div>
          <form onSubmit={handleCommandSubmit} className="flex-1 flex gap-2 w-full">
            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="Type DOS command (e.g. DIR, VER, MEM, KERMIT, HELP, CLS)..."
              className="flex-1 bg-slate-950/90 border border-slate-700 rounded px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-amber-500"
            />
            <button
              type="submit"
              className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-slate-950 font-semibold rounded text-xs transition-colors shrink-0"
            >
              Send Command
            </button>
          </form>
        </div>
      </div>

      {/* Tab Navigation for Detailed Information */}
      <div className="border-b border-slate-800 flex gap-4 text-sm">
        <button
          onClick={() => setActiveTab("specs")}
          className={`pb-2.5 font-semibold transition-colors flex items-center gap-2 border-b-2 ${activeTab === "specs" ? "border-amber-500 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"}`}
        >
          <Cpu className="w-4 h-4" /> Hardware Specifications
        </button>
        <button
          onClick={() => setActiveTab("revive")}
          className={`pb-2.5 font-semibold transition-colors flex items-center gap-2 border-b-2 ${activeTab === "revive" ? "border-amber-500 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"}`}
        >
          <CheckCircle2 className="w-4 h-4" /> Restoration & Runbook (GRID_REVIVE.md)
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`pb-2.5 font-semibold transition-colors flex items-center gap-2 border-b-2 ${activeTab === "history" ? "border-amber-500 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"}`}
        >
          <BookOpen className="w-4 h-4" /> Aerospace & Military Heritage
        </button>
      </div>

      {/* Tab 1: Hardware Specifications */}
      {activeTab === "specs" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <Cpu className="w-4 h-4" /> Core Processing & Memory
            </div>
            <ul className="text-xs text-slate-300 space-y-2">
              <li><strong className="text-slate-100">Processor:</strong> Intel 80286 @ 10 MHz (1 wait state), 16-bit AT architecture</li>
              <li><strong className="text-slate-100">Coprocessor:</strong> Socket for 80287-10 numeric math coprocessor</li>
              <li><strong className="text-slate-100">Standard RAM:</strong> 640 KB conventional RAM (100ns parity-checked DRAM)</li>
              <li><strong className="text-slate-100">Expansion RAM:</strong> Up to 8 MB via internal GRiD 16-bit expansion card</li>
              <li><strong className="text-slate-100">BIOS Architecture:</strong> Phoenix / GRiD-OEM Rev 2.1 AT-compatible ROM (two 27C256 EPROMs)</li>
            </ul>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <Monitor className="w-4 h-4" /> Display & Graphics Subsystem
            </div>
            <ul className="text-xs text-slate-300 space-y-2">
              <li><strong className="text-slate-100">Display Panel:</strong> 10-inch diagonal Amber Gas-Plasma Flat Panel (Matsushita)</li>
              <li><strong className="text-slate-100">Resolution:</strong> 640 × 400 native resolution (CGA 640×200 and EGA 640×350 emulation)</li>
              <li><strong className="text-slate-100">Color/Phosphor:</strong> 590nm neon-argon orange discharge glow, infinite viewing angle</li>
              <li><strong className="text-slate-100">Text Density:</strong> 80 columns × 25 lines (9×14 character cell)</li>
              <li><strong className="text-slate-100">High-Voltage Inverter:</strong> 180V DC-to-AC driver circuitry with dedicated chassis isolation</li>
            </ul>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <HardDrive className="w-4 h-4" /> Storage, Chassis & I/O
            </div>
            <ul className="text-xs text-slate-300 space-y-2">
              <li><strong className="text-slate-100">Internal Storage:</strong> Conner CP-3044 40 MB 3.5" IDE hard drive + 1.44 MB Floppy</li>
              <li><strong className="text-slate-100">ROM Packs:</strong> Dual user-accessible GRiDROM slots for instant firmware apps</li>
              <li><strong className="text-slate-100">Chassis Construction:</strong> Die-cast magnesium alloy casing ("black tub"), EMP/TEMPEST shielded</li>
              <li><strong className="text-slate-100">Keyboard:</strong> 72-key capacitive matrix, Intel 8741 MCU, sculpted Micro Switch ST keys</li>
              <li><strong className="text-slate-100">External Ports:</strong> 9-pin RS-232C Serial, 25-pin Centronics Parallel, 9-pin RGB/CGA video</li>
            </ul>
          </div>
        </div>
      )}

      {/* Tab 2: Restoration Runbook (GRID_REVIVE.md) */}
      {activeTab === "revive" && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-5 space-y-4 text-xs text-slate-300">
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm pb-1 border-b border-slate-800">
            <AlertTriangle className="w-4 h-4 text-amber-500" /> Bench Restoration & Revival Protocol (from docs/GRID_REVIVE.md)
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3.5 rounded bg-slate-950/60 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-100 flex items-center gap-1.5 text-xs">
                <span className="w-5 h-5 rounded-full bg-red-500/20 text-red-400 inline-flex items-center justify-center text-[10px]">0</span>
                Rule Zero: Never Power On Without Battery Removal
              </h4>
              <p className="text-slate-400 leading-relaxed">
                40-year-old NiCd packs leak caustic potassium hydroxide electrolyte onto the motherboard.
                Step one is mechanical, not electrical: remove the battery pack, inspect the Intel 8741 keyboard MCU area,
                neutralize alkaline crust with mild acid + isopropanol, and check high-voltage capacitors before applying power.
              </p>
            </div>

            <div className="p-3.5 rounded bg-slate-950/60 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-100 flex items-center gap-1.5 text-xs">
                <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 inline-flex items-center justify-center text-[10px]">1</span>
                Phase 1: Dump ROMs & Emulation Oracle
              </h4>
              <p className="text-slate-400 leading-relaxed">
                Dump both BIOS EPROMs (Part 300778-21 & 300777-21) and verify against archive.org preservation dumps.
                Set up an 86Box/PCem emulator with generic 286 AT architecture and the 720KB MS-DOS 3.3 system disk to establish the software oracle.
              </p>
            </div>

            <div className="p-3.5 rounded bg-slate-950/60 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-100 flex items-center gap-1.5 text-xs">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 inline-flex items-center justify-center text-[10px]">2</span>
                Branch A (Non-Destructive Serial AI Console)
              </h4>
              <p className="text-slate-400 leading-relaxed">
                Boot real MS-DOS on the 1520 and run Kermit in VT100 mode connected via 9-pin RS-232 serial to a Raspberry Pi at 19,200 baud.
                The vintage amber gas-plasma becomes an interactive AI chatbot console without modifying a single motherboard trace.
              </p>
            </div>

            <div className="p-3.5 rounded bg-slate-950/60 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-100 flex items-center gap-1.5 text-xs">
                <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 inline-flex items-center justify-center text-[10px]">3</span>
                Branch B (Reversible Internal Carrier)
              </h4>
              <p className="text-slate-400 leading-relaxed">
                Retain original magnesium chassis and keyboard. If the gas-plasma tube has lost seal or inverter is dead,
                install a high-contrast transflective LCD behind the original bezel with a Pi 5 scanning the keyboard matrix via GPIO.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Historical & Aerospace Context */}
      {activeTab === "history" && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-5 space-y-4 text-xs text-slate-300">
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm pb-1 border-b border-slate-800">
            <Shield className="w-4 h-4 text-amber-500" /> Industrial Design, NASA Space Shuttle & Espionage Legacy
          </div>

          <div className="space-y-3 leading-relaxed text-slate-300">
            <p>
              Designed by visionary British industrial designer <strong className="text-slate-100">Bill Moggridge</strong> (co-founder of IDEO),
              the GRiD Compass and GRiDCase family invented the folding clamshell form factor (US Patent D280,511) that defines every modern notebook computer today.
              Before GRiD, portable computers were "luggables" like the 25-pound Osborne 1 or Compaq Portable with bulky cathode-ray tubes.
            </p>
            <p>
              The rugged die-cast magnesium housing wasn't just aesthetic: it was engineered to survive extreme shock, vibration, and thermal shifts.
              The GRiDCase was certified for <strong className="text-slate-100">TEMPEST Level II</strong> compliance, preventing electromagnetic eavesdropping by foreign intelligence services,
              making it standard field kit for the CIA, NSA, White House military communications, and military command staff during the Cold War.
            </p>
            <p>
              In aerospace history, modified GRiD portables served as the <strong className="text-slate-100">SPOC (Shuttle Portable On-Orbit Computer)</strong> on NASA Space Shuttle missions starting with STS-51-A in 1984.
              Mounted directly onto the flight deck instrument panels, astronauts used the bright orange flat display to monitor orbital trajectories, payload deployments, and re-entry vectors in real time.
            </p>
          </div>
        </div>
      )}

      {/* Footer metadata */}
      <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 border-t border-slate-800 pt-3 gap-2">
        <div>
          FrankenGRiD Station · Companion: <span className="text-slate-400 font-medium">hardware-m1.tsx</span> · Profile: <span className="font-mono text-slate-400">mame_gridcase1520_profile</span>
        </div>
        <div className="font-mono">
          docs/GRID_REVIVE.md · Three.js r187
        </div>
      </div>
    </div>
  );
}
