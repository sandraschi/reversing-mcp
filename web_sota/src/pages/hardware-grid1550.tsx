import { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";
import {
  Cpu,
  HardDrive,
  Monitor,
  Sun,
  Terminal,
  BookOpen,
  Radio,
  Maximize2,
  Minimize2,
  Battery,
  Plug,
  Sliders,
  Info,
} from "lucide-react";

/**
 * Hardware GRiDCase 1550 SX (1990) Flagship Workstation.
 * 386SX @ 20 MHz, Full 640x480 VGA Amber Gas-Plasma Display (16-level grayscale),
 * IsoPoint roller-bar pointing device, and interchangeable modular Power Pods (AC / Battery).
 * Interactive Three.js 3D viewport with fullscreen toggle, physical PC keyboard capture,
 * and full-featured MS-DOS 4.01 / 5.0 emulation environment.
 */

const BOOT_LINES_1550 = [
  "GRiD Systems Corp.  ROM BIOS REV 4.02",
  "Intel 80386SX-20 MHz CPU Detected",
  "80387SX Math Coprocessor Initialized",
  "2048K SIPP RAM OK   384K Shadow RAM Active",
  "Conner CP30104 120MB IDE Fixed Disk (C:) Ready",
  "IsoPoint Driver v2.10 (PORT 0x2E8, IRQ 3) Loaded",
  "VGA Gas-Plasma 640x480 (16 Gray) Subsystem OK",
  "Starting MS-DOS Version 5.00 (GRiD-OEM) ...",
  "C:\\> _",
];

type DisplayMode = "plasma" | "lcd";
type PowerPodMode = "ac" | "battery";

export function HardwareGrid1550() {
  const mountRef = useRef<HTMLDivElement>(null);
  const stageContainerRef = useRef<HTMLDivElement>(null);

  const [screenLines, setScreenLines] = useState<string[]>(BOOT_LINES_1550);
  const [currentPrompt, setCurrentPrompt] = useState<string>("");
  const [lidAngle, setLidAngle] = useState(105);
  const [spotlightIntensity, setSpotlightIntensity] = useState(6.0);
  const [ambientIntensity, setAmbientIntensity] = useState(1.5);
  const [displayMode, setDisplayMode] = useState<DisplayMode>("plasma");
  const [powerPod, setPowerPod] = useState<PowerPodMode>("ac");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [commandInput, setCommandInput] = useState("");
  const [activeTab, setActiveTab] = useState<"specs" | "isopoint" | "powerpod" | "dos">("specs");

  const screenRef = useRef<string[]>(BOOT_LINES_1550);
  screenRef.current = screenLines;
  const currentPromptRef = useRef<string>("");
  currentPromptRef.current = currentPrompt;

  const displayModeRef = useRef<DisplayMode>("plasma");
  displayModeRef.current = displayMode;
  const lidRef = useRef<THREE.Group | null>(null);
  const lidAngleRef = useRef(lidAngle);
  lidAngleRef.current = lidAngle;

  const spotLightRef = useRef<THREE.SpotLight | null>(null);
  const fillSpotRef = useRef<THREE.SpotLight | null>(null);
  const ambientLightRef = useRef<THREE.AmbientLight | null>(null);
  const setCamViewRef = useRef<((t: number, p: number, r: number) => void) | null>(null);
  const powerPodMeshRef = useRef<THREE.Mesh | null>(null);

  // Command Execution Engine
  const executeCommand = useCallback((rawCmd: string) => {
    const cmd = rawCmd.trim().toUpperCase();
    const args = cmd.split(/\s+/);
    const main = args[0] || "";

    const newLines = [...screenRef.current];
    // Replace trailing prompt line if present
    if (newLines[newLines.length - 1]?.startsWith("C:\\> ")) {
      newLines[newLines.length - 1] = `C:\\> ${rawCmd}`;
    } else {
      newLines.push(`C:\\> ${rawCmd}`);
    }

    if (!main) {
      newLines.push("C:\\> _");
      setScreenLines(newLines.slice(-14));
      setCurrentPrompt("");
      return;
    }

    if (main === "DIR") {
      newLines.push(
        " Volume in drive C has no label",
        " Volume Serial Number is 1E4D-0F29",
        " Directory of C:\\",
        "COMMAND  COM    47845  04-09-91  5:00a",
        "FW       EXE   214820  09-12-88  3:14p",
        "FRED     LIB    52140  09-12-88  3:15p",
        "POWERPLT FW     84210  11-04-89  9:20a",
        "CONFIG   SYS      214  08-14-91 10:12p",
        "AUTOEXEC BAT      188  08-14-91 10:15p",
        "ISOPOINT SYS    12480  06-22-90  1:40p",
        "GRIDUTIL EXE    52840  07-11-90  4:20p",
        "QBASIC   EXE   254799  04-09-91  5:00a",
        "EDIT     COM      413  04-09-91  5:00a",
        "PRINCE   EXE   148290  10-03-89 12:00p",
        "       11 file(s)     868,239 bytes",
        "                   97,820,160 bytes free",
      );
    } else if (main === "FW" || main === "FRAMEWORK" || main === "POWERPLT" || main === "RUN POWERPLT") {
      newLines.push(
        "--- Ashton-Tate Framework III (v1.1) / 386 Enhanced ---",
        "Apps  Disk  Create  Edit  Locate  Frames  Words  Numbers  Graphs  Print",
        "┌─[ KRAFTWERK-WIEN: ENERGIEVERSORGUNG AG (Database Frame) ]────────┐",
        "│ BLOCK  TURBINE_TYP  MW_SOLL  MW_IST  TEMP_C  DRUCK_BAR  STATUS    │",
        "│ T1     KONDENSATION  240.0   239.8   542°C    164.8     NOMINAL   │",
        "│ T2     KONDENSATION  240.0   241.4   538°C    165.2     NOMINAL   │",
        "│ G3     GASTURBINE    120.0   120.2   495°C    120.5     SPITZE    │",
        "└───────────────────────────────────────────────────────────────────┘",
        "┌─[ TAGESBILANZ & LEISTUNGSFAKTOR (Spreadsheet Frame) ]─────────────┐",
        "│ UHRZEIT  ERZEUGUNG_MWH  VERBRAUCH_MWH  NETZ-SALDO   FRED_FORMEL   │",
        "│ 08:00       598.2           540.0        +58.2      @SUM(B1:B3)   │",
        "│ 09:00       612.4           585.1        +27.3      @DELTA(B,C)   │",
        "│ 10:00       601.4           570.0        +31.4      @CALC_GRID    │",
        "└───────────────────────────────────────────────────────────────────┘",
        "[FRED]: @SUM(Turbinen.MW_IST) -> 601.4 MW. Status: 15 JAHRE FEHLERFREI",
        "Framework running. Type 'EXIT' or 'DOS' to return to MS-DOS prompt.",
      );
    } else if (main === "EXIT" || main === "QUIT" || main === "DOS") {
      newLines.push("Exiting Framework III ...", "Back to MS-DOS.");
    } else if (main.startsWith("@") || main.startsWith("FRED")) {
      newLines.push(
        `[FRED Eval]: ${rawCmd}`,
        `Result: OK. Formula compiled into active Frame. Calculated: 601.4 MW`,
      );
    } else if (main === "VER") {
      newLines.push("MS-DOS Version 5.00 (GRiD-OEM 1550 SX 386)");
    } else if (main === "MEM") {
      newLines.push(
        "Memory Type         Total       Used       Free",
        "----------------  --------   --------   --------",
        "Conventional          640K        58K       582K",
        "Upper (Shadow)        384K       128K       256K",
        "Extended (XMS)       1024K          0K      1024K",
        "----------------  --------   --------   --------",
        "Total Memory         2048K       186K      1862K",
        "Total under 1 MB      640K        58K       582K",
        "Largest executable program size:            581K",
      );
    } else if (main === "ISOPOINT" || main === "MOUSE") {
      newLines.push(
        "IsoPoint Hardware Subsystem v2.10",
        "Patented Culver/GRiD Roller Bar Controller",
        "Port: 0x2E8  IRQ: 3  Baud: 9600  Mode: Absolute/Relative",
        "Status: Active. Calibration: OK. Cursor bound to VGA.",
      );
    } else if (main === "GRIDUTIL" || main === "DIAG") {
      newLines.push(
        "GRiDCase 1550 SX Diagnostic Utility v3.2",
        "CPU: Intel 80386SX-20 MHz (Stepping B1) — PASS",
        "FPU: Intel 80387SX Math Coprocessor — PRESENT",
        "RAM: 2048 KB SIPP 80ns Parity Check — PASS",
        "VGA: 640x480 16-Gray Plasma Inverter — 185V NOMINAL",
        "Power: Modular Pod (" + (powerPod === "ac" ? "120/240V AC Mains" : "12V NiCad Battery") + ") — NORMAL",
      );
    } else if (main === "EDIT") {
      newLines.push(
        "--- MS-DOS Editor v1.0 ---",
        "File: C:\\AUTOEXEC.BAT",
        "@ECHO OFF",
        "PATH=C:\\DOS;C:\\GRID",
        "DEVICE=C:\\ISOPOINT.SYS /A",
        "PROMPT $P$G",
        "Press ESC to exit editor...",
      );
    } else if (main === "BASIC" || main === "QBASIC") {
      newLines.push(
        "Microsoft QBasic Version 1.0 (GRiD-OEM)",
        "Copyright (C) Microsoft Corporation, 1991.",
        "10 PRINT \"*** GRIDCASE 1550 SX 386 WORKSTATION ***\"",
        "20 FOR I = 1 TO 3: PRINT \"PLASMA VGA ACTIVE\": NEXT I",
        "Ready.",
      );
    } else if (main === "PRINCE") {
      newLines.push(
        "Jordan Mechner's Prince of Persia (1989)",
        "Loading 16-shade amber VGA graphics drivers...",
        "Sound: Internal PC Speaker beep synthesis",
        "Press CTRL+Q to exit to DOS.",
      );
    } else if (main === "HELP") {
      newLines.push(
        "Available commands:",
        "  DIR, VER, MEM, ISOPOINT, GRIDUTIL, EDIT, QBASIC, PRINCE, CLS",
      );
    } else if (main === "CLS") {
      setScreenLines(["C:\\> _"]);
      setCurrentPrompt("");
      return;
    } else {
      newLines.push(`Bad command or file name: ${rawCmd}`);
    }

    newLines.push("C:\\> _");
    setScreenLines(newLines.slice(-14));
    setCurrentPrompt("");
  }, [powerPod]);

  // Form submit from UI input box
  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandInput.trim()) return;
    executeCommand(commandInput);
    setCommandInput("");
  };

  // Fullscreen toggle handler
  const toggleFullscreen = () => {
    if (!stageContainerRef.current) return;
    if (!document.fullscreenElement) {
      stageContainerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  useEffect(() => {
    const onFsChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  // Capture Physical PC Keyboard when typing on screen or in fullscreen!
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if focused on standard text input/textarea
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === "Enter") {
        e.preventDefault();
        const cmd = currentPromptRef.current;
        executeCommand(cmd);
      } else if (e.key === "Backspace") {
        e.preventDefault();
        setCurrentPrompt((prev) => {
          const next = prev.slice(0, -1);
          setScreenLines((old) => {
            const copy = [...old];
            copy[copy.length - 1] = `C:\\> ${next}_`;
            return copy;
          });
          return next;
        });
      } else if (e.key === "Escape") {
        e.preventDefault();
        setCurrentPrompt("");
        setScreenLines((old) => {
          const copy = [...old];
          copy[copy.length - 1] = "C:\\> _";
          return copy;
        });
      } else if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
        e.preventDefault();
        const char = e.key.toUpperCase();
        setCurrentPrompt((prev) => {
          const next = prev + char;
          setScreenLines((old) => {
            const copy = [...old];
            copy[copy.length - 1] = `C:\\> ${next}_`;
            return copy;
          });
          return next;
        });
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [executeCommand]);

  // Sync spot and ambient lights
  useEffect(() => {
    if (spotLightRef.current) spotLightRef.current.intensity = spotlightIntensity;
    if (fillSpotRef.current) fillSpotRef.current.intensity = spotlightIntensity * 0.55;
  }, [spotlightIntensity]);

  useEffect(() => {
    if (ambientLightRef.current) ambientLightRef.current.intensity = ambientIntensity;
  }, [ambientIntensity]);

  // Sync Power Pod Material (AC vs Battery)
  useEffect(() => {
    if (powerPodMeshRef.current) {
      if (powerPod === "ac") {
        (powerPodMeshRef.current.material as THREE.MeshStandardMaterial).color.setHex(0x272a31);
      } else {
        (powerPodMeshRef.current.material as THREE.MeshStandardMaterial).color.setHex(0x1a1c22);
      }
    }
  }, [powerPod]);

  // Update lid angle
  useEffect(() => {
    if (lidRef.current) {
      lidRef.current.rotation.x = THREE.MathUtils.degToRad(-(lidAngle - 90)) * 0.9;
    }
  }, [lidAngle]);

  // ==========================================
  // THREE.JS GRiDCASE 1550 SX 3D ENGINE
  // ==========================================
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const W = mount.clientWidth || 920;
    const H = isFullscreen ? window.innerHeight : 560;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0e17);

    const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
    let theta = 0.52;
    let phi = 1.05;
    let radius = 3.3;

    const updateCam = () => {
      camera.position.set(
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.cos(theta),
      );
      camera.lookAt(0, 0.22, 0);
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

    // Studio Ground Grid & Dark Floor
    const gridHelper = new THREE.GridHelper(10, 24, 0xf59e0b, 0x1e293b);
    gridHelper.position.y = -0.005;
    scene.add(gridHelper);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(14, 14),
      new THREE.MeshStandardMaterial({ color: 0x070b12, roughness: 0.9, metalness: 0.1 }),
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.01;
    ground.receiveShadow = true;
    scene.add(ground);

    // --- LIGHTING RIG ---
    const spot = new THREE.SpotLight(0xfff6ea, spotlightIntensity);
    spot.position.set(1.4, 5.2, 3.5);
    spot.angle = Math.PI / 3.8;
    spot.penumbra = 0.45;
    spot.decay = 1.2;
    spot.castShadow = true;
    scene.add(spot);
    spotLightRef.current = spot;

    const fillSpot = new THREE.SpotLight(0xffeedd, spotlightIntensity * 0.55);
    fillSpot.position.set(-2.8, 4.4, 2.2);
    fillSpot.angle = Math.PI / 3.2;
    fillSpot.penumbra = 0.6;
    scene.add(fillSpot);
    fillSpotRef.current = fillSpot;

    const amb = new THREE.AmbientLight(0xd4e2f5, ambientIntensity);
    scene.add(amb);
    ambientLightRef.current = amb;

    const dirKey = new THREE.DirectionalLight(0xfff8ee, 1.8);
    dirKey.position.set(2.5, 4.5, 3.5);
    scene.add(dirKey);

    const dirFill = new THREE.DirectionalLight(0x94b4dd, 1.0);
    dirFill.position.set(-3.5, 3.0, 1.5);
    scene.add(dirFill);

    const machine = new THREE.Group();
    scene.add(machine);
    spot.target = machine;
    fillSpot.target = machine;

    // --- GRiDCASE 1550 SX DIE-CAST MAGNESIUM CHASSIS ---
    const tubMat = new THREE.MeshStandardMaterial({
      color: 0x363940, // AZ91D die-cast magnesium
      roughness: 0.50,
      metalness: 0.36,
    });
    const tubAccentMat = new THREE.MeshStandardMaterial({
      color: 0x27292f,
      roughness: 0.60,
      metalness: 0.25,
    });
    const rubberMat = new THREE.MeshStandardMaterial({
      color: 0x141518,
      roughness: 0.88,
      metalness: 0.05,
    });
    const metalPortMat = new THREE.MeshStandardMaterial({
      color: 0xc4c8d0,
      roughness: 0.28,
      metalness: 0.82,
    });

    // Lower belly & upper wedge
    const lowerBelly = new THREE.Mesh(new THREE.BoxGeometry(2.20, 0.07, 1.50), tubAccentMat);
    lowerBelly.position.set(0, 0.035, 0);
    lowerBelly.castShadow = true;
    lowerBelly.receiveShadow = true;
    machine.add(lowerBelly);

    const upperDeck = new THREE.Mesh(new THREE.BoxGeometry(2.22, 0.09, 1.52), tubMat);
    upperDeck.position.set(0, 0.105, 0);
    upperDeck.castShadow = true;
    upperDeck.receiveShadow = true;
    machine.add(upperDeck);

    // Front wrist rest
    const palmRest = new THREE.Mesh(new THREE.BoxGeometry(2.20, 0.02, 0.28), tubMat);
    palmRest.position.set(0, 0.155, 0.62);
    palmRest.receiveShadow = true;
    machine.add(palmRest);

    // Four bottom shock feet
    const footPositions = [
      [-0.96, 0.01, -0.64],
      [0.96, 0.01, -0.64],
      [-0.96, 0.01, 0.64],
      [0.96, 0.01, 0.64],
    ];
    footPositions.forEach(([fx, fy, fz]) => {
      const foot = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.025, 16), rubberMat);
      foot.position.set(fx, fy, fz);
      machine.add(foot);
    });

    // --- ISOPOINT ROLLER-BAR POINTING STICK ---
    // The defining innovation of the 1550 SX! Situated below the spacebar on the wrist rest
    const isoWell = new THREE.Mesh(
      new THREE.BoxGeometry(0.52, 0.018, 0.07),
      new THREE.MeshStandardMaterial({ color: 0x181a1f, roughness: 0.8 }),
    );
    isoWell.position.set(0, 0.162, 0.58);
    machine.add(isoWell);

    // The cylindrical rotating and sliding IsoPoint roller bar
    const isoBar = new THREE.Mesh(
      new THREE.CylinderGeometry(0.014, 0.014, 0.36, 16),
      new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.35, metalness: 0.4 }),
    );
    isoBar.rotation.z = Math.PI / 2;
    isoBar.position.set(0, 0.174, 0.58);
    isoBar.castShadow = true;
    machine.add(isoBar);

    // Left and right click buttons on either side of the roller bar
    const leftClick = new THREE.Mesh(new THREE.BoxGeometry(0.065, 0.015, 0.045), tubAccentMat);
    leftClick.position.set(-0.22, 0.168, 0.58);
    machine.add(leftClick);

    const rightClick = new THREE.Mesh(new THREE.BoxGeometry(0.065, 0.015, 0.045), tubAccentMat);
    rightClick.position.set(0.22, 0.168, 0.58);
    machine.add(rightClick);

    // IsoPoint silk-screen legend
    const isoCanvas = document.createElement("canvas");
    isoCanvas.width = 256;
    isoCanvas.height = 64;
    const ig = isoCanvas.getContext("2d");
    if (ig) {
      ig.fillStyle = "#363940";
      ig.fillRect(0, 0, 256, 64);
      ig.fillStyle = "#f8fafc";
      ig.font = "bold 24px monospace";
      ig.fillText("IsoPoint®", 60, 42);
    }
    const isoTex = new THREE.CanvasTexture(isoCanvas);
    const isoBadge = new THREE.Mesh(
      new THREE.PlaneGeometry(0.18, 0.045),
      new THREE.MeshStandardMaterial({ map: isoTex, roughness: 0.5 }),
    );
    isoBadge.rotation.x = -Math.PI / 2;
    isoBadge.position.set(0, 0.166, 0.66);
    machine.add(isoBadge);

    // --- REAR INTERCHANGEABLE MODULAR POWER POD SYSTEM ---
    // The slide-in cavity on the rear-right of the chassis
    const podMat = new THREE.MeshStandardMaterial({
      color: powerPod === "ac" ? 0x272a31 : 0x1a1c22,
      roughness: 0.55,
      metalness: 0.3,
    });
    const powerPodMesh = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.08, 0.28), podMat);
    powerPodMesh.position.set(0.68, 0.085, -0.62);
    powerPodMesh.castShadow = true;
    machine.add(powerPodMesh);
    powerPodMeshRef.current = powerPodMesh;

    // AC Mains Receptacle on the back of the AC Pod
    const acInlet = new THREE.Mesh(
      new THREE.BoxGeometry(0.12, 0.04, 0.02),
      new THREE.MeshStandardMaterial({ color: 0x0f1115, roughness: 0.8 }),
    );
    acInlet.position.set(0.68, 0.085, -0.765);
    machine.add(acInlet);

    // Rear I/O Connectors on the fixed chassis plate
    const serialPort1 = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.038, 0.03), metalPortMat);
    serialPort1.position.set(-0.75, 0.085, -0.765);
    machine.add(serialPort1);

    const serialPort2 = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.038, 0.03), metalPortMat);
    serialPort2.position.set(-0.52, 0.085, -0.765);
    machine.add(serialPort2);

    const parallelPort = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.038, 0.03), metalPortMat);
    parallelPort.position.set(-0.22, 0.085, -0.765);
    machine.add(parallelPort);

    const vgaPort = new THREE.Mesh(
      new THREE.BoxGeometry(0.14, 0.038, 0.03),
      new THREE.MeshStandardMaterial({ color: 0x1e3a8a, roughness: 0.4, metalness: 0.7 }), // Blue 15-pin VGA D-sub!
    );
    vgaPort.position.set(0.10, 0.085, -0.765);
    machine.add(vgaPort);

    // --- KEYBOARD DECK ---
    const deckMat = new THREE.MeshStandardMaterial({ color: 0x22242a, roughness: 0.55 });
    const deckRecess = new THREE.Mesh(new THREE.BoxGeometry(2.04, 0.025, 0.72), deckMat);
    deckRecess.position.set(0, 0.155, 0.14);
    machine.add(deckRecess);

    const keyAlphaMat = new THREE.MeshStandardMaterial({ color: 0x282a31, roughness: 0.40 });
    const keyModMat = new THREE.MeshStandardMaterial({ color: 0x40444f, roughness: 0.42 });

    const deck = new THREE.Group();
    deck.position.set(0, 0.170, 0.14);
    machine.add(deck);

    for (let r = 0; r < 5; r++) {
      for (let c = 0; c < 14; c++) {
        const isSpace = r === 4 && c >= 4 && c <= 8;
        if (r === 4 && c > 4 && c <= 8) continue;

        const isModifier = c === 0 || c === 13 || r === 0 || (r === 4 && (c < 4 || c > 8));
        const currentKeyMat = isModifier ? keyModMat.clone() : keyAlphaMat.clone();

        const width = isSpace ? 0.72 : (c === 0 && r > 0) || (c === 13 && r > 0) ? 0.16 : 0.115;
        const xPos = isSpace ? 0 : -0.88 + c * 0.136;
        const zPos = -0.26 + r * 0.13;

        const k = new THREE.Mesh(new THREE.BoxGeometry(width, 0.038, 0.11), currentKeyMat);
        k.position.set(xPos, 0, zPos);
        k.userData.key = isSpace ? "SPACE" : `R${r}C${c}`;
        k.castShadow = true;
        k.receiveShadow = true;
        deck.add(k);
      }
    }

    // 1550 SX Identification Badge
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
      idG.fillStyle = "#f59e0b";
      idG.fillText("Case 1550 SX", 175, 74);
      idG.fillStyle = "#94a3b8";
      idG.font = "20px monospace";
      idG.fillText("386SX · VGA 640x480 PLASMA · ISOPOINT", 26, 112);
    }
    const idTex = new THREE.CanvasTexture(idCanvas);
    const idBadge = new THREE.Mesh(
      new THREE.PlaneGeometry(0.48, 0.12),
      new THREE.MeshStandardMaterial({ map: idTex, roughness: 0.4 }),
    );
    idBadge.rotation.x = -Math.PI / 2;
    idBadge.position.set(-0.72, 0.158, -0.42);
    machine.add(idBadge);

    // --- FULL 640x480 VGA GAS-PLASMA DISPLAY & CLAMSHELL LID ---
    const hingeAxisZ = -0.73;
    const hingeAxisY = 0.17;

    const lid = new THREE.Group();
    lid.position.set(0, hingeAxisY, hingeAxisZ);
    machine.add(lid);

    const lidSlab = new THREE.Mesh(new THREE.BoxGeometry(2.20, 1.28, 0.08), tubMat);
    lidSlab.position.set(0, 0.64, 0);
    lidSlab.castShadow = true;
    lidSlab.receiveShadow = true;
    lid.add(lidSlab);

    // Rear fluted ribs
    for (let ribIdx = -3; ribIdx <= 3; ribIdx++) {
      const rib = new THREE.Mesh(new THREE.BoxGeometry(0.03, 1.08, 0.015), tubAccentMat);
      rib.position.set(ribIdx * 0.26, 0.64, -0.045);
      lid.add(rib);
    }

    // Outer logo
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
      new THREE.MeshStandardMaterial({ map: outerLogoTex, roughness: 0.4 }),
    );
    outerLogoMesh.rotation.y = Math.PI;
    outerLogoMesh.position.set(0, 0.64, -0.048);
    lid.add(outerLogoMesh);

    // Inner Bezel (Thinner, framing the taller 640x480 VGA panel!)
    const innerBezel = new THREE.Mesh(
      new THREE.BoxGeometry(2.04, 1.08, 0.025),
      new THREE.MeshStandardMaterial({ color: 0x2e3037, roughness: 0.55 }),
    );
    innerBezel.position.set(0, 0.64, 0.045);
    innerBezel.receiveShadow = true;
    lid.add(innerBezel);

    // Brightness and Contrast thumbwheels on right bezel
    const dialMat = new THREE.MeshStandardMaterial({ color: 0x18191d, roughness: 0.35, metalness: 0.7 });
    const brightDial = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.035, 16), dialMat);
    brightDial.rotation.z = Math.PI / 2;
    brightDial.position.set(0.96, 0.78, 0.052);
    lid.add(brightDial);

    const contrastDial = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.035, 16), dialMat);
    contrastDial.rotation.z = Math.PI / 2;
    contrastDial.position.set(0.96, 0.58, 0.052);
    lid.add(contrastDial);

    // FULL 640x480 VGA DISPLAY BUFFER
    const scrCanvas = document.createElement("canvas");
    scrCanvas.width = 640;
    scrCanvas.height = 480;
    const scrTex = new THREE.CanvasTexture(scrCanvas);

    const drawScreen = (flicker: number) => {
      const g = scrCanvas.getContext("2d");
      if (!g) return;

      const isPlasma = displayModeRef.current === "plasma";
      if (isPlasma) {
        g.fillStyle = "#0c0601";
        g.fillRect(0, 0, 640, 480);

        // Plasma scanlines
        g.fillStyle = "rgba(0,0,0,0.16)";
        for (let y = 0; y < 480; y += 3) {
          g.fillRect(0, y, 640, 1);
        }

        // Amber neon text with glow
        g.fillStyle = `rgba(255, ${125 + flicker}, 15, 0.96)`;
        g.shadowColor = "#ff7700";
        g.shadowBlur = 4;
      } else {
        g.fillStyle = "#8fa382";
        g.fillRect(0, 0, 640, 480);
        g.fillStyle = "#1e2b19";
        g.shadowBlur = 0;
      }

      g.font = "bold 23px 'Courier New', monospace";
      screenRef.current.slice(-14).forEach((line, i) => {
        g.fillText(line.slice(0, 46), 24, 40 + i * 31);
      });
      scrTex.needsUpdate = true;
    };
    drawScreen(0);

    // Display plane: taller 4:3 ratio (1.82 x 0.94 units)
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(1.82, 0.94),
      new THREE.MeshBasicMaterial({ map: scrTex }),
    );
    screen.position.set(-0.04, 0.64, 0.058);
    lid.add(screen);

    // Amber screen light spill
    const glow = new THREE.PointLight(0xff6600, 1.6, 4.5);
    glow.position.set(0, 0.64, 0.4);
    lid.add(glow);

    lidRef.current = lid;
    lid.rotation.x = THREE.MathUtils.degToRad(-(lidAngleRef.current - 90)) * 0.9;

    // Raycast key clicks
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
        executeCommand(`KEY ${k}`);
      }
    };
    renderer.domElement.addEventListener("click", onClick);

    // Orbit & Zoom
    let dragging = false;
    let px = 0;
    let py = 0;
    const down = (e: MouseEvent) => { dragging = true; px = e.clientX; py = e.clientY; };
    const move = (e: MouseEvent) => {
      if (!dragging) return;
      theta -= (e.clientX - px) * 0.006;
      phi = Math.min(1.45, Math.max(0.2, phi - (e.clientY - py) * 0.006));
      px = e.clientX;
      py = e.clientY;
      updateCam();
    };
    const up = () => { dragging = false; };
    const wheel = (e: WheelEvent) => {
      radius = Math.min(6.5, Math.max(1.4, radius + e.deltaY * 0.002));
      updateCam();
    };

    renderer.domElement.addEventListener("mousedown", down);
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    renderer.domElement.addEventListener("wheel", wheel);

    const onResize = () => {
      const w = mount.clientWidth || 920;
      const h = isFullscreen ? window.innerHeight : 560;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    window.addEventListener("resize", onResize);

    let raf = 0;
    let tick = 0;
    const loop = () => {
      raf = requestAnimationFrame(loop);
      tick++;
      if (tick % 6 === 0) {
        drawScreen(Math.sin(tick * 0.3) * 15);
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
  }, [executeCommand, isFullscreen, powerPod]);

  return (
    <div className="space-y-6 p-4 max-w-7xl mx-auto">
      {/* Title Header with Badges */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
              <Cpu className="h-6 w-6 text-amber-500" />
              GRiDCase 1550 SX
            </h1>
            <span className="rounded-full bg-amber-500/20 px-2.5 py-0.5 text-xs font-semibold text-amber-400 border border-amber-500/30">
              1990 Flagship Workstation
            </span>
            <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-mono text-slate-300 border border-slate-700">
              386SX @ 20 MHz · Full 640x480 VGA Plasma
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-400 max-w-3xl">
            The ultimate specimen of the GRiDCase lineage: featuring the edge-to-edge 640×480 VGA 16-shade amber gas-plasma panel,
            patented <strong>IsoPoint</strong> roller-bar pointing stick, and modular interchangeable slide-in Power Pods.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Power Pod Indicator Button */}
          <button
            onClick={() => setPowerPod((prev) => (prev === "ac" ? "battery" : "ac"))}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition ${
              powerPod === "ac"
                ? "bg-sky-500/15 border-sky-500/40 text-sky-300 hover:bg-sky-500/25"
                : "bg-emerald-500/15 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/25"
            }`}
            title="Toggle between Slide-in AC Power Pod and NiCad Battery Pod"
          >
            {powerPod === "ac" ? (
              <>
                <Plug className="h-3.5 w-3.5 text-sky-400" />
                <span>Power Pod: AC Mains</span>
              </>
            ) : (
              <>
                <Battery className="h-3.5 w-3.5 text-emerald-400" />
                <span>Power Pod: NiCad Pack</span>
              </>
            )}
          </button>

          <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/20">
            <Radio className="w-3.5 h-3.5 animate-pulse" /> Profile: gridcase1550sx_vga
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
          <div className="flex justify-between text-[10px] text-slate-400 pt-0.5">
            <button onClick={() => setLidAngle(0)} className="hover:text-amber-400">0° Closed</button>
            <button onClick={() => setLidAngle(95)} className="hover:text-amber-400">95° Typist</button>
            <button onClick={() => setLidAngle(105)} className="hover:text-amber-400">105° Normal</button>
            <button onClick={() => setLidAngle(120)} className="hover:text-amber-400">120° Wide</button>
          </div>
        </div>

        {/* Studio Spotlight Control */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-slate-300 font-medium">
            <span className="flex items-center gap-1">
              <Sun className="w-3.5 h-3.5 text-amber-400" /> Studio Spotlight
            </span>
            <span className="text-amber-400 font-mono">{spotlightIntensity.toFixed(1)}x</span>
          </div>
          <input
            type="range"
            min={0.5}
            max={12.0}
            step={0.5}
            value={spotlightIntensity}
            onChange={(e) => setSpotlightIntensity(Number(e.target.value))}
            className="w-full accent-amber-500 cursor-pointer"
          />
          <div className="flex justify-between items-center text-[10px] text-slate-400">
            <span>Soft Shadow Cast</span>
            <button
              onClick={() => setAmbientIntensity((prev) => (prev >= 1.5 ? 0.8 : 2.0))}
              className="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              Fill: {ambientIntensity}x
            </button>
          </div>
        </div>

        {/* Camera Angle Presets */}
        <div className="space-y-1.5">
          <span className="text-slate-300 font-medium block">Camera Viewpoint</span>
          <div className="grid grid-cols-2 gap-1 pt-0.5">
            <button onClick={() => setCamViewRef.current?.(0.52, 1.05, 3.3)} className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-left">Isometric</button>
            <button onClick={() => setCamViewRef.current?.(0.0, 1.15, 2.7)} className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-left">Cockpit Front</button>
            <button onClick={() => setCamViewRef.current?.(0.0, 0.22, 3.1)} className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-left">IsoPoint Deck</button>
            <button onClick={() => setCamViewRef.current?.(1.57, 1.1, 3.2)} className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-left">Rear Power Pod</button>
          </div>
        </div>

        {/* Display Mode & Fullscreen */}
        <div className="space-y-1.5">
          <span className="text-slate-300 font-medium block">Display & Fullscreen</span>
          <div className="flex gap-2">
            <button
              onClick={() => setDisplayMode("plasma")}
              className={`flex-1 py-1 rounded font-medium ${displayMode === "plasma" ? "bg-amber-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
            >
              VGA Plasma
            </button>
            <button
              onClick={() => setDisplayMode("lcd")}
              className={`flex-1 py-1 rounded font-medium ${displayMode === "lcd" ? "bg-emerald-700 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
            >
              LCD Mode
            </button>
          </div>
          <button
            onClick={toggleFullscreen}
            className="w-full py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center justify-center gap-1.5 font-medium transition"
          >
            {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
            {isFullscreen ? "Exit Fullscreen" : "Fullscreen Stage (PC Keyboard Typing)"}
          </button>
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
          style={{ height: isFullscreen ? "100vh" : 560 }}
        />

        {/* Top-Right Floating Fullscreen Button inside Canvas */}
        <button
          onClick={toggleFullscreen}
          className="absolute top-3 right-3 z-20 rounded-lg bg-slate-900/90 border border-slate-700 p-2 text-slate-300 hover:text-white shadow-lg backdrop-blur"
          title={isFullscreen ? "Exit Fullscreen" : "Toggle Fullscreen View"}
        >
          {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </button>

        {/* Floating Physical PC Keyboard Typing Pill */}
        <div className="absolute top-3 left-3 z-20 rounded-lg bg-amber-950/80 border border-amber-500/40 px-3 py-1.5 text-xs text-amber-200 backdrop-blur shadow flex items-center gap-2">
          <Terminal className="h-3.5 w-3.5 text-amber-400" />
          <span>Physical PC Keyboard: <strong>ACTIVE</strong> (Type any key to input onto plasma screen)</span>
        </div>

        {/* Bottom HUD: Interactive Plasma Terminal Quick-Sender */}
        <div className="absolute bottom-3 left-3 right-3 z-20 bg-slate-900/85 backdrop-blur-md border border-slate-700/60 p-2.5 rounded-lg flex flex-col sm:flex-row items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-mono text-amber-400 shrink-0">
            <Terminal className="w-4 h-4 text-amber-500" />
            <span>MS-DOS 5.00 Command Prompt:</span>
          </div>
          <form onSubmit={handleCommandSubmit} className="flex-1 flex gap-2 w-full">
            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="Try: DIR, VER, MEM, ISOPOINT, GRIDUTIL, EDIT, QBASIC, PRINCE, CLS"
              className="flex-1 bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-xs font-mono text-amber-300 placeholder:text-slate-600 focus:outline-none focus:border-amber-500"
            />
            <button
              type="submit"
              className="px-3 py-1 rounded bg-amber-600 hover:bg-amber-500 text-slate-950 font-semibold text-xs transition"
            >
              Execute
            </button>
          </form>
        </div>
      </div>

      {/* Technical Dossier Tabs */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-800 bg-slate-950/80 overflow-x-auto">
          <button
            onClick={() => setActiveTab("specs")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "specs"
                ? "border-amber-500 text-amber-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Cpu className="h-4 w-4 text-amber-400" />
            386SX Architecture & Specs
          </button>
          <button
            onClick={() => setActiveTab("isopoint")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "isopoint"
                ? "border-amber-500 text-amber-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Sliders className="h-4 w-4 text-sky-400" />
            IsoPoint Roller Bar
          </button>
          <button
            onClick={() => setActiveTab("powerpod")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "powerpod"
                ? "border-amber-500 text-amber-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Plug className="h-4 w-4 text-emerald-400" />
            Modular Power Pod System
          </button>
          <button
            onClick={() => setActiveTab("dos")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "dos"
                ? "border-amber-500 text-amber-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Terminal className="h-4 w-4 text-amber-400" />
            MS-DOS 5.0 & Software
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === "specs" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4">
                  <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm mb-2">
                    <Cpu className="h-4 w-4" />
                    Processor & Architecture
                  </div>
                  <ul className="text-xs text-slate-300 space-y-1.5 font-mono">
                    <li>• <span className="text-slate-400">CPU:</span> Intel 80386SX @ 20 MHz</li>
                    <li>• <span className="text-slate-400">Internal Bus:</span> 32-bit registers & ALU</li>
                    <li>• <span className="text-slate-400">External Bus:</span> 16-bit data, 24-bit address</li>
                    <li>• <span className="text-slate-400">FPU Socket:</span> Intel 80387SX coprocessor</li>
                    <li>• <span className="text-slate-400">Paging/MMU:</span> CR0/CR3 hardware paging</li>
                  </ul>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4">
                  <div className="flex items-center gap-2 text-sky-400 font-semibold text-sm mb-2">
                    <Monitor className="h-4 w-4" />
                    Full VGA Gas-Plasma Display
                  </div>
                  <ul className="text-xs text-slate-300 space-y-1.5 font-mono">
                    <li>• <span className="text-slate-400">Resolution:</span> 640 x 480 True VGA</li>
                    <li>• <span className="text-slate-400">Aspect Ratio:</span> 4:3 (fills lid edge-to-edge)</li>
                    <li>• <span className="text-slate-400">Grayscale:</span> 16-shade plasma dithering</li>
                    <li>• <span className="text-slate-400">Panel Type:</span> Matsushita neon-xenon tube</li>
                    <li>• <span className="text-slate-400">Inverter:</span> High-voltage 185V DC-AC step-up</li>
                  </ul>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4">
                  <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm mb-2">
                    <HardDrive className="h-4 w-4" />
                    Memory & Mass Storage
                  </div>
                  <ul className="text-xs text-slate-300 space-y-1.5 font-mono">
                    <li>• <span className="text-slate-400">RAM:</span> 2 MB standard (expandable to 8 MB)</li>
                    <li>• <span className="text-slate-400">Modules:</span> 30-pin SIPP 80ns with parity</li>
                    <li>• <span className="text-slate-400">Hard Drive:</span> Conner CP30104 120 MB IDE</li>
                    <li>• <span className="text-slate-400">Floppy:</span> Citizen 1.44 MB 3.5" internal</li>
                    <li>• <span className="text-slate-400">ROM:</span> 128 KB Phoenix/GRiD BIOS ROM</li>
                  </ul>
                </div>
              </div>

              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 space-y-3">
                <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-amber-400" />
                  Why the 1550 SX is the Pinnacle of the GRiDCase Series
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Released in 1990, the GRiDCase 1550 SX solved the two biggest ergonomic compromises of earlier 1500-series portables.
                  First, it replaced the letterboxed 640×400 CGA/EGA screen with a glorious, edge-to-edge <strong>640×480 VGA Gas-Plasma panel</strong> capable of rendering 16 distinct shades of amber.
                  Second, it replaced external serial mice with the built-in <strong>IsoPoint roller bar</strong>, allowing full point-and-click graphical operation in early Windows 3.0 and AutoCAD right from your lap.
                </p>
              </div>
            </div>
          )}

          {activeTab === "isopoint" && (
            <div className="space-y-4">
              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 space-y-3">
                <h4 className="text-sm font-semibold text-sky-400 flex items-center gap-2">
                  <Sliders className="h-4 w-4" />
                  The IsoPoint Mechanism: Before the Trackpad Existed
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Invented by Craig Culver and licensed to GRiD Systems (US Patent 4,935,728), the <strong>IsoPoint</strong> is a cylindrical straw-shaped roller bar mounted in a slot just beneath the spacebar.
                  The user can roll the bar forward and backward with their thumbs (controlling the Y-axis) and slide it left and right along its axle (controlling the X-axis).
                  Pressing down on the entire bar or on the flanking tactile buttons clicks the left and right mouse buttons.
                </p>
                <p className="text-xs text-slate-400 leading-relaxed font-mono">
                  Driver: <code className="text-sky-300">ISOPOINT.SYS</code> connected internally to UART COM3 @ 0x2E8, IRQ 3, emulating a standard Microsoft Bus Mouse.
                </p>
              </div>
            </div>
          )}

          {activeTab === "powerpod" && (
            <div className="space-y-4">
              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 space-y-3">
                <h4 className="text-sm font-semibold text-emerald-400 flex items-center gap-2">
                  <Plug className="h-4 w-4" />
                  Modular Slide-In Power Pod Engineering
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  The GRiDCase 1500 series eliminated external power bricks through its modular rear bay.
                  Both the <strong>AC Line Power Supply Pod</strong> and the <strong>Rechargeable NiCad Battery Pod</strong> shared the exact same dimensions and blind-mating rear bus connector.
                  In the office, the AC pod accepted a standard wall cord directly into the machine. In the field, users unlocked the rear slide latch, pulled the AC supply out, and inserted a fresh battery pod.
                </p>
              </div>
            </div>
          )}

          {activeTab === "dos" && (
            <div className="space-y-4">
              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 space-y-3">
                <h4 className="text-sm font-semibold text-amber-400 flex items-center gap-2">
                  <Terminal className="h-4 w-4" />
                  Operating System & Bundled Software Environment
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Shipped standard with <strong>MS-DOS 5.0 (GRiD-OEM)</strong> or <strong>GRiD-OS</strong>.
                  With its 80386SX CPU and full 640×480 VGA display, the 1550 SX was one of the first portable machines to comfortably run <strong>Microsoft Windows 3.0 / 3.1</strong> in 386 Enhanced Mode, Lotus 1-2-3 Release 3, and early 32-bit CAD software.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500 pt-2 border-t border-slate-800/80">
        <div className="flex items-center gap-1.5">
          <Info className="h-3.5 w-3.5 text-slate-400" />
          <span>Specimen: <span className="font-mono text-slate-300">GRiDCase 1550 SX</span> · Serial/Plate: <span className="font-mono text-slate-300">1550-SX-VGA-PLASMA</span></span>
        </div>
        <div className="font-mono text-slate-500">
          Companion: <span className="text-slate-400">hardware-grid.tsx (1520)</span> · <span className="text-slate-400">hardware-m1.tsx (M1 Synth)</span>
        </div>
      </div>
    </div>
  );
}
