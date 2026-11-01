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
  Sliders,
  Info,
  Calculator,
  Table,
  FileText,
  Volume2,
  VolumeX,
} from "lucide-react";

/**
 * Hardware HP 200LX Palmtop PC (1994).
 * Intel 80186-compatible "Hornet" SoC @ 7.91 MHz, 3MB ROM with MS-DOS 5.0 & Lotus 1-2-3,
 * 640x200 CGA Transflective Monochrome LCD, 80-key QWERTY keyboard with blue application keys,
 * PCMCIA Type II slot, and dual AA battery operation (30-40 hours runtime).
 */

type AppMode = "lotus" | "calc" | "dos" | "filer" | "memo";

const LOTUS_SAMPLE_SHEET = [
  "A1: [W12] 'EXPENSE_LOG           HP 200LX LOTUS 1-2-3 REL 2.4",
  "       A            B            C            D            E",
  "1  EXPENSE_LOG   CATEGORY      BUDGET       ACTUAL       VARIANCE",
  "2  ───────────   ────────      ──────       ──────       ────────",
  "3  HardDrive     Storage       $180.00      $165.00       +$15.00",
  "4  CF-PCMCIA     Adapter        $35.00       $29.50        +$5.50",
  "5  CR2032 x5     BackupCell     $12.00        $9.80        +$2.20",
  "6  EneloopPro    AA-NiMH x4     $24.00       $22.00        +$2.00",
  "7  SerialCable   HP-F1015A      $45.00       $45.00         $0.00",
  "8  ───────────   ────────      ──────       ──────       ────────",
  "9  TOTAL:        @SUM(C3..C7)  $296.00      $271.30       +$24.70",
  "10 NET BALANCE:  $1,248.50     READY",
];

const CALC_REGISTERS = [
  "┌──────────────────────────────────────────────────────────────┐",
  "│  HEWLETT PACKARD 19BII BUSINESS CONSULTANT II (EMULATION)    │",
  "│  FINANCIAL / RPN MODE ACTIVE                  BATTERY: GOOD  │",
  "├──────────────────────────────────────────────────────────────┤",
  "│  N = 360.00       (Loan Term Months)                         │",
  "│  I%YR = 6.25%     (Annual Interest Rate)                     │",
  "│  PV = $250,000.00 (Present Value / Principal)                │",
  "│  PMT = -$1,539.29 (Monthly Payment P&I)                      │",
  "│  FV = $0.00       (Future Value at Maturity)                 │",
  "├──────────────────────────────────────────────────────────────┤",
  "│  REGISTER STACK:                                             │",
  "│  Z: 144.00000000                                             │",
  "│  Y:  12.00000000                                             │",
  "│  X:   1,539.29412                                            │",
  "└──────────────────────────────────────────────────────────────┘",
];

const DOS_DEFAULT_LINES = [
  "HP 200LX BIOS Version 1.02A (C) Copyright Hewlett-Packard 1994",
  "Hornet 80186-compatible CPU @ 7.91 MHz (CMOS)",
  "2048 KB RAM Available, 3072 KB System ROM (Drive D:)",
  "PCMCIA Card Controller Active (Socket 1: ATA/CF 512MB Mounted on A:)",
  "MS-DOS Version 5.00 (HP Palmtop OEM)",
  "System Manager V1.02 Installed. Press blue keys to switch applications.",
  "",
  "D:\\> DIR A:",
  " Volume in drive A is HP200LX_CF",
  " Volume Serial Number is 1994-0824",
  " Directory of A:\\",
  "",
  " LOTUS24  WK1     48,128 08-24-94  10:15a",
  " PALMTOP  DAT     12,288 09-02-94   2:40p",
  " PROCOMM  EXE    142,336 04-12-93   4:20p",
  " QUICKEN  EXE    215,040 06-18-94   8:00a",
  "         4 file(s)        417,792 bytes",
  "                    536,412,160 bytes free",
  "",
  "D:\\> _",
];

export function HardwareHp200lx() {
  const mountRef = useRef<HTMLDivElement>(null);
  const stageContainerRef = useRef<HTMLDivElement>(null);

  const [appMode, setAppMode] = useState<AppMode>("lotus");
  const [screenLines, setScreenLines] = useState<string[]>(LOTUS_SAMPLE_SHEET);
  const [currentPrompt, setCurrentPrompt] = useState<string>("");
  const [commandInput, setCommandInput] = useState<string>("");
  const [lidAngle, setLidAngle] = useState<number>(115);
  const [contrast, setContrast] = useState<number>(85); // 0 to 100
  const [spotlightIntensity, setSpotlightIntensity] = useState<number>(5.5);
  const ambientIntensity = 1.6;
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [overclockMode, setOverclockMode] = useState<boolean>(false); // 7.91 MHz vs 15.8 MHz
  const [activeTab, setActiveTab] = useState<"silicon" | "lotus" | "battery" | "cult">("silicon");

  const lidAngleRef = useRef(lidAngle);
  lidAngleRef.current = lidAngle;
  const contrastRef = useRef(contrast);
  contrastRef.current = contrast;

  const lidGroupRef = useRef<THREE.Group | null>(null);
  const screenCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const screenTextureRef = useRef<THREE.CanvasTexture | null>(null);
  const spotLightRef = useRef<THREE.SpotLight | null>(null);
  const fillSpotRef = useRef<THREE.SpotLight | null>(null);
  const ambientLightRef = useRef<THREE.AmbientLight | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

  // Play authentic HP 200LX piezo buzzer beep
  const playPiezoBeep = useCallback((freq = 2400, durationSec = 0.015) => {
    if (!soundEnabled) return;
    try {
      if (!audioCtxRef.current) {
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        audioCtxRef.current = new AudioCtx();
      }
      if (audioCtxRef.current.state === "suspended") {
        audioCtxRef.current.resume();
      }
      const ctx = audioCtxRef.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "square";
      osc.frequency.setValueAtTime(freq, ctx.currentTime);

      gain.gain.setValueAtTime(0.04, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + durationSec);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + durationSec);
    } catch {}
  }, [soundEnabled]);

  // Switch between HP 200LX ROM Applications
  const switchApp = (mode: AppMode) => {
    setAppMode(mode);
    playPiezoBeep(mode === "calc" ? 3200 : mode === "lotus" ? 2400 : 1800, 0.02);
    if (mode === "lotus") {
      setScreenLines(LOTUS_SAMPLE_SHEET);
      setCurrentPrompt("");
    } else if (mode === "calc") {
      setScreenLines(CALC_REGISTERS);
      setCurrentPrompt("");
    } else if (mode === "dos") {
      setScreenLines(DOS_DEFAULT_LINES);
      setCurrentPrompt("D:\\> ");
    } else if (mode === "filer") {
      setScreenLines([
        "┌─ FILER: A:\\ (PCMCIA ATA FLASH) ───────────────┬─ C:\\ (RAM DISK) ─────────────┐",
        "│ LOTUS24.WK1    48,128  08-24-94  10:15a        │ AUTOEXEC.BAT       218 08-24 │",
        "│ PALMTOP.DAT    12,288  09-02-94   2:40p        │ CONFIG.SYS         142 08-24 │",
        "│ PROCOMM.EXE   142,336  04-12-93   4:20p        │ APPT.DAT         8,192 10-31 │",
        "│ QUICKEN.EXE   215,040  06-18-94   8:00a        │ PHONE.DAT        4,096 10-31 │",
        "│ TURBO.EXE     184,320  11-05-92   1:10p        │ MEMO.DAT         2,048 10-31 │",
        "├────────────────────────────────────────────────┴──────────────────────────────┤",
        "│ [F1 Help]  [F2 Copy]  [F3 Move]  [F4 Delete]  [F5 Rename]  [F9 View]  [F10 Quit]  │",
        "└───────────────────────────────────────────────────────────────────────────────┘",
      ]);
      setCurrentPrompt("");
    } else if (mode === "memo") {
      setScreenLines([
        "MEMO: FIELD_DIARY.TXT ─────────────────────────────────────────── [INSERT MODE]",
        "",
        "DATE: 31-OCT-2026",
        "STATION: FLEET REVERSING WORKSHOP",
        "HARDWARE: HEWLETT PACKARD 200LX PALMTOP PC",
        "",
        "Observed: The 200LX remains the ultimate offline portable computing artifact.",
        "Running full MS-DOS 5.0 with Lotus 1-2-3 in ROM on two AA batteries.",
        "Equipped with 512MB CompactFlash in PCMCIA slot via passive adapter.",
        "All telemetry records logged. Crystal mod verified stable at 15.8 MHz.",
        "",
        "─── [F1 Help] ─── [F2 Save] ─── [F3 Search] ─── [F10 Exit] ───────────────────",
      ]);
      setCurrentPrompt("");
    }
  };

  // Fullscreen Handler
  const toggleFullscreen = () => {
    if (!stageContainerRef.current) return;
    if (!document.fullscreenElement) {
      stageContainerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  useEffect(() => {
    const onFs = () => setIsFullscreen(document.fullscreenElement === stageContainerRef.current);
    document.addEventListener("fullscreenchange", onFs);
    return () => document.removeEventListener("fullscreenchange", onFs);
  }, []);

  // Update 2D Canvas & 3D Texture whenever Screen Content or Contrast changes
  useEffect(() => {
    const canvas = screenCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // HP 200LX Monochrome Transflective LCD Palette
    // Contrast slider shifts background from washed light-olive to rich deep tone
    const contrastRatio = contrast / 100;
    const bgR = Math.round(138 * (1.15 - contrastRatio * 0.3));
    const bgG = Math.round(154 * (1.15 - contrastRatio * 0.25));
    const bgB = Math.round(122 * (1.15 - contrastRatio * 0.3));
    const bgColor = `rgb(${bgR}, ${bgG}, ${bgB})`;

    // Pixel color
    const darkIntensity = Math.round(18 + (1 - contrastRatio) * 60);
    const pixelColor = `rgb(${darkIntensity}, ${darkIntensity + 8}, ${darkIntensity})`;

    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Subtle LCD pixel dot grid / texture simulation
    ctx.fillStyle = "rgba(0, 0, 0, 0.03)";
    for (let y = 0; y < canvas.height; y += 4) {
      ctx.fillRect(0, y, canvas.width, 1);
    }

    // Top Status Header (HP 200LX System Manager banner)
    ctx.fillStyle = pixelColor;
    ctx.fillRect(0, 0, canvas.width, 18);
    ctx.fillStyle = bgColor;
    ctx.font = "bold 13px Courier, monospace";
    const appTitles: Record<AppMode, string> = {
      lotus: "1-2-3  [LOTUS 1-2-3 REL 2.4 IN ROM]   HP 200LX   [F10=MENU]",
      calc: "CALC   [HP 19BII FINANCIAL CONSULTANT] HP 200LX   [RPN/ALG]",
      dos: "DOS    [MS-DOS 5.00 COMMAND PROMPT]    HP 200LX   [D:\\DOS]",
      filer: "FILER  [PCMCIA ATA / RAM DUAL BROWSER] HP 200LX   [A: <-> C:]",
      memo: "MEMO   [TEXT EDITOR & FIELD NOTES]     HP 200LX   [INSERT]",
    };
    ctx.fillText(appTitles[appMode], 10, 14);

    // Screen text rendering (640x200 CGA 80x25 character grid)
    ctx.fillStyle = pixelColor;
    ctx.font = "14px Courier, monospace";
    const lineHeight = 19;
    const startY = 38;

    screenLines.forEach((line, idx) => {
      ctx.fillText(line, 10, startY + idx * lineHeight);
    });

    if (currentPrompt) {
      const pIdx = screenLines.length;
      ctx.fillText(currentPrompt + commandInput + "_", 10, startY + pIdx * lineHeight);
    }

    if (screenTextureRef.current) {
      screenTextureRef.current.needsUpdate = true;
    }
  }, [screenLines, currentPrompt, commandInput, contrast, appMode]);

  // Execute MS-DOS Command when in DOS mode
  const executeCommand = (cmdStr: string) => {
    playPiezoBeep(1800, 0.02);
    const cmd = cmdStr.trim().toUpperCase();
    const newLines = [...screenLines];
    newLines.push(`D:\\> ${cmdStr}`);

    if (cmd === "CLS") {
      setScreenLines([]);
      setCommandInput("");
      return;
    }

    if (cmd === "VER") {
      newLines.push("MS-DOS Version 5.00 (Hewlett-Packard Palmtop Edition)");
      newLines.push("Hornet SoC Core Rev 1.02, 80186-compatible static CMOS");
    } else if (cmd === "DIR" || cmd === "DIR A:" || cmd === "DIR D:") {
      newLines.push(" Volume in drive D is HP_SYS_ROM");
      newLines.push(" Directory of D:\\");
      newLines.push(" 123      EXE    184,320 08-24-94   2:00p");
      newLines.push(" CALC     EXE     92,160 08-24-94   2:00p");
      newLines.push(" FILER    EXE     64,512 08-24-94   2:00p");
      newLines.push(" MEMO     EXE     48,128 08-24-94   2:00p");
      newLines.push(" PHONE    EXE     52,224 08-24-94   2:00p");
      newLines.push(" COMMAND  COM     47,845 08-24-94   2:00p");
      newLines.push("         6 file(s)        489,189 bytes");
      newLines.push("                    2,097,152 bytes free on C:");
    } else if (cmd === "MEM") {
      newLines.push("   655,360 bytes total conventional memory");
      newLines.push("   655,360 bytes available to MS-DOS");
      newLines.push("   582,144 largest executable program size");
      newLines.push(" 1,441,792 bytes total contiguous extended memory");
      newLines.push(" 1,441,792 bytes available continuous extended memory");
    } else if (cmd === "123" || cmd === "LOTUS") {
      switchApp("lotus");
      setCommandInput("");
      return;
    } else if (cmd === "CALC") {
      switchApp("calc");
      setCommandInput("");
      return;
    } else if (cmd === "FILER") {
      switchApp("filer");
      setCommandInput("");
      return;
    } else if (cmd === "MEMO") {
      switchApp("memo");
      setCommandInput("");
      return;
    } else if (cmd === "SPEED") {
      newLines.push(overclockMode ? "CPU Clock: 15.82 MHz (Double-Speed Mod Active)" : "CPU Clock: 7.91 MHz (Standard Crystal)");
    } else if (cmd === "HELP") {
      newLines.push("Available Commands: DIR, MEM, VER, CLS, 123, CALC, FILER, MEMO, SPEED, HELP");
    } else if (cmd !== "") {
      newLines.push(`Bad command or file name: ${cmdStr}`);
    }

    setScreenLines(newLines.slice(-18));
    setCommandInput("");
  };

  // Keyboard capture: Physical typing streams into HP 200LX terminal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      playPiezoBeep(1200 + Math.random() * 600, 0.008);

      if (e.key === "Enter") {
        e.preventDefault();
        executeCommand(commandInput);
      } else if (e.key === "Backspace") {
        e.preventDefault();
        setCommandInput((prev) => prev.slice(0, -1));
      } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        setCommandInput((prev) => prev + e.key);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [commandInput, playPiezoBeep]);

  // ==========================================
  // THREE.JS 3D PALMTOP PC WORKSTATION BUILDER
  // ==========================================
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0c10);

    const camera = new THREE.PerspectiveCamera(40, mount.clientWidth / mount.clientHeight, 0.1, 100);
    camera.position.set(0, 2.8, 3.8);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    mount.appendChild(renderer.domElement);

    // 2. Lighting Rig
    const ambientLight = new THREE.AmbientLight(0xffffff, ambientIntensity);
    scene.add(ambientLight);
    ambientLightRef.current = ambientLight;

    const spotLight = new THREE.SpotLight(0xfff5e6, spotlightIntensity);
    spotLight.position.set(2.5, 5.0, 2.5);
    spotLight.angle = 0.6;
    spotLight.penumbra = 0.5;
    spotLight.castShadow = true;
    spotLight.shadow.mapSize.width = 1024;
    spotLight.shadow.mapSize.height = 1024;
    scene.add(spotLight);
    spotLightRef.current = spotLight;

    const fillSpot = new THREE.SpotLight(0x7dd3fc, spotlightIntensity * 0.45);
    fillSpot.position.set(-3.5, 3.0, 2.0);
    fillSpot.angle = 0.8;
    fillSpot.penumbra = 0.6;
    scene.add(fillSpot);
    fillSpotRef.current = fillSpot;

    // Desk Pad
    const deskGeo = new THREE.PlaneGeometry(16, 12);
    const deskMat = new THREE.MeshStandardMaterial({
      color: 0x12141a,
      roughness: 0.9,
      metalness: 0.1,
    });
    const desk = new THREE.Mesh(deskGeo, deskMat);
    desk.rotation.x = -Math.PI / 2;
    desk.position.y = -0.01;
    desk.receiveShadow = true;
    scene.add(desk);

    // 3. Materials
    const palmtopDarkMat = new THREE.MeshStandardMaterial({
      color: 0x22262c,
      roughness: 0.65,
      metalness: 0.15,
    });

    const palmtopLidMat = new THREE.MeshStandardMaterial({
      color: 0x1d2127,
      roughness: 0.6,
      metalness: 0.2,
    });

    const keyGreyMat = new THREE.MeshStandardMaterial({
      color: 0x3a3f47,
      roughness: 0.5,
      metalness: 0.1,
    });

    const blueKeyMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7, // HP Blue application key
      roughness: 0.4,
      metalness: 0.1,
    });

    const irdaWindowMat = new THREE.MeshStandardMaterial({
      color: 0x450a0a, // Dark red IrDA window
      roughness: 0.2,
      metalness: 0.8,
      transparent: true,
      opacity: 0.85,
    });

    // Root Group
    const palmtopGroup = new THREE.Group();
    scene.add(palmtopGroup);

    // ------------------------------------------
    // A. LOWER TUB (Base Chassis ~160 x 86 x 14 mm)
    // ------------------------------------------
    const baseW = 2.8;
    const baseD = 1.5;
    const baseH = 0.18;

    const baseGeo = new THREE.BoxGeometry(baseW, baseH, baseD);
    const baseMesh = new THREE.Mesh(baseGeo, palmtopDarkMat);
    baseMesh.position.set(0, baseH / 2, 0);
    baseMesh.castShadow = true;
    baseMesh.receiveShadow = true;
    palmtopGroup.add(baseMesh);

    // PCMCIA Slot on Left
    const pcmciaGeo = new THREE.BoxGeometry(0.04, 0.08, 0.9);
    const pcmciaMat = new THREE.MeshStandardMaterial({ color: 0x111317, roughness: 0.9 });
    const pcmcia = new THREE.Mesh(pcmciaGeo, pcmciaMat);
    pcmcia.position.set(-baseW / 2 + 0.01, baseH / 2, 0.05);
    palmtopGroup.add(pcmcia);

    // PCMCIA Eject Button
    const pcmciaBtnGeo = new THREE.BoxGeometry(0.05, 0.04, 0.12);
    const pcmciaBtnMat = new THREE.MeshStandardMaterial({ color: 0x475569 });
    const pcmciaBtn = new THREE.Mesh(pcmciaBtnGeo, pcmciaBtnMat);
    pcmciaBtn.position.set(-baseW / 2 + 0.02, baseH / 2, -0.45);
    palmtopGroup.add(pcmciaBtn);

    // Serial Port (10-pin) & DC Jack on Right
    const serialGeo = new THREE.BoxGeometry(0.04, 0.06, 0.35);
    const serialPort = new THREE.Mesh(serialGeo, pcmciaMat);
    serialPort.position.set(baseW / 2 - 0.01, baseH / 2, -0.2);
    palmtopGroup.add(serialPort);

    // IrDA Window on Rear Edge
    const irdaGeo = new THREE.BoxGeometry(0.35, 0.06, 0.03);
    const irda = new THREE.Mesh(irdaGeo, irdaWindowMat);
    irda.position.set(-0.6, baseH / 2 + 0.02, -baseD / 2);
    palmtopGroup.add(irda);

    // ------------------------------------------
    // B. KEYBOARD DECK (80-Key Chiclet Array)
    // ------------------------------------------
    const keyRows = 6;
    const keyCols = 15;
    const keyW = 0.14;
    const keyD = 0.12;
    const keyH = 0.04;
    const keySpacingX = 0.165;
    const keySpacingZ = 0.145;

    const startKeyX = -baseW / 2 + 0.25;
    const startKeyZ = -baseD / 2 + 0.28;

    for (let r = 0; r < keyRows; r++) {
      for (let c = 0; c < keyCols; c++) {
        // Dedicated blue keys for top row & app keys
        const isBlueKey = r === 0 && (c >= 2 && c <= 9);
        const mat = isBlueKey ? blueKeyMat : keyGreyMat;

        const kGeo = new THREE.BoxGeometry(keyW, keyH, keyD);
        const keyMesh = new THREE.Mesh(kGeo, mat);
        keyMesh.position.set(
          startKeyX + c * keySpacingX,
          baseH + keyH / 2,
          startKeyZ + r * keySpacingZ
        );
        keyMesh.castShadow = true;
        palmtopGroup.add(keyMesh);
      }
    }

    // ------------------------------------------
    // C. HINGED DISPLAY LID (640x200 CGA LCD)
    // ------------------------------------------
    const hingeGroup = new THREE.Group();
    hingeGroup.position.set(0, baseH, -baseD / 2);
    palmtopGroup.add(hingeGroup);
    lidGroupRef.current = hingeGroup;

    // Lid Bezel
    const lidW = baseW;
    const lidD = baseD;
    const lidH = 0.12;

    const lidMeshGeo = new THREE.BoxGeometry(lidW, lidH, lidD);
    const lidMesh = new THREE.Mesh(lidMeshGeo, palmtopLidMat);
    lidMesh.position.set(0, 0, lidD / 2);
    lidMesh.castShadow = true;
    hingeGroup.add(lidMesh);

    // HP Badge on outer lid / bezel
    const hpBadgeGeo = new THREE.BoxGeometry(0.3, 0.01, 0.08);
    const hpBadgeMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.6 });
    const hpBadge = new THREE.Mesh(hpBadgeGeo, hpBadgeMat);
    hpBadge.position.set(-lidW / 2 + 0.35, lidH / 2 + 0.005, lidD / 2 - 0.55);
    hingeGroup.add(hpBadge);

    // 2D Offscreen Canvas for Real-Time LCD Rendering (640x200 Aspect)
    const canvas = document.createElement("canvas");
    canvas.width = 640;
    canvas.height = 200;
    screenCanvasRef.current = canvas;

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    screenTextureRef.current = texture;

    // LCD Screen Plane
    const screenW = baseW * 0.82;
    const screenD = screenW * (200 / 640); // Exact 640x200 CGA aspect
    const screenGeo = new THREE.PlaneGeometry(screenW, screenD);
    const screenMat = new THREE.MeshBasicMaterial({
      map: texture,
    });
    const screenMesh = new THREE.Mesh(screenGeo, screenMat);
    screenMesh.rotation.x = -Math.PI / 2;
    screenMesh.position.set(0, lidH / 2 + 0.005, lidD / 2 - 0.05);
    hingeGroup.add(screenMesh);

    // Initial Lid Angle
    const rad = (lidAngleRef.current * Math.PI) / 180;
    hingeGroup.rotation.x = rad;

    // 4. Interactive Orbit Controls (Mouse Drag)
    let isMouseDown = false;
    let prevMouse = { x: 0, y: 0 };
    let theta = 0;
    let phi = 0.65;
    let radius = 3.6;

    const updateCam = () => {
      camera.position.x = radius * Math.sin(phi) * Math.sin(theta);
      camera.position.y = radius * Math.cos(phi);
      camera.position.z = radius * Math.sin(phi) * Math.cos(theta);
      camera.lookAt(0, 0.1, 0);
    };
    updateCam();

    const onMouseDown = (e: MouseEvent) => {
      isMouseDown = true;
      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isMouseDown) return;
      const dx = e.clientX - prevMouse.x;
      const dy = e.clientY - prevMouse.y;
      prevMouse = { x: e.clientX, y: e.clientY };

      theta -= dx * 0.008;
      phi = Math.max(0.15, Math.min(Math.PI / 2 - 0.05, phi - dy * 0.008));
      updateCam();
    };

    const onMouseUp = () => {
      isMouseDown = false;
    };

    const onWheel = (e: WheelEvent) => {
      radius = Math.max(1.8, Math.min(6.5, radius + e.deltaY * 0.003));
      updateCam();
    };

    const dom = renderer.domElement;
    dom.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    dom.addEventListener("wheel", onWheel);

    const onResize = () => {
      if (!mount) return;
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener("resize", onResize);

    // 5. Animation Loop
    let rafId: number;
    const animate = () => {
      rafId = requestAnimationFrame(animate);
      if (lidGroupRef.current) {
        const targetRad = (lidAngleRef.current * Math.PI) / 180;
        lidGroupRef.current.rotation.x = THREE.MathUtils.lerp(lidGroupRef.current.rotation.x, targetRad, 0.1);
      }
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(rafId);
      dom.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      dom.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, []);

  // Sync spot light slider
  useEffect(() => {
    if (spotLightRef.current) spotLightRef.current.intensity = spotlightIntensity;
    if (fillSpotRef.current) fillSpotRef.current.intensity = spotlightIntensity * 0.45;
  }, [spotlightIntensity]);

  return (
    <div className="space-y-8 p-4 max-w-7xl mx-auto">
      {/* 1. Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">📟</span>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Hewlett Packard 200LX Palmtop PC (1994)
            </h1>
            <span className="rounded bg-sky-950 px-2 py-0.5 font-mono text-xs text-sky-400 border border-sky-800">
              Hornet 80186 @ {overclockMode ? "15.8 MHz (Modded)" : "7.91 MHz"}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            The legendary pocket-sized MS-DOS 5.0 computer: 3MB ROM with Lotus 1-2-3 & HP 19BII Calculator,
            640×200 CGA transflective LCD, PCMCIA Type II slot, and 40 hours of continuous runtime on two AA batteries.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => {
              setOverclockMode(!overclockMode);
              playPiezoBeep(overclockMode ? 1400 : 2800, 0.02);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition flex items-center gap-1.5 ${
              overclockMode
                ? "bg-amber-500/20 border-amber-500 text-amber-300"
                : "bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200"
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>{overclockMode ? "15.8 MHz (Double Crystal)" : "7.91 MHz (Stock)"}</span>
          </button>

          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title={soundEnabled ? "Mute Piezo Buzzer" : "Enable Piezo Buzzer"}
          >
            {soundEnabled ? <Volume2 className="h-4 w-4 text-sky-400" /> : <VolumeX className="h-4 w-4 text-slate-500" />}
          </button>
        </div>
      </div>

      {/* 2. Interactive 3D Studio & Live Palmtop Workspace */}
      <div
        ref={stageContainerRef}
        className={`relative rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl transition-all ${
          isFullscreen ? "fixed inset-0 z-50 rounded-none border-0" : ""
        }`}
      >
        {/* Studio Control Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 bg-slate-900/90 px-4 py-3">
          <div className="flex items-center gap-2 text-xs text-slate-300">
            <Monitor className="h-4 w-4 text-sky-400" />
            <span className="font-semibold text-slate-200">HP 200LX 3D Studio</span>
            <span className="font-mono text-slate-500">|</span>
            <span className="text-slate-400">Click &amp; drag to orbit · Scroll to zoom</span>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs">
            {/* Clamshell Lid Angle */}
            <div className="flex items-center gap-2 text-slate-300">
              <span className="text-slate-400">Hinge:</span>
              <input
                type="range"
                min="0"
                max="135"
                value={lidAngle}
                onChange={(e) => setLidAngle(parseInt(e.target.value))}
                className="w-20 accent-sky-400 h-1.5 bg-slate-700 rounded-lg cursor-pointer"
              />
              <span className="font-mono text-slate-300 w-8">{lidAngle}°</span>
            </div>

            {/* LCD Rotary Contrast Slider */}
            <div className="flex items-center gap-2 text-slate-300">
              <Sliders className="h-3.5 w-3.5 text-amber-400" />
              <span className="text-slate-400">Contrast:</span>
              <input
                type="range"
                min="20"
                max="100"
                value={contrast}
                onChange={(e) => setContrast(parseInt(e.target.value))}
                className="w-20 accent-amber-400 h-1.5 bg-slate-700 rounded-lg cursor-pointer"
              />
              <span className="font-mono text-slate-300 w-7">{contrast}%</span>
            </div>

            {/* Transflective LCD Illumination Lamp */}
            <div className="flex items-center gap-2 text-slate-300">
              <Sun className="h-3.5 w-3.5 text-amber-300" />
              <span className="text-slate-400">Lamp:</span>
              <input
                type="range"
                min="1.0"
                max="10.0"
                step="0.5"
                value={spotlightIntensity}
                onChange={(e) => setSpotlightIntensity(parseFloat(e.target.value))}
                className="w-16 accent-amber-300 h-1.5 bg-slate-700 rounded-lg cursor-pointer"
                title="Simulate ambient desk lamp aimed at the reflective LCD matrix"
              />
            </div>

            {/* Fullscreen Button */}
            <button
              onClick={toggleFullscreen}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen 3D Studio"}
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* 3D WebGL Canvas */}
        <div
          ref={mountRef}
          className={`w-full cursor-grab active:cursor-grabbing ${isFullscreen ? "h-[calc(100vh-120px)]" : "h-[480px]"}`}
        />

        {/* Dedicated Blue Function Launch Keys Bar */}
        <div className="border-t border-slate-800 bg-slate-900/90 px-4 py-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            <span className="text-xs font-mono text-sky-400 font-bold mr-1">ROM APPS:</span>
            <button
              onClick={() => switchApp("lotus")}
              className={`px-3 py-1 rounded text-xs font-bold transition flex items-center gap-1.5 ${
                appMode === "lotus"
                  ? "bg-sky-500 text-slate-950 shadow"
                  : "bg-sky-950/60 text-sky-300 border border-sky-800/60 hover:bg-sky-900/40"
              }`}
            >
              <Table className="h-3.5 w-3.5" />
              <span>Lotus 1-2-3</span>
            </button>

            <button
              onClick={() => switchApp("calc")}
              className={`px-3 py-1 rounded text-xs font-bold transition flex items-center gap-1.5 ${
                appMode === "calc"
                  ? "bg-sky-500 text-slate-950 shadow"
                  : "bg-sky-950/60 text-sky-300 border border-sky-800/60 hover:bg-sky-900/40"
              }`}
            >
              <Calculator className="h-3.5 w-3.5" />
              <span>HP 19BII Calc</span>
            </button>

            <button
              onClick={() => switchApp("dos")}
              className={`px-3 py-1 rounded text-xs font-bold transition flex items-center gap-1.5 ${
                appMode === "dos"
                  ? "bg-sky-500 text-slate-950 shadow"
                  : "bg-sky-950/60 text-sky-300 border border-sky-800/60 hover:bg-sky-900/40"
              }`}
            >
              <Terminal className="h-3.5 w-3.5" />
              <span>MS-DOS 5.0</span>
            </button>

            <button
              onClick={() => switchApp("filer")}
              className={`px-3 py-1 rounded text-xs font-bold transition flex items-center gap-1.5 ${
                appMode === "filer"
                  ? "bg-sky-500 text-slate-950 shadow"
                  : "bg-sky-950/60 text-sky-300 border border-sky-800/60 hover:bg-sky-900/40"
              }`}
            >
              <HardDrive className="h-3.5 w-3.5" />
              <span>Filer / PCMCIA</span>
            </button>

            <button
              onClick={() => switchApp("memo")}
              className={`px-3 py-1 rounded text-xs font-bold transition flex items-center gap-1.5 ${
                appMode === "memo"
                  ? "bg-sky-500 text-slate-950 shadow"
                  : "bg-sky-950/60 text-sky-300 border border-sky-800/60 hover:bg-sky-900/40"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Memo &amp; Notes</span>
            </button>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <Battery className="h-4 w-4 text-emerald-400" />
            <span>2x AA: 2.84V (36h Left)</span>
            <span className="text-slate-600">|</span>
            <span>CR2032: 3.12V OK</span>
          </div>
        </div>
      </div>

      {/* 3. Interactive DOS / App Keyboard Console */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <Terminal className="h-4 w-4 text-sky-400" />
            <span>Interactive Terminal Keystrokes &amp; Command Injection</span>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Type directly on your PC keyboard or enter commands below
          </span>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            executeCommand(commandInput);
          }}
          className="flex gap-2"
        >
          <div className="relative flex-1">
            <span className="absolute left-3 top-2.5 font-mono text-xs text-sky-400 font-bold">
              {appMode === "dos" ? "D:\\>" : `[${appMode.toUpperCase()}] >`}
            </span>
            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="Type command (DIR, MEM, 123, CALC, SPEED, HELP) or type on screen..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-24 pr-4 py-2 font-mono text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-slate-950 font-bold rounded-lg text-xs transition"
          >
            Send ScanCode
          </button>
        </form>
      </div>

      {/* 4. Technical Dossiers & Reversing Tabs */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-800 bg-slate-950/80 overflow-x-auto">
          <button
            onClick={() => setActiveTab("silicon")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "silicon"
                ? "border-sky-500 text-sky-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Cpu className="h-4 w-4 text-sky-400" />
            Hornet SoC &amp; Architecture
          </button>

          <button
            onClick={() => setActiveTab("lotus")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "lotus"
                ? "border-sky-500 text-sky-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <BookOpen className="h-4 w-4 text-indigo-400" />
            Lotus 1-2-3 in ROM
          </button>

          <button
            onClick={() => setActiveTab("battery")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "battery"
                ? "border-sky-500 text-sky-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Battery className="h-4 w-4 text-emerald-400" />
            AA Power &amp; Mods
          </button>

          <button
            onClick={() => setActiveTab("cult")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "cult"
                ? "border-sky-500 text-sky-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Radio className="h-4 w-4 text-amber-400" />
            Field Cult &amp; Ham Radio
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* TAB 1: SILICON & HARDWARE ARCHITECTURE */}
          {activeTab === "silicon" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-1">
                  <div className="text-sky-400 font-semibold text-sm">Processor: HP "Hornet" SoC</div>
                  <p className="text-xs text-slate-300 leading-relaxed font-mono">
                    Intel 80186-compatible static CMOS core @ 7.91 MHz. Integrates DMA, timers, interrupt controller,
                    and LCD driver into a single low-power ASIC consuming only ~100mW.
                  </p>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-1">
                  <div className="text-sky-400 font-semibold text-sm">Display: 640×200 CGA Transflective</div>
                  <p className="text-xs text-slate-300 leading-relaxed font-mono">
                    Monochrome LCD supporting 80 cols × 25 rows or 40×16 zoom. Sunlight readable with high contrast;
                    rotary side dial shifts voltage potential without requiring power-hungry backlights.
                  </p>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-1">
                  <div className="text-sky-400 font-semibold text-sm">Storage: PCMCIA &amp; 3MB ROM</div>
                  <p className="text-xs text-slate-300 leading-relaxed font-mono">
                    16-bit PCMCIA Type II slot supports CompactFlash cards up to 2GB via passive adapter.
                    3MB mask ROM holds MS-DOS 5.0, Lotus 1-2-3, Pocket Quicken, and System Manager.
                  </p>
                </div>
              </div>

              {/* Hardware Spec Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border border-slate-800 rounded-lg overflow-hidden">
                  <thead className="bg-slate-950 text-slate-300 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Subsystem</th>
                      <th className="py-2.5 px-3 font-semibold">Specification</th>
                      <th className="py-2.5 px-3 font-semibold">Memory Map / Ports</th>
                      <th className="py-2.5 px-3 font-semibold">Technical Note</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Core CPU</td>
                      <td className="py-2 px-3 text-amber-300">Intel 80186 "Hornet" SoC</td>
                      <td className="py-2 px-3">0x00000 – 0xFFFFF</td>
                      <td className="py-2 px-3 font-sans">Overclockable to 15.82 MHz via crystal swap</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">System ROM</td>
                      <td className="py-2 px-3 text-amber-300">3 MB Mask ROM (Drive D:)</td>
                      <td className="py-2 px-3">Banked Page Windows</td>
                      <td className="py-2 px-3 font-sans">Contains DOS 5.0, 1-2-3, Quicken, cc:Mail, Memo, Calc</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Internal RAM</td>
                      <td className="py-2 px-3 text-amber-300">1 MB / 2 MB / 4 MB SRAM</td>
                      <td className="py-2 px-3">Conventional + Drive C:</td>
                      <td className="py-2 px-3 font-sans">Software split between DOS execution RAM &amp; C: RAM disk</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Expansion Bus</td>
                      <td className="py-2 px-3 text-amber-300">PCMCIA Type II (16-bit)</td>
                      <td className="py-2 px-3">Socket 1 (Drive A:)</td>
                      <td className="py-2 px-3 font-sans">Supports ATA Flash, SRAM cards with coin cell, CF cards</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Serial I/O</td>
                      <td className="py-2 px-3 text-amber-300">10-pin proprietary (COM1)</td>
                      <td className="py-2 px-3">0x3F8, IRQ 4</td>
                      <td className="py-2 px-3 font-sans">RS-232C up to 115,200 baud via HP F1015A cable</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Infrared Transceiver</td>
                      <td className="py-2 px-3 text-amber-300">HP SIR IrDA (115.2 kbps)</td>
                      <td className="py-2 px-3">Switched with COM1</td>
                      <td className="py-2 px-3 font-sans">Wireless palmtop-to-palmtop &amp; printer communication</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: LOTUS 1-2-3 IN ROM */}
          {activeTab === "lotus" && (
            <div className="space-y-4">
              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 space-y-3">
                <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Table className="h-4 w-4 text-sky-400" />
                  The Legendary ROM-Resident Lotus 1-2-3 Release 2.4
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  The crowning achievement of the HP 200LX was licensing and burning <strong>Lotus 1-2-3 Release 2.4 directly into ROM</strong>.
                  Unlike third-party mobile apps, this was the authentic, full-featured PC spreadsheet engine—capable of executing complex
                  macro routines, financial models, and full mathematical formulas without requiring a floppy disk or hard drive.
                </p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Through the HP System Manager, Lotus 1-2-3 could be suspended instantly by pressing another application key (such as the Memo or Calculator key)
                  and resumed in milliseconds without losing worksheet state, thanks to static RAM retention.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-2">
                  <span className="text-xs font-semibold text-sky-300 uppercase tracking-wider">Spreadsheet Capabilities</span>
                  <ul className="text-xs text-slate-400 space-y-1 font-mono">
                    <li>• <span className="text-slate-200">Grid Size:</span> 8,192 rows × 256 columns</li>
                    <li>• <span className="text-slate-200">File Format:</span> Native Lotus <code className="text-sky-300">.WK1</code> files</li>
                    <li>• <span className="text-slate-200">Graphics:</span> Bar, line, pie, and XY scatter charts in CGA monochrome</li>
                    <li>• <span className="text-slate-200">Formula Library:</span> Full financial, statistical, and mathematical functions</li>
                  </ul>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-2">
                  <span className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">System Manager Integration</span>
                  <ul className="text-xs text-slate-400 space-y-1 font-mono">
                    <li>• <span className="text-slate-200">Instant Task Switching:</span> Press blue <code className="text-sky-300">[1-2-3]</code> key</li>
                    <li>• <span className="text-slate-200">Clipboard Transfer:</span> Copy cells into Memo editor or Quicken</li>
                    <li>• <span className="text-slate-200">Zero Load Time:</span> Executes directly out of 3MB Mask ROM</li>
                    <li>• <span className="text-slate-200">Power Save:</span> Auto-sleep after 5 minutes with zero data loss</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: BATTERY & MODS */}
          {activeTab === "battery" && (
            <div className="space-y-4">
              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 space-y-3">
                <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Battery className="h-4 w-4 text-emerald-400" />
                  30–40 Hours of True DOS Computing on Two AA Cells
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  While modern laptops struggle to survive a workday, the HP 200LX runs for <strong>30 to 40 hours of active typing</strong> on two standard AA alkaline or Eneloop NiMH rechargeable cells.
                  The static CMOS design of the Hornet 80186 draws almost negligible power when idle, allowing the device to remain on standby for months.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-2">
                  <span className="text-xs font-semibold text-emerald-300 uppercase tracking-wider">The "Double-Speed" Crystal Mod</span>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    By default, the 200LX is clocked by a 15.82 MHz crystal (divided by 2 for a 7.91 MHz CPU clock).
                    Enthusiasts desolder the stock oscillator and install a <strong>31.64 MHz or 32 MHz crystal</strong>, doubling system throughput to ~15.8 MHz.
                    Because the Hornet chip was fabricated on high-grade static CMOS, it runs cool and reliably at 16 MHz with only a ~15% increase in battery drain.
                  </p>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-2">
                  <span className="text-xs font-semibold text-amber-300 uppercase tracking-wider">Hinge Repair &amp; Maintenance</span>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    The only physical vulnerability of the 200LX is its right display hinge casing, which can crack under torsion after decades of opening.
                    Modern preservationists install <strong>3D-printed metal or carbon hinge reinforcement clips</strong> to distribute stress across the lid tub, preserving specimen integrity.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: FIELD CULT & HAM RADIO */}
          {activeTab === "cult" && (
            <div className="space-y-4">
              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 space-y-3">
                <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Radio className="h-4 w-4 text-amber-400" />
                  The Enduring Cult: Field Telemetry &amp; Ham Radio APRS
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Decades after discontinuation, the HP 200LX maintains a fiercely loyal community among telecommunications engineers, network administrators, and amateur radio operators.
                  Because it possesses a real hardware 16550 UART serial port and native MS-DOS command interpreter, it serves as the ultimate pocket terminal for configuring routers, PBX switches, and packet radio TNC controllers in the wilderness.
                </p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  In amateur radio, operators connect the 200LX to an HT radio via an AEA PK-88 or Kantronics TNC to transmit packet messages and APRS GPS telemetry from mountain summits where no cell towers exist.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 5. Footer Info */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500 pt-2 border-t border-slate-800/80">
        <div className="flex items-center gap-1.5">
          <Info className="h-3.5 w-3.5 text-slate-400" />
          <span>Documentation sources: <span className="font-mono text-slate-400">HP 200LX User's Guide</span> · <span className="font-mono text-slate-400">The HP Palmtop Paper</span> · <span className="font-mono text-slate-400">Hornet ASIC Architecture</span></span>
        </div>
        <div className="font-mono text-slate-500">
          Emulation targets: <span className="text-slate-400">PALM186</span> · <span className="text-slate-400">DOSBox-X (640x200 CGA)</span> · <span className="text-slate-400">MAME hp200lx</span>
        </div>
      </div>
    </div>
  );
}
