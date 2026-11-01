import { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";
import {
  Cpu,
  Music,
  Sliders,
  Sun,
  Volume2,
  Layers,
  Radio,
  BookOpen,
  Play,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Info,
  Disc,
  Microchip,
  Maximize2,
  Minimize2,
  Activity,
  Search,
  Download,
} from "lucide-react";
import {
  M1_100_PROGRAMS,
  M1_100_COMBIS,
  type M1Program,
  type M1Combi,
} from "../data/korg-m1-bank";

/**
 * Hardware M1 — Korg M1 (1988) Music Workstation & KLM-1266 PCB 3D Studio.
 * Dual Three.js Viewers:
 *  1. Full 3D Synth Workstation (chassis, 61 keys, joystick, LCD, playable keys)
 *  2. Full 3D KLM-1266 Main Logic PCB Board (silicon chips, traces, CR2032, inspection)
 * Interactive Ambient Sound showcase featuring the legendary M1 atmospheric voices.
 */

interface SoundPatch {
  id: string;
  name: string;
  category: string;
  oscType: OscillatorType;
  filterFreq: number;
  resonance?: number;
  attack: number;
  decay: number;
  sustain: number;
  release: number;
  detune: number;
  subOsc: boolean;
  synthMode:
    | "formant-choir"
    | "bell-pad"
    | "pan-lore"
    | "polar-chime"
    | "house-piano"
    | "slap-bass"
    | "house-organ"
    | "analog-brass"
    | "crystal-bell"
    | "ethnic-mallet"
    | "glass-pad";
  ambientVibe?: string;
  samples?: string;
  famousUse?: string;
}

const CLASSIC_PATCHES: SoundPatch[] = [
  {
    id: "00",
    name: "00: Universe",
    category: "Atmospheric Pad",
    oscType: "sawtooth",
    filterFreq: 1400,
    resonance: 2.2,
    attack: 0.4,
    decay: 1.2,
    sustain: 0.85,
    release: 2.2,
    detune: 16,
    subOsc: true,
    synthMode: "bell-pad",
    ambientVibe: "Choir breath chiff + sparkling metallic bells + warm sustained pad with lush hall reverb.",
    samples: "PCM #08 Choir + #14 Bell Wave + #01 Strings",
    famousUse: "Queen (Innuendo), Eric Serra (The Fifth Element), Enya, 90s ambient chillout.",
  },
  {
    id: "13",
    name: "13: Lore",
    category: "Ambient Dreamscape",
    oscType: "sawtooth",
    filterFreq: 1800,
    resonance: 3.0,
    attack: 0.15,
    decay: 1.5,
    sustain: 0.8,
    release: 2.4,
    detune: 20,
    subOsc: false,
    synthMode: "pan-lore",
    ambientVibe: "Haunting breathy pan-pipe chiff dissolving into shimmering delayed overtone chimes.",
    samples: "PCM #12 Pan Flute attack + #22 Lore Wave",
    famousUse: "The Cure (Disintegration / Pictures of You), Depeche Mode (Violator), Angelo Badalamenti.",
  },
  {
    id: "23",
    name: "23: Pole",
    category: "Arctic Resonance",
    oscType: "sine",
    filterFreq: 2400,
    resonance: 2.5,
    attack: 0.05,
    decay: 2.0,
    sustain: 0.7,
    release: 3.2,
    detune: 12,
    subOsc: true,
    synthMode: "polar-chime",
    ambientVibe: "Crystalline, icy metallic ringing sustained over deep sub-harmonic ambient warmth.",
    samples: "PCM #23 Pole Wave + #06 Kalimba transient",
    famousUse: "The Orb, Biosphere, early 90s ambient techno & IDM chillout rooms.",
  },
  {
    id: "08",
    name: "08: Ooh / Aah",
    category: "Vocal Choral Pad",
    oscType: "sawtooth",
    filterFreq: 1100,
    resonance: 4.8,
    attack: 0.45,
    decay: 0.8,
    sustain: 0.85,
    release: 1.8,
    detune: 10,
    subOsc: true,
    synthMode: "formant-choir",
    ambientVibe: "Ghostly multi-sampled vocal formants sweeping dynamically from Ooh to Aah with warm choral vibrato.",
    samples: "PCM #08 Choir Aah + #09 Choir Ooh",
    famousUse: "Vangelis, Enigma (MCMXC a.D.), Twin Peaks incidental atmospheres.",
  },
  {
    id: "09",
    name: "09: Theme",
    category: "Cinematic Swell",
    oscType: "sawtooth",
    filterFreq: 1600,
    resonance: 2.5,
    attack: 0.25,
    decay: 1.0,
    sustain: 0.8,
    release: 1.5,
    detune: 14,
    subOsc: true,
    synthMode: "analog-brass",
    ambientVibe: "Expansive orchestral brass/string swell with rich spatial stereo chorus.",
    samples: "PCM #02 Brass Ensemble + #01 Strings",
    famousUse: "Hollywood sci-fi and dramatic soundtracks, Hans Zimmer early synth layers.",
  },
  {
    id: "33",
    name: "33: Cloud Nine",
    category: "Ethereal Glass",
    oscType: "triangle",
    filterFreq: 2100,
    resonance: 2.0,
    attack: 0.35,
    decay: 1.2,
    sustain: 0.85,
    release: 2.0,
    detune: 15,
    subOsc: true,
    synthMode: "glass-pad",
    ambientVibe: "Floating crystalline bell harmonics layered over lush warm analog-style bedding.",
    samples: "PCM #14 Bell Ring + #04 Analog Saw",
    famousUse: "Steve Roach, Brian Eno collaborations, 90s planetarium & nature documentaries.",
  },
  {
    id: "27",
    name: "27: Bell Ring",
    category: "Harmonic Chime",
    oscType: "sine",
    filterFreq: 3100,
    resonance: 3.5,
    attack: 0.005,
    decay: 2.5,
    sustain: 0.1,
    release: 3.0,
    detune: 22,
    subOsc: false,
    synthMode: "crystal-bell",
    ambientVibe: "Sparkling FM-style crystal bell with multi-tap stereo delay and cathedral reverb.",
    samples: "PCM #27 Tubular Bell + #14 Digital Bell",
    famousUse: "Robert Miles, Tangerine Dream (late 80s era), New Age meditation music.",
  },
  {
    id: "45",
    name: "45: Digital Native",
    category: "Ethnic Percussive Ambient",
    oscType: "sawtooth",
    filterFreq: 3800,
    resonance: 3.0,
    attack: 0.005,
    decay: 1.2,
    sustain: 0.05,
    release: 1.0,
    detune: 25,
    subOsc: true,
    synthMode: "ethnic-mallet",
    ambientVibe: "Log drums, marimba mallets, and tribal percussion fading into rhythmic stereo echoes.",
    samples: "PCM #45 Log Drum + #46 Ethnic Mallet + #44 Taiko",
    famousUse: "Peter Gabriel, Enigma, Deep Forest, worldbeat ambient fusion.",
  },
  {
    id: "01",
    name: "01: Piano 16'",
    category: "Acoustic / Dance Piano",
    oscType: "triangle",
    filterFreq: 3600,
    resonance: 1.5,
    attack: 0.002,
    decay: 1.6,
    sustain: 0.001,
    release: 0.3,
    detune: 4,
    subOsc: true,
    synthMode: "house-piano",
    ambientVibe: "Crisp percussive hammer strike with tight low-frequency body.",
    samples: "PCM #00 Acoustic Piano multi-samples",
    famousUse: "Robin S (Show Me Love), Madonna (Vogue), Black Box (Ride On Time).",
  },
  {
    id: "16",
    name: "16: Slap Bass",
    category: "Percussive Bass",
    oscType: "square",
    filterFreq: 2800,
    resonance: 3.8,
    attack: 0.002,
    decay: 0.45,
    sustain: 0.05,
    release: 0.15,
    detune: 2,
    subOsc: false,
    synthMode: "slap-bass",
    ambientVibe: "Punchy, aggressive thumb-slap transient with quick damped decay.",
    samples: "PCM #16 Slap Bass thumb + pop",
    famousUse: "Jonathan Wolff (Seinfeld Theme), 90s TV scoring.",
  },
  {
    id: "17",
    name: "17: Organ 2",
    category: "House Organ",
    oscType: "square",
    filterFreq: 3200,
    resonance: 2.0,
    attack: 0.004,
    decay: 0.5,
    sustain: 0.9,
    release: 0.12,
    detune: 8,
    subOsc: true,
    synthMode: "house-organ",
    ambientVibe: "Percussive click harmonic organ key with deep hollow bass resonance.",
    samples: "PCM #17 Electronic Organ 2",
    famousUse: "Robin S (Show Me Love bassline), Nightcrawlers, 90s UK garage.",
  },
  {
    id: "24",
    name: "24: Brass 1",
    category: "Synth Brass",
    oscType: "sawtooth",
    filterFreq: 2400,
    resonance: 2.8,
    attack: 0.1,
    decay: 0.8,
    sustain: 0.75,
    release: 0.7,
    detune: 12,
    subOsc: true,
    synthMode: "analog-brass",
    ambientVibe: "Punchy analog-modeled polyphonic brass fanfare.",
    samples: "PCM #02 Brass Waveform",
    famousUse: "Toto, late 80s arena pop and television themes.",
  },
];

const MODES = [
  "INT",
  "COMBI",
  "PROG",
  "SEQ",
  "GLOBAL",
  "CARD",
  "EDITC",
  "EDITP",
];

interface ChipInfo {
  id: string;
  label: string;
  partNumber: string;
  name: string;
  package: string;
  busRange: string;
  description: string;
  x: number;
  z: number;
  w: number;
  d: number;
  h: number;
  color: number;
}

const KLM1266_CHIPS: ChipInfo[] = [
  {
    id: "cpu",
    label: "IC1",
    partNumber: "NEC uPD70216 (V50)",
    name: "16-bit Master Microprocessor",
    package: "80-pin QFP / PGA",
    busRange: "0x00000 – 0xFFFFF (1 MB address space @ 16 MHz)",
    description: "Coordination CPU running 8086-compatible opcode architecture. Drives UI, scans keyboard/front panel, coordinates MIDI parser, and manages the 8-track sequencer.",
    x: -0.65,
    z: -0.35,
    w: 0.32,
    d: 0.32,
    h: 0.045,
    color: 0x181a1f,
  },
  {
    id: "tg1",
    label: "IC4",
    partNumber: "Fujitsu MB87402 (TG1)",
    name: "Tone Generator 1 (Voices 1–8)",
    package: "80-pin Flatpack",
    busRange: "I/O 0x1000 – 0x10FF",
    description: "Custom Korg tone generation ASIC. Interpolates 16-bit PCM multi-samples from waveform ROM into 8 discrete digital audio voice streams.",
    x: 0.15,
    z: -0.38,
    w: 0.28,
    d: 0.28,
    h: 0.042,
    color: 0x181a1f,
  },
  {
    id: "tg2",
    label: "IC5",
    partNumber: "Fujitsu MB87403 (TG2)",
    name: "Tone Generator 2 (Voices 9–16)",
    package: "80-pin Flatpack",
    busRange: "I/O 0x1100 – 0x11FF",
    description: "Secondary tone generation ASIC providing remaining 8 polyphonic voice streams, supporting 16-voice single mode or 8-voice layered double mode.",
    x: 0.52,
    z: -0.38,
    w: 0.28,
    d: 0.28,
    h: 0.042,
    color: 0x181a1f,
  },
  {
    id: "vdf1",
    label: "IC8",
    partNumber: "Fujitsu MB87404 (VDF1)",
    name: "Variable Digital Filter 1",
    package: "64-pin Flatpack",
    busRange: "I/O 0x0100",
    description: "Digital low-pass filter IC providing dynamic frequency cutoff, resonance emulation, and key tracking for Voices 1–8.",
    x: 0.15,
    z: 0.05,
    w: 0.24,
    d: 0.24,
    h: 0.038,
    color: 0x181a1f,
  },
  {
    id: "vdf2",
    label: "IC9",
    partNumber: "Fujitsu MB87404 (VDF2)",
    name: "Variable Digital Filter 2",
    package: "64-pin Flatpack",
    busRange: "I/O 0x0200",
    description: "Digital filter IC for Voices 9–16 with independent 8-stage envelope generator modulation.",
    x: 0.52,
    z: 0.05,
    w: 0.24,
    d: 0.24,
    h: 0.038,
    color: 0x181a1f,
  },
  {
    id: "mde",
    label: "IC12",
    partNumber: "Fujitsu MB87405 (MDE)",
    name: "Multi-Digital Effects DSP",
    package: "80-pin Flatpack",
    busRange: "I/O 0x0500",
    description: "Dedicated 24-bit audio effects DSP. Calculates two independent stereo effects chains simultaneously (33 algorithms: Hall Reverb, Stereo Delay, Chorus, Flanger, Exciter).",
    x: 0.35,
    z: 0.42,
    w: 0.30,
    d: 0.30,
    h: 0.042,
    color: 0x181a1f,
  },
  {
    id: "rom",
    label: "IC15",
    partNumber: "Fujitsu MB83512 (128 KB)",
    name: "System IPL Firmware ROM",
    package: "28-pin DIP",
    busRange: "0xE0000 – 0xFFFFF",
    description: "Mask ROM containing NEC V50 boot firmware, self-test routines, system diagnostic vectors, and front-panel operating OS.",
    x: -0.65,
    z: 0.12,
    w: 0.18,
    d: 0.36,
    h: 0.045,
    color: 0x111216,
  },
  {
    id: "sram",
    label: "IC20",
    partNumber: "HM62256 (64 KB)",
    name: "Battery NVRAM (Programs/Combis)",
    package: "28-pin SOP",
    busRange: "0x00000 – 0x0FFFF",
    description: "Static RAM backed by the CR2032 lithium cell. Stores 100 Programs, 100 Combinations, Global MIDI settings, and 7,700-note sequencer songs.",
    x: -0.28,
    z: 0.12,
    w: 0.16,
    d: 0.34,
    h: 0.04,
    color: 0x111216,
  },
  {
    id: "battery",
    label: "BT1",
    partNumber: "CR2032 (3V Lithium)",
    name: "NVRAM Backup Coin Cell",
    package: "Through-hole battery clip",
    busRange: "+3.0V DC Rail",
    description: "Provides standby voltage to keep SRAM preserved when powered off. When voltage falls under 2.2V, memory corrupts resulting in blank patches / garbled LCD.",
    x: -0.28,
    z: 0.48,
    w: 0.22,
    d: 0.22,
    h: 0.035,
    color: 0xd4d4d8,
  },
  {
    id: "pcm_rom1",
    label: "IC17",
    partNumber: "TC532000 (2 MB)",
    name: "PCM Waveform ROM Bank 1",
    package: "32-pin DIP",
    busRange: "TG Bus (Lower 2 MB)",
    description: "Stores multi-sampled acoustic PCM instruments (Piano, Choir, Strings, Flute, Drums) sampled at 31.25 kHz.",
    x: -0.15,
    z: -0.42,
    w: 0.16,
    d: 0.38,
    h: 0.045,
    color: 0x111216,
  },
  {
    id: "pio",
    label: "IC22",
    partNumber: "Sony CXD1095Q",
    name: "Front Panel I/O Expander",
    package: "64-pin QFP",
    busRange: "I/O 0x0A00 (Y0..Y7)",
    description: "Programmable I/O peripheral controller scanning the 34 tactile front-panel buttons, mode select keys, and slide potentiometers.",
    x: -0.68,
    z: 0.48,
    w: 0.22,
    d: 0.22,
    h: 0.038,
    color: 0x181a1f,
  },
  {
    id: "dac",
    label: "IC28",
    partNumber: "PCM54HP (Burr-Brown)",
    name: "16-bit Linear Audio DAC",
    package: "28-pin DIP",
    busRange: "Audio Subsystem (KLM-1261)",
    description: "Ultra-low distortion monotonic 16-bit DAC converting digital sum from MDE effects processor into warm, punchy analog stereo outputs.",
    x: 0.76,
    z: 0.42,
    w: 0.16,
    d: 0.36,
    h: 0.045,
    color: 0x111216,
  },
];

export function HardwareM1() {
  const mountRef = useRef<HTMLDivElement>(null);
  const pcbMountRef = useRef<HTMLDivElement>(null);

  const [selectedPatch, setSelectedPatch] = useState<SoundPatch>(CLASSIC_PATCHES[0]);
  const [selectedProgram, setSelectedProgram] = useState<M1Program>(M1_100_PROGRAMS[0]);
  const [selectedCombi, setSelectedCombi] = useState<M1Combi>(M1_100_COMBIS[0]);
  const [bankTab, setBankTab] = useState<"programs" | "combis">("programs");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  // Web MIDI Output Ports (to drive DAW / VST3 / External hardware)
  const [midiOutputs, setMidiOutputs] = useState<{ id: string; name: string }[]>([]);
  const [selectedMidiOutputId, setSelectedMidiOutputId] = useState<string>("");
  const midiOutputRef = useRef<MIDIOutput | null>(null);
  const midiAccessRef = useRef<MIDIAccess | null>(null);

  const [selectedMode, setSelectedMode] = useState<string>("PROG");
  const [lcdLine1, setLcdLine1] = useState<string>("PROG 00 Universe   I-C00");
  const [lcdLine2, setLcdLine2] = useState<string>("16V AI-SYNTH  KLM-1266 OK");
  const [spotlightIntensity, setSpotlightIntensity] = useState<number>(6.5);
  const [ambientIntensity, setAmbientIntensity] = useState<number>(1.6);
  const [volume, setVolume] = useState<number>(85);
  const [audioEnabled, setAudioEnabled] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"arch" | "silicon" | "restore" | "culture" | "vst">("arch");

  // Fullscreen States & Container Refs
  const [isFullscreenSynth, setIsFullscreenSynth] = useState(false);
  const [isFullscreenPcb, setIsFullscreenPcb] = useState(false);
  const stageSynthRef = useRef<HTMLDivElement>(null);
  const stagePcbRef = useRef<HTMLDivElement>(null);

  // Web MIDI API State
  const [midiConnected, setMidiConnected] = useState(false);
  const [midiDeviceName, setMidiDeviceName] = useState<string>("No MIDI Device Detected");

  // VST Synthesizer Parameters
  const vstCutoff = 1800;
  const vstResonance = 3.5;
  const vstDecay = 2.5;
  const vstDetune = 14;
  const vstDoubleMode = true;
  const vstDelayFeedback = 35;

  // Selected PCB Chip for detailed inspection
  const [inspectedChip, setInspectedChip] = useState<ChipInfo>(KLM1266_CHIPS[0]);
  const [pcbSpotlight, setPcbSpotlight] = useState<number>(5.5);

  // Web Audio Context for real synthesizer playback
  const audioCtxRef = useRef<AudioContext | null>(null);

  // References for live 3D sync
  const lcdRef = useRef<{ l1: string; l2: string }>({ l1: lcdLine1, l2: lcdLine2 });
  lcdRef.current = { l1: lcdLine1, l2: lcdLine2 };

  const spotLightRef = useRef<THREE.SpotLight | null>(null);
  const fillSpotRef = useRef<THREE.SpotLight | null>(null);
  const ambientLightRef = useRef<THREE.AmbientLight | null>(null);
  const keyMeshesRef = useRef<Map<number, { mesh: THREE.Mesh; origY: number; origColor: number }>>(new Map());
  const setCamViewRef = useRef<((t: number, p: number, r: number) => void) | null>(null);

  // PCB Viewer References
  const pcbCamFocusRef = useRef<((x: number, z: number) => void) | null>(null);
  const pcbSpotRef = useRef<THREE.SpotLight | null>(null);

  // Fullscreen Handlers
  const toggleSynthFullscreen = () => {
    if (!stageSynthRef.current) return;
    if (!document.fullscreenElement) {
      stageSynthRef.current.requestFullscreen().then(() => setIsFullscreenSynth(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreenSynth(false)).catch(() => {});
    }
  };

  const togglePcbFullscreen = () => {
    if (!stagePcbRef.current) return;
    if (!document.fullscreenElement) {
      stagePcbRef.current.requestFullscreen().then(() => setIsFullscreenPcb(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreenPcb(false)).catch(() => {});
    }
  };

  useEffect(() => {
    const onFsChange = () => {
      setIsFullscreenSynth(document.fullscreenElement === stageSynthRef.current);
      setIsFullscreenPcb(document.fullscreenElement === stagePcbRef.current);
    };
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  // Visual key depression trigger
  const triggerKeyVisualDirect = useCallback((midiPitch: number) => {
    const entry = keyMeshesRef.current.get(midiPitch);
    if (!entry) return;
    const mesh = entry.mesh;
    mesh.position.y = entry.origY - 0.015;
    mesh.rotation.x = 0.02;

    const mat = mesh.material as THREE.MeshStandardMaterial;
    mat.color.setHex(0x38bdf8);
    mat.emissive.setHex(0x0284c7);
    mat.emissiveIntensity = 0.5;

    window.setTimeout(() => {
      mesh.position.y = entry.origY;
      mesh.rotation.x = 0;
      mat.color.setHex(entry.origColor);
      mat.emissive.setHex(0x000000);
      mat.emissiveIntensity = 0;
    }, 180);
  }, []);

  // Play audio note with custom VST parameters
  const playNote = useCallback((midiNote: number, patchOverride?: SoundPatch, velocity = 100) => {
    if (!audioEnabled) return;
    try {
      if (!audioCtxRef.current) {
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        audioCtxRef.current = new AudioCtx();
      }
      if (audioCtxRef.current.state === "suspended") {
        audioCtxRef.current.resume();
      }
      const ctx = audioCtxRef.current;
      const targetPatch = patchOverride || selectedPatch;
      const freq = 440 * Math.pow(2, (midiNote - 69) / 12);
      const now = ctx.currentTime;

      // Master gain for this note scaled by velocity
      const noteGain = ctx.createGain();
      const velScale = velocity / 127;
      const volLinear = (volume / 100) * 0.22 * velScale;
      noteGain.gain.setValueAtTime(volLinear, now);
      noteGain.gain.exponentialRampToValueAtTime(0.0001, now + vstDecay);

      // Variable Digital Filter (VDF)
      const vdf = ctx.createBiquadFilter();
      vdf.type = "lowpass";
      vdf.frequency.setValueAtTime(vstCutoff, now);
      vdf.frequency.exponentialRampToValueAtTime(vstCutoff * 0.35, now + vstDecay);
      vdf.Q.setValueAtTime(vstResonance, now);

      // Oscillator 1
      const osc1 = ctx.createOscillator();
      osc1.type = targetPatch.oscType;
      osc1.frequency.setValueAtTime(freq, now);
      osc1.detune.setValueAtTime(-vstDetune, now);

      osc1.connect(vdf);
      osc1.start(now);
      osc1.stop(now + vstDecay);

      // Oscillator 2 (Double Mode)
      if (vstDoubleMode || targetPatch.subOsc) {
        const osc2 = ctx.createOscillator();
        osc2.type = targetPatch.oscType === "sawtooth" ? "square" : targetPatch.oscType;
        osc2.frequency.setValueAtTime(freq, now);
        osc2.detune.setValueAtTime(vstDetune, now);
        osc2.connect(vdf);
        osc2.start(now);
        osc2.stop(now + vstDecay);
      }

      // Simulated spatial stereo delay / MDE reverb
      const delay = ctx.createDelay();
      delay.delayTime.setValueAtTime(0.24, now);
      const delayFeedback = ctx.createGain();
      delayFeedback.gain.setValueAtTime((vstDelayFeedback / 100) * 0.6, now);

      vdf.connect(delay);
      delay.connect(delayFeedback);
      delayFeedback.connect(delay);
      delay.connect(noteGain);

      vdf.connect(noteGain);
      noteGain.connect(ctx.destination);
    } catch {
      // Audio playback fails silently if browser blocks autoplay before user gesture
    }
  }, [audioEnabled, volume, selectedPatch, vstCutoff, vstResonance, vstDecay, vstDetune, vstDoubleMode, vstDelayFeedback]);

  // WEB MIDI API: Connect to hardware MIDI keyboard
  useEffect(() => {
    if (!navigator.requestMIDIAccess) {
      setMidiDeviceName("Web MIDI API not supported in this browser");
      return;
    }

    let midiAccessObj: MIDIAccess | null = null;

    const onMIDIMessage = (event: MIDIMessageEvent) => {
      const data = event.data;
      if (!data || data.length < 2) return;
      const status = data[0] & 0xf0;
      const note = data[1];
      const velocity = data.length > 2 ? data[2] : 0;

      // Note On
      if (status === 0x90 && velocity > 0) {
        triggerKeyVisualDirect(note);
        playNote(note, undefined, velocity);

        const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
        const octave = Math.floor(note / 12) - 1;
        const noteStr = `${noteNames[note % 12]}${octave}`;
        lcdRef.current.l2 = `MIDI-IN: ${noteStr.padEnd(4, " ")} VEL:${velocity.toString().padEnd(3, " ")} CH1`;
        setLcdLine2(lcdRef.current.l2);
      }
    };

    navigator.requestMIDIAccess({ sysex: true }).then((access) => {
      midiAccessObj = access;
      midiAccessRef.current = access;
      let hasDevice = false;

      const setupPorts = () => {
        let name = "Web MIDI Active";
        access.inputs.forEach((input) => {
          hasDevice = true;
          name = input.name || "External MIDI Controller";
          input.onmidimessage = onMIDIMessage;
        });
        setMidiConnected(hasDevice);
        setMidiDeviceName(hasDevice ? name : "Listening (Plug in USB MIDI keyboard)");

        const outs: { id: string; name: string }[] = [];
        access.outputs.forEach((out) => {
          outs.push({ id: out.id, name: out.name || "MIDI Output Port" });
        });
        setMidiOutputs(outs);
        if (outs.length > 0) {
          setSelectedMidiOutputId((prev) => {
            const nextId = prev || outs[0].id;
            midiOutputRef.current = access.outputs.get(nextId) || null;
            return nextId;
          });
        }
      };

      setupPorts();
      access.onstatechange = () => setupPorts();
    }).catch(() => {
      setMidiDeviceName("MIDI Access Denied or Unavailable");
    });

    return () => {
      if (midiAccessObj) {
        midiAccessObj.inputs.forEach((input) => {
          input.onmidimessage = null;
        });
      }
    };
  }, [playNote, triggerKeyVisualDirect]);

  // Send MIDI event out to selected MIDI Output port (e.g. loopMIDI to VST3 DAW)
  const sendMidiMessage = useCallback((bytes: number[]) => {
    if (midiOutputRef.current) {
      try {
        midiOutputRef.current.send(bytes);
      } catch (err) {
        console.warn("MIDI output error:", err);
      }
    }
  }, []);

  const handleSelectMidiOutput = (id: string) => {
    setSelectedMidiOutputId(id);
    if (midiAccessRef.current) {
      midiOutputRef.current = midiAccessRef.current.outputs.get(id) || null;
    }
  };

  // Physical PC Keyboard Piano Mapping (ASDF.. for C4..C5)
  useEffect(() => {
    const PC_PIANO: Record<string, number> = {
      KeyA: 60, // C4
      KeyW: 61, // C#4
      KeyS: 62, // D4
      KeyE: 63, // D#4
      KeyD: 64, // E4
      KeyF: 65, // F4
      KeyT: 66, // F#4
      KeyG: 67, // G4
      KeyY: 68, // G#4
      KeyH: 69, // A4
      KeyU: 70, // A#4
      KeyJ: 71, // B4
      KeyK: 72, // C5
      KeyO: 73, // C#5
      KeyL: 74, // D5
      KeyP: 75, // D#5
      Semicolon: 76, // E5
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      const note = PC_PIANO[e.code];
      if (note && !e.repeat) {
        e.preventDefault();
        triggerKeyVisualDirect(note);
        playNote(note, undefined, 110);
        sendMidiMessage([0x90, note, 110]); // Broadcast to VST3

        const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
        const octave = Math.floor(note / 12) - 1;
        const noteStr = `${noteNames[note % 12]}${octave}`;
        lcdRef.current.l2 = `KEYBD: ${noteStr.padEnd(4, " ")} MIDI:${note}  VEL:110`;
        setLcdLine2(lcdRef.current.l2);
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      const note = PC_PIANO[e.code];
      if (note) {
        sendMidiMessage([0x80, note, 0]); // Note Off to VST3
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [playNote, triggerKeyVisualDirect, sendMidiMessage]);

  // Handle program selection (00-99)
  const handleSelectProgram = (prog: M1Program) => {
    setSelectedProgram(prog);
    setSelectedMode("PROG");
    setSelectedPatch((prev) => ({
      ...prev,
      id: prog.id,
      name: `${prog.id}: ${prog.name}`,
      category: prog.category,
      samples: prog.osc1Sample + (prog.osc2Sample ? ` + ${prog.osc2Sample}` : ""),
    }));
    const l1 = `PROG ${prog.id} ${prog.name.slice(0, 14).padEnd(14, " ")}  I-C${prog.id}`;
    const l2 = `${prog.oscMode.toUpperCase().padEnd(6, " ")} PCM:${prog.osc1Sample.slice(0, 16)} OK`;
    setLcdLine1(l1);
    setLcdLine2(l2);
    sendMidiMessage([0xC0, prog.num]); // Send MIDI Program Change to VST3
    triggerKeyVisualDirect(60);
    playNote(60);
  };

  // Handle combination selection (00-99)
  const handleSelectCombi = (combi: M1Combi) => {
    setSelectedCombi(combi);
    setSelectedMode("COMBI");
    setSelectedPatch((prev) => ({
      ...prev,
      id: combi.id,
      name: `${combi.id}: ${combi.name}`,
      category: "Multi",
      samples: combi.programs.join(" + "),
    }));
    const l1 = `COMBI ${combi.id} ${combi.name.slice(0, 14).padEnd(14, " ")}`;
    const l2 = `${combi.type.toUpperCase().padEnd(6, " ")} 8-PART MULTI TIMB OK`;
    setLcdLine1(l1);
    setLcdLine2(l2);
    sendMidiMessage([0xC0, combi.num]); // Send MIDI Program Change to VST3
    triggerKeyVisualDirect(60);
    playNote(60);
  };

  // Sync spot / ambient light when sliders change
  useEffect(() => {
    if (spotLightRef.current) spotLightRef.current.intensity = spotlightIntensity;
    if (fillSpotRef.current) fillSpotRef.current.intensity = spotlightIntensity * 0.55;
  }, [spotlightIntensity]);

  useEffect(() => {
    if (ambientLightRef.current) ambientLightRef.current.intensity = ambientIntensity;
  }, [ambientIntensity]);

  useEffect(() => {
    if (pcbSpotRef.current) pcbSpotRef.current.intensity = pcbSpotlight;
  }, [pcbSpotlight]);

  // ==========================================
  // 1. THREE.JS SYNTH WORKSTATION VIEWER SETUP
  // ==========================================
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const W = mount.clientWidth || 920;
    const H = 500;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f172a); // Slate-900 studio backdrop

    const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
    let theta = 0.42;
    let phi = 1.05;
    let radius = 3.4;

    const updateCam = () => {
      camera.position.set(
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.cos(theta),
      );
      camera.lookAt(0, 0.05, 0.08);
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

    // Studio Ground Grid & Shadow Floor
    const gridHelper = new THREE.GridHelper(10, 24, 0x38bdf8, 0x1e293b);
    gridHelper.position.y = -0.12;
    scene.add(gridHelper);

    const floorGeo = new THREE.PlaneGeometry(12, 12);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      roughness: 0.9,
      metalness: 0.1,
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.125;
    floor.receiveShadow = true;
    scene.add(floor);

    // LIGHTING RIG
    const spot = new THREE.SpotLight(0xfffaed, spotlightIntensity);
    spot.position.set(0, 3.8, 2.5);
    spot.angle = Math.PI / 4.2;
    spot.penumbra = 0.4;
    spot.decay = 1.3;
    spot.distance = 15;
    spot.castShadow = true;
    spot.shadow.mapSize.width = 1024;
    spot.shadow.mapSize.height = 1024;
    scene.add(spot);
    spotLightRef.current = spot;

    const fillSpot = new THREE.SpotLight(0xcce2ff, spotlightIntensity * 0.55);
    fillSpot.position.set(-2.8, 3.0, 1.8);
    fillSpot.angle = Math.PI / 3.8;
    fillSpot.penumbra = 0.5;
    fillSpot.decay = 1.4;
    scene.add(fillSpot);
    fillSpotRef.current = fillSpot;

    const amb = new THREE.AmbientLight(0xdde8f8, ambientIntensity);
    scene.add(amb);
    ambientLightRef.current = amb;

    const dirKey = new THREE.DirectionalLight(0xfff5ea, 1.6);
    dirKey.position.set(1.5, 4.0, 2.0);
    dirKey.castShadow = true;
    scene.add(dirKey);

    const rim = new THREE.DirectionalLight(0x38bdf8, 0.9);
    rim.position.set(-2.5, 2.0, -3.0);
    scene.add(rim);

    const synth = new THREE.Group();
    scene.add(synth);
    spot.target = synth;
    fillSpot.target = synth;

    // SYNTH CHASSIS
    const chassisMat = new THREE.MeshStandardMaterial({
      color: 0x1f232b,
      roughness: 0.52,
      metalness: 0.35,
    });
    const chassis = new THREE.Mesh(new THREE.BoxGeometry(2.56, 0.18, 0.84), chassisMat);
    chassis.castShadow = true;
    chassis.receiveShadow = true;
    synth.add(chassis);

    // Cheek blocks
    const cheekMat = new THREE.MeshStandardMaterial({ color: 0x15181e, roughness: 0.65, metalness: 0.2 });
    const leftCheek = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.20, 0.86), cheekMat);
    leftCheek.position.set(-1.28, 0, 0);
    leftCheek.castShadow = true;
    synth.add(leftCheek);
    const rightCheek = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.20, 0.86), cheekMat);
    rightCheek.position.set(1.28, 0, 0);
    rightCheek.castShadow = true;
    synth.add(rightCheek);

    // Deck plate
    const deck = new THREE.Mesh(
      new THREE.BoxGeometry(2.42, 0.02, 0.42),
      new THREE.MeshStandardMaterial({ color: 0x262b35, roughness: 0.45, metalness: 0.4 }),
    );
    deck.position.set(0, 0.095, -0.20);
    synth.add(deck);

    // LCD DISPLAY
    const lcdCanvas = document.createElement("canvas");
    lcdCanvas.width = 512;
    lcdCanvas.height = 128;
    const lcdTex = new THREE.CanvasTexture(lcdCanvas);

    const drawLcd = () => {
      const g = lcdCanvas.getContext("2d");
      if (!g) return;
      g.fillStyle = "#0c281e";
      g.fillRect(0, 0, 512, 128);

      const grad = g.createLinearGradient(0, 0, 512, 128);
      grad.addColorStop(0, "rgba(52, 211, 153, 0.15)");
      grad.addColorStop(1, "rgba(16, 185, 129, 0.05)");
      g.fillStyle = grad;
      g.fillRect(0, 0, 512, 128);

      g.fillStyle = "#86efac";
      g.shadowColor = "#34d399";
      g.shadowBlur = 6;
      g.font = "bold 28px 'Courier New', monospace";
      g.fillText(lcdRef.current.l1.slice(0, 24), 20, 48);
      g.fillText(lcdRef.current.l2.slice(0, 24), 20, 96);
      g.shadowBlur = 0;
      lcdTex.needsUpdate = true;
    };
    drawLcd();

    const bezel = new THREE.Mesh(
      new THREE.BoxGeometry(0.72, 0.015, 0.22),
      new THREE.MeshStandardMaterial({ color: 0x111317, roughness: 0.8 }),
    );
    bezel.position.set(-0.46, 0.108, -0.20);
    synth.add(bezel);

    const lcdMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.66, 0.16), new THREE.MeshBasicMaterial({ map: lcdTex }));
    lcdMesh.rotation.x = -Math.PI / 2;
    lcdMesh.position.set(-0.46, 0.118, -0.20);
    synth.add(lcdMesh);
    const lcdTimer = window.setInterval(drawLcd, 400);

    // KORG M1 BADGE
    const badgeCanvas = document.createElement("canvas");
    badgeCanvas.width = 512;
    badgeCanvas.height = 128;
    const badgeG = badgeCanvas.getContext("2d");
    if (badgeG) {
      badgeG.fillStyle = "#262b35";
      badgeG.fillRect(0, 0, 512, 128);
      badgeG.fillStyle = "#ffffff";
      badgeG.font = "bold 44px sans-serif";
      badgeG.fillText("KORG", 16, 68);
      badgeG.fillStyle = "#38bdf8";
      badgeG.font = "bold 58px sans-serif";
      badgeG.fillText("M1", 160, 70);
      badgeG.fillStyle = "#94a3b8";
      badgeG.font = "16px sans-serif";
      badgeG.fillText("MUSIC WORKSTATION · AI SYNTHESIS SYSTEM", 18, 106);
    }
    const badgeTex = new THREE.CanvasTexture(badgeCanvas);
    const badgeMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(0.55, 0.14),
      new THREE.MeshStandardMaterial({ map: badgeTex, roughness: 0.5, metalness: 0.2 }),
    );
    badgeMesh.rotation.x = -Math.PI / 2;
    badgeMesh.position.set(-0.85, 0.106, -0.32);
    synth.add(badgeMesh);

    // 4-WAY VECTOR JOYSTICK
    const joyBlock = new THREE.Mesh(
      new THREE.BoxGeometry(0.18, 0.05, 0.26),
      new THREE.MeshStandardMaterial({ color: 0x181a20, roughness: 0.7 }),
    );
    joyBlock.position.set(-1.15, 0.08, 0.15);
    synth.add(joyBlock);

    const joyStick = new THREE.Mesh(
      new THREE.CylinderGeometry(0.012, 0.016, 0.09, 12),
      new THREE.MeshStandardMaterial({ color: 0x0f1115, roughness: 0.3, metalness: 0.7 }),
    );
    joyStick.position.set(-1.15, 0.13, 0.15);
    joyStick.castShadow = true;
    synth.add(joyStick);

    const joyCap = new THREE.Mesh(
      new THREE.SphereGeometry(0.024, 16, 12),
      new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.4 }),
    );
    joyCap.position.set(-1.15, 0.175, 0.15);
    synth.add(joyCap);

    // Y-MATRIX MODE BUTTONS
    const btnMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.5 });
    const btnActiveMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      roughness: 0.35,
      emissive: 0x0369a1,
      emissiveIntensity: 0.4,
    });
    const btnMeshes: THREE.Mesh[] = [];
    MODES.forEach((m, i) => {
      const b = new THREE.Mesh(
        new THREE.BoxGeometry(0.08, 0.025, 0.055),
        m === selectedMode ? btnActiveMat : btnMat,
      );
      b.position.set(-0.08 + (i % 4) * 0.11, 0.112, -0.24 + Math.floor(i / 4) * 0.08);
      b.userData.mode = m;
      b.castShadow = true;
      synth.add(b);
      btnMeshes.push(b);
    });

    // 61-KEY KEYBED
    const whiteKeyMat = new THREE.MeshStandardMaterial({ color: 0xfaf9f5, roughness: 0.28, metalness: 0.08 });
    const blackKeyMat = new THREE.MeshStandardMaterial({ color: 0x181a1f, roughness: 0.35, metalness: 0.15 });

    const keyGroup = new THREE.Group();
    keyGroup.position.set(0.02, 0.07, 0.19);
    synth.add(keyGroup);

    keyMeshesRef.current.clear();
    const whiteCount = 36;
    const totalKeyWidth = 2.26;
    const kw = totalKeyWidth / whiteCount;
    let whiteIndex = 0;

    for (let noteIdx = 0; noteIdx < 61; noteIdx++) {
      const midiPitch = 36 + noteIdx;
      const semitone = noteIdx % 12;
      const isBlack = [1, 3, 6, 8, 10].includes(semitone);

      if (!isBlack) {
        const whiteKey = new THREE.Mesh(new THREE.BoxGeometry(kw * 0.94, 0.045, 0.33), whiteKeyMat.clone());
        const xPos = -totalKeyWidth / 2 + whiteIndex * kw + kw / 2;
        whiteKey.position.set(xPos, 0.015, 0);
        whiteKey.castShadow = true;
        whiteKey.receiveShadow = true;
        whiteKey.userData.note = midiPitch;
        keyGroup.add(whiteKey);

        keyMeshesRef.current.set(midiPitch, { mesh: whiteKey, origY: 0.015, origColor: 0xfaf9f5 });
        whiteIndex++;
      } else {
        const blackKey = new THREE.Mesh(new THREE.BoxGeometry(kw * 0.62, 0.06, 0.21), blackKeyMat.clone());
        const xPos = -totalKeyWidth / 2 + whiteIndex * kw;
        blackKey.position.set(xPos, 0.038, -0.06);
        blackKey.castShadow = true;
        blackKey.receiveShadow = true;
        blackKey.userData.note = midiPitch;
        keyGroup.add(blackKey);

        keyMeshesRef.current.set(midiPitch, { mesh: blackKey, origY: 0.038, origColor: 0x181a1f });
      }
    }

    // RAYCASTING
    const ray = new THREE.Raycaster();
    const ptr = new THREE.Vector2();

    const triggerKeyVisual = (mesh: THREE.Mesh, midiPitch: number) => {
      const entry = keyMeshesRef.current.get(midiPitch);
      if (!entry) return;
      mesh.position.y = entry.origY - 0.015;
      mesh.rotation.x = 0.02;
      const mat = mesh.material as THREE.MeshStandardMaterial;
      mat.color.setHex(0x38bdf8);
      mat.emissive.setHex(0x0284c7);
      mat.emissiveIntensity = 0.5;

      window.setTimeout(() => {
        mesh.position.y = entry.origY;
        mesh.rotation.x = 0;
        mat.color.setHex(entry.origColor);
        mat.emissive.setHex(0x000000);
        mat.emissiveIntensity = 0;
      }, 180);
    };

    const onClick = (e: MouseEvent) => {
      const r = renderer.domElement.getBoundingClientRect();
      ptr.x = ((e.clientX - r.left) / r.width) * 2 - 1;
      ptr.y = -((e.clientY - r.top) / r.height) * 2 + 1;
      ray.setFromCamera(ptr, camera);

      const hits = ray.intersectObjects([...keyGroup.children, ...btnMeshes]);
      if (hits.length > 0) {
        const hit = hits[0].object as THREE.Mesh;
        if (hit.userData.mode) {
          const m = hit.userData.mode as string;
          setSelectedMode(m);
          btnMeshes.forEach((b) => {
            (b as THREE.Mesh).material = b.userData.mode === m ? btnActiveMat : btnMat;
          });
          lcdRef.current.l1 = `${m.padEnd(8, " ")} KORG M1 AI-SYNTH`;
          setLcdLine1(lcdRef.current.l1);
        } else if (typeof hit.userData.note === "number") {
          const midiPitch = hit.userData.note as number;
          triggerKeyVisual(hit, midiPitch);
          playNote(midiPitch);

          const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
          const octave = Math.floor(midiPitch / 12) - 1;
          const noteStr = `${noteNames[midiPitch % 12]}${octave}`;
          lcdRef.current.l2 = `KEY:${noteStr.padEnd(4, " ")} MIDI:${midiPitch}  VEL:110`;
          setLcdLine2(lcdRef.current.l2);
        }
      }
    };
    renderer.domElement.addEventListener("click", onClick);

    // ORBIT
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
      phi = Math.min(1.42, Math.max(0.25, phi - (e.clientY - py) * 0.005));
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
  }, [playNote]);

  // ==========================================
  // 2. THREE.JS KLM-1266 PCB 3D VIEWER SETUP
  // ==========================================
  useEffect(() => {
    const mount = pcbMountRef.current;
    if (!mount) return;

    const W = mount.clientWidth || 600;
    const H = 420;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a101d);

    const camera = new THREE.PerspectiveCamera(40, W / H, 0.1, 50);
    let theta = 0.0;
    let phi = 0.45;
    let radius = 2.8;

    const updateCam = () => {
      camera.position.set(
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.cos(theta),
      );
      camera.lookAt(0, 0, 0);
    };
    updateCam();

    pcbCamFocusRef.current = (targetX: number, targetZ: number) => {
      theta = Math.atan2(targetX, targetZ + 1.2);
      phi = 0.55;
      radius = 1.6;
      updateCam();
    };

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    mount.appendChild(renderer.domElement);

    // PCB Studio Lighting Rig
    const pcbSpot = new THREE.SpotLight(0xfff6e5, pcbSpotlight);
    pcbSpot.position.set(0, 3.2, 1.4);
    pcbSpot.angle = Math.PI / 3.2;
    pcbSpot.penumbra = 0.35;
    pcbSpot.decay = 1.2;
    pcbSpot.castShadow = true;
    scene.add(pcbSpot);
    pcbSpotRef.current = pcbSpot;

    const pcbFill = new THREE.SpotLight(0x99ccff, pcbSpotlight * 0.4);
    pcbFill.position.set(-1.8, 2.4, -1.2);
    pcbFill.angle = Math.PI / 3.0;
    scene.add(pcbFill);

    const pcbAmb = new THREE.AmbientLight(0xd1e3f8, 1.5);
    scene.add(pcbAmb);

    const pcbGroup = new THREE.Group();
    scene.add(pcbGroup);
    pcbSpot.target = pcbGroup;

    // PCB FR-4 SUBSTRATE (Authentic Emerald Green Solder Mask)
    // Scale ~2.2 x 1.4 units
    const pcbCanvas = document.createElement("canvas");
    pcbCanvas.width = 1024;
    pcbCanvas.height = 768;
    const pcbG = pcbCanvas.getContext("2d");
    if (pcbG) {
      pcbG.fillStyle = "#0c3b24"; // FR-4 green
      pcbG.fillRect(0, 0, 1024, 768);

      // Copper trace grid lines
      pcbG.strokeStyle = "#1b5e39";
      pcbG.lineWidth = 1.5;
      for (let x = 32; x < 1024; x += 32) {
        pcbG.beginPath();
        pcbG.moveTo(x, 0);
        pcbG.lineTo(x, 768);
        pcbG.stroke();
      }
      for (let y = 32; y < 768; y += 32) {
        pcbG.beginPath();
        pcbG.moveTo(0, y);
        pcbG.lineTo(1024, y);
        pcbG.stroke();
      }

      // Ground plane bus tracks
      pcbG.strokeStyle = "#277a4d";
      pcbG.lineWidth = 4;
      pcbG.strokeRect(24, 24, 976, 720);
      pcbG.strokeRect(320, 48, 670, 670);

      // Gold silkscreen markings
      pcbG.fillStyle = "#fef08a";
      pcbG.font = "bold 26px monospace";
      pcbG.fillText("KORG INC. MADE IN JAPAN", 50, 720);
      pcbG.font = "bold 22px monospace";
      pcbG.fillText("KLM-1266 MAIN CORE ASS'Y", 50, 680);
      pcbG.font = "14px monospace";
      pcbG.fillText("REV 1988 · uPD70216 V50 16-BIT ARCHITECTURE", 50, 650);

      // Silkscreen chip labels
      KLM1266_CHIPS.forEach((chip) => {
        const cx = ((chip.x + 1.1) / 2.2) * 1024;
        const cy = ((chip.z + 0.7) / 1.4) * 768;
        pcbG.fillStyle = "#fef08a";
        pcbG.font = "bold 13px monospace";
        pcbG.fillText(`${chip.label}: ${chip.partNumber.slice(0, 18)}`, cx - 60, cy - 35);
      });
    }

    const pcbTex = new THREE.CanvasTexture(pcbCanvas);
    const pcbMat = new THREE.MeshStandardMaterial({
      map: pcbTex,
      roughness: 0.45,
      metalness: 0.18,
    });
    const pcbBoard = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.035, 1.4), pcbMat);
    pcbBoard.receiveShadow = true;
    pcbGroup.add(pcbBoard);

    // Corner mounting holes / standoffs
    const standoffMat = new THREE.MeshStandardMaterial({ color: 0xd4af37, metalness: 0.8, roughness: 0.3 });
    const holePositions = [
      [-1.02, -0.62],
      [1.02, -0.62],
      [-1.02, 0.62],
      [1.02, 0.62],
      [0.0, -0.62],
      [0.0, 0.62],
    ];
    holePositions.forEach(([hx, hz]) => {
      const ring = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.04, 16), standoffMat);
      ring.position.set(hx, 0.02, hz);
      pcbGroup.add(ring);
    });

    // CHIPS ON PCB
    const chipMeshes: THREE.Mesh[] = [];
    KLM1266_CHIPS.forEach((chip) => {
      const chipMat = new THREE.MeshStandardMaterial({
        color: chip.color,
        roughness: 0.35,
        metalness: chip.id === "battery" ? 0.8 : 0.2,
      });

      let chipMesh: THREE.Mesh;
      if (chip.id === "battery") {
        chipMesh = new THREE.Mesh(
          new THREE.CylinderGeometry(chip.w / 2, chip.w / 2, chip.h, 24),
          chipMat,
        );
      } else {
        chipMesh = new THREE.Mesh(
          new THREE.BoxGeometry(chip.w, chip.h, chip.d),
          chipMat,
        );
      }
      chipMesh.position.set(chip.x, 0.018 + chip.h / 2, chip.z);
      chipMesh.castShadow = true;
      chipMesh.receiveShadow = true;
      chipMesh.userData.chip = chip;
      pcbGroup.add(chipMesh);
      chipMeshes.push(chipMesh);

      // Gold pins / solder leads around the chip
      if (chip.id !== "battery") {
        const pinMat = new THREE.MeshStandardMaterial({ color: 0xd4d4d8, metalness: 0.9, roughness: 0.2 });
        const pinStrips = [
          new THREE.Mesh(new THREE.BoxGeometry(chip.w + 0.03, 0.008, chip.d * 0.8), pinMat),
          new THREE.Mesh(new THREE.BoxGeometry(chip.w * 0.8, 0.008, chip.d + 0.03), pinMat),
        ];
        pinStrips.forEach((ps) => {
          ps.position.set(chip.x, 0.02, chip.z);
          pcbGroup.add(ps);
        });
      }
    });

    // RAYCASTING FOR PCB CHIP CLICKS
    const pcbRay = new THREE.Raycaster();
    const pcbPtr = new THREE.Vector2();

    const onPcbClick = (e: MouseEvent) => {
      const r = renderer.domElement.getBoundingClientRect();
      pcbPtr.x = ((e.clientX - r.left) / r.width) * 2 - 1;
      pcbPtr.y = -((e.clientY - r.top) / r.height) * 2 + 1;
      pcbRay.setFromCamera(pcbPtr, camera);

      const hits = pcbRay.intersectObjects(chipMeshes);
      if (hits.length > 0) {
        const hit = hits[0].object as THREE.Mesh;
        const chip = hit.userData.chip as ChipInfo;
        if (chip) {
          setInspectedChip(chip);
          pcbCamFocusRef.current?.(chip.x, chip.z);
        }
      }
    };
    renderer.domElement.addEventListener("click", onPcbClick);

    // ORBIT
    let dragging = false;
    let px = 0;
    let py = 0;
    const down = (e: MouseEvent) => { dragging = true; px = e.clientX; py = e.clientY; };
    const move = (e: MouseEvent) => {
      if (!dragging) return;
      theta -= (e.clientX - px) * 0.006;
      phi = Math.min(1.3, Math.max(0.15, phi - (e.clientY - py) * 0.006));
      px = e.clientX;
      py = e.clientY;
      updateCam();
    };
    const up = () => { dragging = false; };
    const wheel = (e: WheelEvent) => {
      radius = Math.min(4.5, Math.max(1.0, radius + e.deltaY * 0.002));
      updateCam();
    };

    renderer.domElement.addEventListener("mousedown", down);
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    renderer.domElement.addEventListener("wheel", wheel);

    const onResize = () => {
      const w = mount.clientWidth || 600;
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
      renderer.domElement.removeEventListener("click", onPcbClick);
      renderer.domElement.removeEventListener("mousedown", down);
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
      renderer.domElement.removeEventListener("wheel", wheel);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, []);

  const filteredPrograms = M1_100_PROGRAMS.filter((p) => {
    const matchesCat = selectedCategory === "All" || p.category === selectedCategory;
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      p.id.toLowerCase().includes(q) ||
      p.name.toLowerCase().includes(q) ||
      p.description.toLowerCase().includes(q) ||
      p.osc1Sample.toLowerCase().includes(q) ||
      (p.osc2Sample && p.osc2Sample.toLowerCase().includes(q)) ||
      (p.famousUse && p.famousUse.toLowerCase().includes(q));
    return matchesCat && matchesSearch;
  });

  const filteredCombis = M1_100_COMBIS.filter((c) => {
    const q = searchQuery.toLowerCase().trim();
    return (
      !q ||
      c.id.toLowerCase().includes(q) ||
      c.name.toLowerCase().includes(q) ||
      c.description.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-8 p-4 max-w-7xl mx-auto">
      {/* 1. Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-sky-500/20 px-2 py-0.5 text-xs font-semibold text-sky-400 border border-sky-500/30">
              1988 Workstation Flagship
            </span>
            <span className="text-xs text-slate-400 font-mono">
              KLM-1266 · NEC V50 · Dual Tone Generator ASIC
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1 flex items-center gap-2">
            <Music className="h-6 w-6 text-sky-400" />
            Korg M1 Music Workstation
          </h1>
          <p className="text-sm text-slate-400">
            Interactive Three.js hardware visualizer with high-intensity studio spotlight, playable Web Audio synthesis engine, KLM-1266 PCB 3D viewer, and ambient sound archives.
          </p>
        </div>

        {/* Status Pills */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 rounded-md bg-slate-900 border border-slate-700/80 px-3 py-1.5 text-slate-300">
            <Radio className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
            <span>Mode:</span>
            <span className="font-semibold text-sky-400">{selectedMode}</span>
          </div>
          <div className="flex items-center gap-1.5 rounded-md bg-slate-900 border border-slate-700/80 px-3 py-1.5 text-slate-300">
            <Sliders className="h-3.5 w-3.5 text-amber-400" />
            <span>Patch:</span>
            <span className="font-semibold text-amber-300">{selectedPatch.name}</span>
          </div>
          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className={`flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition ${
              audioEnabled
                ? "bg-emerald-950/60 border-emerald-600 text-emerald-300 hover:bg-emerald-900/60"
                : "bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700"
            }`}
          >
            <Volume2 className="h-3.5 w-3.5" />
            {audioEnabled ? "Synth Audio: ON" : "Synth Audio: MUTED"}
          </button>
        </div>
      </div>

      {/* 2. Main 3D Viewport: Korg M1 Synth Workstation */}
      <div
        ref={stageSynthRef}
        className={`relative rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl ${
          isFullscreenSynth ? "h-screen w-screen border-none rounded-none" : ""
        }`}
      >
        {/* Top Control Bar inside Viewport */}
        <div className="absolute top-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
          {/* LCD HUD Readout */}
          <div className="pointer-events-auto rounded-lg bg-emerald-950/90 border border-emerald-600/50 px-3 py-2 shadow-lg backdrop-blur font-mono text-emerald-300">
            <div className="text-[10px] uppercase tracking-wider text-emerald-500 font-bold flex items-center justify-between">
              <span>HD44780 2x40 LCD</span>
              <span className="text-[9px] bg-emerald-900/60 px-1 rounded text-emerald-400">31.25 kHz PCM</span>
            </div>
            <div className="text-xs font-bold text-emerald-200 mt-0.5">{lcdLine1}</div>
            <div className="text-xs text-emerald-400">{lcdLine2}</div>
          </div>

          {/* Quick Camera & Lighting Controls & Fullscreen */}
          <div className="pointer-events-auto flex items-center gap-2 bg-slate-900/90 border border-slate-700/80 rounded-lg p-1.5 backdrop-blur shadow-lg">
            <span className="text-xs text-slate-400 px-1.5 font-medium flex items-center gap-1">
              <Sun className="h-3.5 w-3.5 text-amber-400" />
              Spotlight:
            </span>
            <input
              type="range"
              min="1"
              max="14"
              step="0.5"
              value={spotlightIntensity}
              onChange={(e) => setSpotlightIntensity(parseFloat(e.target.value))}
              className="w-20 accent-amber-400 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
              title={`Spotlight Intensity: ${spotlightIntensity}x`}
            />
            <span className="text-xs font-mono text-amber-300 w-8 text-right">{spotlightIntensity}x</span>

            <div className="h-4 w-px bg-slate-700 mx-1" />

            {/* Ambient Boost Toggle */}
            <button
              onClick={() => setAmbientIntensity((prev) => (prev > 1.8 ? 1.0 : prev > 1.2 ? 2.4 : 1.6))}
              className="text-xs rounded px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1 transition"
              title="Cycle Ambient Fill Light"
            >
              Fill: <span className="font-mono text-sky-300">{ambientIntensity}x</span>
            </button>

            <div className="h-4 w-px bg-slate-700 mx-1" />

            {/* Fullscreen Button */}
            <button
              onClick={toggleSynthFullscreen}
              className="text-xs rounded px-2 py-1 bg-sky-950 hover:bg-sky-900 text-sky-300 border border-sky-700/60 flex items-center gap-1 transition"
              title={isFullscreenSynth ? "Exit Fullscreen" : "Fullscreen Synth Viewport"}
            >
              {isFullscreenSynth ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
              <span>{isFullscreenSynth ? "Exit" : "Fullscreen"}</span>
            </button>
          </div>
        </div>

        {/* Floating Web MIDI & Physical PC Keyboard Status Pills */}
        <div className="absolute top-16 left-3 z-10 pointer-events-auto flex flex-wrap gap-2">
          <div className={`rounded-lg px-2.5 py-1 text-[11px] backdrop-blur border flex items-center gap-1.5 shadow ${
            midiConnected
              ? "bg-emerald-950/80 border-emerald-500/50 text-emerald-300"
              : "bg-slate-900/80 border-slate-700/60 text-slate-400"
          }`}>
            <Activity className="h-3 w-3 text-emerald-400" />
            <span>Web MIDI: <strong className="text-slate-200">{midiDeviceName}</strong></span>
          </div>

          <div className="rounded-lg bg-sky-950/80 border border-sky-500/40 px-2.5 py-1 text-[11px] text-sky-200 backdrop-blur shadow flex items-center gap-1.5">
            <Music className="h-3 w-3 text-sky-400" />
            <span>PC Keys <kbd className="bg-slate-800 px-1 rounded text-amber-300">A-W-S-E-D-F-T-G-Y-H-U-J-K</kbd> = C4–C5</span>
          </div>
        </div>

        {/* Bottom Camera Angles Bar inside Viewport */}
        <div className="absolute bottom-3 left-3 z-10 pointer-events-auto flex flex-wrap items-center gap-1.5 bg-slate-900/80 border border-slate-800 rounded-lg p-1.5 backdrop-blur">
          <span className="text-[11px] text-slate-400 px-1 font-semibold uppercase tracking-wider">Angles:</span>
          <button
            onClick={() => setCamViewRef.current?.(0.42, 1.05, 3.4)}
            className="text-xs rounded bg-slate-800 hover:bg-slate-700 px-2.5 py-1 text-slate-200 border border-slate-700/60"
          >
            Isometric
          </button>
          <button
            onClick={() => setCamViewRef.current?.(0.02, 0.42, 2.6)}
            className="text-xs rounded bg-slate-800 hover:bg-slate-700 px-2.5 py-1 text-slate-200 border border-slate-700/60"
          >
            Cockpit (Keys)
          </button>
          <button
            onClick={() => setCamViewRef.current?.(0.01, 0.08, 2.8)}
            className="text-xs rounded bg-slate-800 hover:bg-slate-700 px-2.5 py-1 text-slate-200 border border-slate-700/60"
          >
            Deck Top
          </button>
          <button
            onClick={() => setCamViewRef.current?.(1.52, 1.15, 3.2)}
            className="text-xs rounded bg-slate-800 hover:bg-slate-700 px-2.5 py-1 text-slate-200 border border-slate-700/60"
          >
            Left Joystick
          </button>
        </div>

        {/* 3D Canvas Mount */}
        <div
          ref={mountRef}
          className="w-full cursor-grab active:cursor-grabbing"
          style={{ height: isFullscreenSynth ? "100vh" : 500 }}
        />
      </div>

      {/* 3. EXTRA THREE.JS VIEWER: KLM-1266 MOTHERBOARD SILICON INSPECTION */}
      <div
        ref={stagePcbRef}
        className={`rounded-xl border border-slate-800 bg-slate-900/70 overflow-hidden shadow-xl ${
          isFullscreenPcb ? "h-screen w-screen border-none rounded-none fixed inset-0 z-50 bg-slate-950" : ""
        }`}
      >
        <div className="border-b border-slate-800 bg-slate-950/80 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Microchip className="h-5 w-5 text-emerald-400" />
              <h2 className="text-base font-bold text-slate-100">
                KLM-1266 Main Logic Motherboard — 3D Silicon Inspection
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Interactive 3D board teardown. Click any IC chip to inspect bus mapped registers, pinout function, and hardware telemetry.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 flex items-center gap-1">
              <Sun className="h-3.5 w-3.5 text-amber-400" />
              PCB Spot:
            </span>
            <input
              type="range"
              min="1"
              max="10"
              step="0.5"
              value={pcbSpotlight}
              onChange={(e) => setPcbSpotlight(parseFloat(e.target.value))}
              className="w-20 accent-amber-400 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
            />
            <span className="font-mono text-amber-300 w-8 text-right">{pcbSpotlight}x</span>

            <button
              onClick={togglePcbFullscreen}
              className="ml-2 text-xs rounded px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1"
            >
              {isFullscreenPcb ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
              <span>{isFullscreenPcb ? "Exit" : "Fullscreen"}</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
          {/* 3D PCB Canvas Viewport (7 Cols) */}
          <div className="lg:col-span-7 relative bg-slate-950 border-b lg:border-b-0 lg:border-r border-slate-800">
            <div
              ref={pcbMountRef}
              className="w-full cursor-grab active:cursor-grabbing"
              style={{ height: isFullscreenPcb ? "calc(100vh - 70px)" : 420 }}
            />
            <div className="absolute bottom-2 left-2 z-10 text-[10px] text-slate-400 bg-slate-900/80 px-2 py-1 rounded border border-slate-800">
              Drag to Orbit · Wheel to Zoom · Click chips to inspect
            </div>
          </div>

          {/* Silicon Inspection Detail Card (5 Cols) */}
          <div className="lg:col-span-5 p-5 flex flex-col justify-between space-y-4 bg-slate-900/40">
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="rounded bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-xs font-mono font-bold text-emerald-400">
                  {inspectedChip.label} · {inspectedChip.package}
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  {inspectedChip.busRange}
                </span>
              </div>

              <div>
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-1.5">
                  {inspectedChip.partNumber}
                </h3>
                <p className="text-xs font-semibold text-sky-400 mt-0.5">
                  {inspectedChip.name}
                </p>
              </div>

              <div className="rounded-lg bg-slate-950 border border-slate-800/80 p-3 text-xs text-slate-300 leading-relaxed font-sans">
                {inspectedChip.description}
              </div>
            </div>

            {/* Quick Chip Preset Focus Selector */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Direct Silicon Jump:
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {KLM1266_CHIPS.map((chip) => {
                  const isCurrent = inspectedChip.id === chip.id;
                  return (
                    <button
                      key={chip.id}
                      onClick={() => {
                        setInspectedChip(chip);
                        pcbCamFocusRef.current?.(chip.x, chip.z);
                      }}
                      className={`px-2 py-1 text-left text-xs rounded border truncate transition font-mono ${
                        isCurrent
                          ? "bg-sky-500/20 border-sky-500 text-sky-200 font-bold"
                          : "bg-slate-800/60 border-slate-700/60 text-slate-300 hover:bg-slate-700/60"
                      }`}
                    >
                      {chip.label} {chip.partNumber.split(" ")[0]}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. AUTHENTIC KORG M1 FACTORY SOUNDBANK BROWSER (100 PROGRAMS & 100 COMBIS) */}
      <div className="rounded-xl border border-sky-900/40 bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950/40 p-6 space-y-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Disc className="h-5 w-5 text-sky-400" />
              <h2 className="text-lg font-bold text-slate-100">
                Official Korg M1 Factory Preload Soundbank (MPC-00P / NVRAM 64KB)
              </h2>
            </div>
            <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
              Every single authentic preset from the 1988 factory release. The M1 is an <strong>AI PCM Rompler</strong>:
              its timbres are built from 4 Megabytes of uncompressed 16-bit acoustic sample recordings (PCM #00–#99)
              streamed through custom Fujitsu MB87402 Tone Generator ASICs. Click any preset to update the 3D M1 hardware display
              and broadcast MIDI Program Change <code className="text-sky-300 font-mono">0xC0 [num]</code> to your DAW or external VST3 module.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <div className="flex items-center gap-1.5 text-xs text-slate-300 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800">
              <Volume2 className="h-3.5 w-3.5 text-sky-400" />
              <span>Vol:</span>
              <input
                type="range"
                min="0"
                max="100"
                value={volume}
                onChange={(e) => setVolume(parseInt(e.target.value))}
                className="w-16 accent-sky-400 h-1.5 bg-slate-700 rounded-lg cursor-pointer"
              />
              <span className="font-mono text-slate-300 w-7">{volume}%</span>
            </div>
          </div>
        </div>

        {/* Filter bar: Bank Tabs, Search, Category Pills */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            {/* Bank switcher */}
            <div className="flex rounded-lg bg-slate-950 p-1 border border-slate-800 shrink-0 w-full sm:w-auto">
              <button
                onClick={() => setBankTab("programs")}
                className={`flex-1 sm:flex-none px-4 py-1.5 rounded-md text-xs font-bold transition ${
                  bankTab === "programs"
                    ? "bg-sky-500 text-slate-950 shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                100 Factory Programs (Prog 00–99)
              </button>
              <button
                onClick={() => setBankTab("combis")}
                className={`flex-1 sm:flex-none px-4 py-1.5 rounded-md text-xs font-bold transition ${
                  bankTab === "combis"
                    ? "bg-indigo-500 text-slate-950 shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                100 Factory Combinations (Combi 00–99)
              </button>
            </div>

            {/* Search Input */}
            <div className="relative w-full sm:w-80">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                placeholder={
                  bankTab === "programs"
                    ? "Search programs (Ooh, Universe, Piano, Brass)..."
                    : "Search combinations (Film Score, Harvest)..."
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>
          </div>

          {/* Category Filter Pills (when in programs mode) */}
          {bankTab === "programs" && (
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
              {[
                "All",
                "Vocal / Choir",
                "Piano / Keyboard",
                "Pad / Ambient",
                "Brass",
                "Strings",
                "Bass",
                "Guitar / Pluck",
                "Ethnic / Bell",
                "Drums / Perc",
                "Synth / Lead",
                "SFX / Split",
              ].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded text-[11px] font-semibold whitespace-nowrap transition ${
                    selectedCategory === cat
                      ? "bg-sky-950 text-sky-300 border border-sky-600/60 shadow-sm"
                      : "bg-slate-950/80 text-slate-400 hover:text-slate-200 border border-slate-800/80 hover:bg-slate-800/50"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 100 Programs Grid */}
        {bankTab === "programs" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>Showing {filteredPrograms.length} of 100 Factory Programs (MPC-00P ROM)</span>
              <span className="hidden sm:inline">Clicking preset transmits MIDI Program Change <code className="text-sky-300 font-bold">0xC0 [num]</code> to VST3</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[620px] overflow-y-auto pr-2 scrollbar-thin">
              {filteredPrograms.map((prog) => {
                const isSelected = selectedProgram.num === prog.num && selectedMode === "PROG";
                return (
                  <div
                    key={prog.num}
                    onClick={() => handleSelectProgram(prog)}
                    className={`rounded-xl border p-4 flex flex-col justify-between cursor-pointer transition-all duration-200 ${
                      isSelected
                        ? "bg-sky-950/70 border-sky-500 shadow-lg shadow-sky-500/15 ring-1 ring-sky-500/60"
                        : "bg-slate-950/80 border-slate-800/90 hover:border-slate-700 hover:bg-slate-900/70"
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800/50">
                          PROG {prog.id}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                            {prog.oscMode}
                          </span>
                          <span className="text-[11px] font-medium text-slate-400">{prog.category}</span>
                        </div>
                      </div>

                      <h3 className="text-sm font-bold text-slate-100 flex items-center justify-between">
                        <span>{prog.id}: {prog.name}</span>
                        {isSelected && (
                          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/80 px-1.5 py-0.5 rounded border border-emerald-600/40">
                            ACTIVE
                          </span>
                        )}
                      </h3>

                      <p className="text-xs text-slate-300 leading-relaxed min-h-[38px]">
                        {prog.description}
                      </p>

                      <div className="rounded bg-slate-900/90 border border-slate-800 p-2 space-y-1 text-[11px] font-mono">
                        <div className="text-slate-400 truncate">
                          <span className="text-slate-500 font-sans">PCM 1: </span>{prog.osc1Sample}
                        </div>
                        {prog.osc2Sample && (
                          <div className="text-slate-400 truncate">
                            <span className="text-slate-500 font-sans">PCM 2: </span>{prog.osc2Sample}
                          </div>
                        )}
                        {prog.famousUse && (
                          <div className="text-slate-300 font-sans text-[11px] pt-0.5">
                            <span className="text-slate-500">Heard in: </span>
                            <span className="text-amber-300 font-medium">{prog.famousUse}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="pt-2 mt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                      <span className="font-mono text-slate-400">VDF Cutoff: {prog.vdfCutoff}</span>
                      <span className="text-sky-400 font-medium flex items-center gap-1">
                        Select & MIDI Prog <Play className="h-2.5 w-2.5 fill-current" />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 100 Combinations Grid */}
        {bankTab === "combis" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>Showing {filteredCombis.length} of 100 Factory Combinations (8-Part Multi-Timbral)</span>
              <span className="hidden sm:inline">Clicking combi transmits MIDI Program Change <code className="text-indigo-300 font-bold">0xC0 [num]</code> to VST3</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[620px] overflow-y-auto pr-2 scrollbar-thin">
              {filteredCombis.map((combi) => {
                const isSelected = selectedCombi.num === combi.num && selectedMode === "COMBI";
                return (
                  <div
                    key={combi.num}
                    onClick={() => handleSelectCombi(combi)}
                    className={`rounded-xl border p-4 flex flex-col justify-between cursor-pointer transition-all duration-200 ${
                      isSelected
                        ? "bg-indigo-950/70 border-indigo-500 shadow-lg shadow-indigo-500/15 ring-1 ring-indigo-500/60"
                        : "bg-slate-950/80 border-slate-800/90 hover:border-slate-700 hover:bg-slate-900/70"
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800/50">
                          COMBI {combi.id}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                          {combi.type}
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-slate-100 flex items-center justify-between">
                        <span>{combi.id}: {combi.name}</span>
                        {isSelected && (
                          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/80 px-1.5 py-0.5 rounded border border-emerald-600/40">
                            ACTIVE
                          </span>
                        )}
                      </h3>

                      <p className="text-xs text-slate-300 leading-relaxed min-h-[38px]">
                        {combi.description}
                      </p>

                      <div className="rounded bg-slate-900/90 border border-slate-800 p-2 space-y-1 text-[11px] font-mono">
                        <span className="text-slate-500 font-sans">Layered Programs:</span>
                        <div className="flex flex-wrap gap-1 pt-1">
                          {combi.programs.map((p, idx) => (
                            <span key={idx} className="bg-slate-800 text-sky-300 px-1.5 py-0.5 rounded text-[10px]">
                              {p}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="pt-2 mt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                      <span className="font-mono text-slate-400">8-Part Multi-Timbral</span>
                      <span className="text-indigo-400 font-medium flex items-center gap-1">
                        Select & MIDI Prog <Play className="h-2.5 w-2.5 fill-current" />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 5. Technical Dossiers & Reversing Tabs */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-800 bg-slate-950/80 overflow-x-auto">
          <button
            onClick={() => setActiveTab("arch")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "arch"
                ? "border-sky-500 text-sky-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Cpu className="h-4 w-4 text-sky-400" />
            AI Synthesis & Specs
          </button>
          <button
            onClick={() => setActiveTab("silicon")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "silicon"
                ? "border-sky-500 text-sky-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Layers className="h-4 w-4 text-indigo-400" />
            Silicon & Logic Boards
          </button>
          <button
            onClick={() => setActiveTab("restore")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "restore"
                ? "border-sky-500 text-sky-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <RotateCcw className="h-4 w-4 text-amber-400" />
            NVRAM & Pi Implant
          </button>
          <button
            onClick={() => setActiveTab("culture")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "culture"
                ? "border-sky-500 text-sky-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Disc className="h-4 w-4 text-purple-400" />
            Cultural Impact & 90s Hits
          </button>
          <button
            onClick={() => setActiveTab("vst")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "vst"
                ? "border-amber-500 text-amber-300 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
            }`}
          >
            <Sliders className="h-4 w-4 text-amber-400" />
            VST3 & Reversed Emulation
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* TAB 1: AI SYNTHESIS & ARCHITECTURE */}
          {activeTab === "arch" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4">
                  <div className="flex items-center gap-2 text-sky-400 font-semibold text-sm mb-2">
                    <Music className="h-4 w-4" />
                    Polyphony & Sound Engine
                  </div>
                  <ul className="text-xs text-slate-300 space-y-1.5 font-mono">
                    <li>• <span className="text-slate-400">Polyphony:</span> 16 voices (Single), 8 voices (Double)</li>
                    <li>• <span className="text-slate-400">Synthesis:</span> AI (Advanced Integrated) PCM</li>
                    <li>• <span className="text-slate-400">Multitimbral:</span> 8-part dynamic voice allocation</li>
                    <li>• <span className="text-slate-400">Keybed:</span> 61-key Yamaha FS-61 action</li>
                    <li>• <span className="text-slate-400">Sensors:</span> Velocity + Channel Aftertouch</li>
                  </ul>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4">
                  <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm mb-2">
                    <Disc className="h-4 w-4" />
                    Waveform ROM & Envelopes
                  </div>
                  <ul className="text-xs text-slate-300 space-y-1.5 font-mono">
                    <li>• <span className="text-slate-400">PCM ROM:</span> 4 MB 16-bit linear @ 31.25 kHz</li>
                    <li>• <span className="text-slate-400">Instruments:</span> 100 Multi-Sound PCM instruments</li>
                    <li>• <span className="text-slate-400">Drums:</span> 44 internal drum/percussion sounds</li>
                    <li>• <span className="text-slate-400">Filters:</span> Dual VDF (digital low-pass)</li>
                    <li>• <span className="text-slate-400">Envelopes:</span> Six 8-stage EGs per voice</li>
                  </ul>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4">
                  <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm mb-2">
                    <Sliders className="h-4 w-4" />
                    Effects & Sequencer
                  </div>
                  <ul className="text-xs text-slate-300 space-y-1.5 font-mono">
                    <li>• <span className="text-slate-400">Effects DSP:</span> Dual MDE (33 algorithms)</li>
                    <li>• <span className="text-slate-400">FX Types:</span> Hall, Room, Chorus, Delay, Exciter</li>
                    <li>• <span className="text-slate-400">Sequencer:</span> 8-track MIDI sequencer</li>
                    <li>• <span className="text-slate-400">Capacity:</span> 7,700 notes, 10 songs, 100 patterns</li>
                    <li>• <span className="text-slate-400">Power:</span> 11 W nominal power draw</li>
                  </ul>
                </div>
              </div>

              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 space-y-3">
                <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-sky-400" />
                  Why the M1 Defined the Modern "Workstation"
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Introduced in May 1988, the Korg M1 single-handedly established the concept of the <strong>Music Workstation</strong>.
                  Before the M1, a music producer needed an FM or analog synth, a separate rackmount sampler, an outboard digital reverb unit,
                  and an external computer or hardware sequencer. The M1 condensed the entire recording studio into a single sleek 13.5 kg instrument:
                  pristine 16-bit acoustic sample playback, two independent digital multi-effects units, an 8-track sequencer, and a comprehensive master keyboard controller.
                </p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Its 4 MB PCM ROM was voiced by a legendary sound design team including Peter Busch, Jack Hotop, and Akiyama-san.
                  Instead of attempting cold clinical reproduction, the sounds were engineered to slice aggressively through dense dance mixes without requiring outboard EQ.
                </p>
              </div>
            </div>
          )}

          {/* TAB 2: SILICON & HARDWARE ARCHITECTURE */}
          {activeTab === "silicon" && (
            <div className="space-y-6">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border border-slate-800 rounded-lg overflow-hidden">
                  <thead className="bg-slate-950 text-slate-300 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Subsystem</th>
                      <th className="py-2.5 px-3 font-semibold">Part Number</th>
                      <th className="py-2.5 px-3 font-semibold">Memory / Bus Range</th>
                      <th className="py-2.5 px-3 font-semibold">Technical Function</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Main Processor</td>
                      <td className="py-2 px-3 text-amber-300">NEC uPD70216 (V50)</td>
                      <td className="py-2 px-3">16-bit x86 architecture @ 16 MHz</td>
                      <td className="py-2 px-3 font-sans">Coordinates UI, MIDI parser, sequencer timing, and voice assignment.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Tone Generators</td>
                      <td className="py-2 px-3 text-amber-300">Fujitsu MB87402 x2</td>
                      <td className="py-2 px-3">0x1000 – 0x11FF</td>
                      <td className="py-2 px-3 font-sans">Custom Korg TG silicon; reads PCM sample ROM and interpolates 16 voices.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Variable Digital Filter</td>
                      <td className="py-2 px-3 text-amber-300">Fujitsu MB87404 x2</td>
                      <td className="py-2 px-3">0x0100 / 0x0200</td>
                      <td className="py-2 px-3 font-sans">Dual 4-pole low-pass digital filters with resonance emulation.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Multi-Digital Effects</td>
                      <td className="py-2 px-3 text-amber-300">Fujitsu MB87405</td>
                      <td className="py-2 px-3">0x0500</td>
                      <td className="py-2 px-3 font-sans">Dedicated 24-bit DSP core running 33 stereo effect algorithms.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Panel Matrix PIO</td>
                      <td className="py-2 px-3 text-amber-300">Sony CXD1095Q</td>
                      <td className="py-2 px-3">0x0A00 (Y0..Y7 select)</td>
                      <td className="py-2 px-3 font-sans">Scans the 34 tactile front-panel switches, bank buttons, and data entry.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Audio DAC</td>
                      <td className="py-2 px-3 text-amber-300">PCM54HP (Burr-Brown)</td>
                      <td className="py-2 px-3">KLM-1261 Audio Board</td>
                      <td className="py-2 px-3 font-sans">Ultra-low distortion 16-bit monotonic linear DAC with op-amp smoothing.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Firmware IPL ROM</td>
                      <td className="py-2 px-3 text-amber-300">Fujitsu MB83512</td>
                      <td className="py-2 px-3">0xE0000 – 0xFFFFF (128 KB)</td>
                      <td className="py-2 px-3 font-sans">System bootloader, diagnostic test suites, and V50 interrupt vectors.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-sky-300 font-sans font-medium">Battery NVRAM</td>
                      <td className="py-2 px-3 text-amber-300">64 KB SRAM + CR2032</td>
                      <td className="py-2 px-3">0x00000 – 0x0FFFF</td>
                      <td className="py-2 px-3 font-sans">Stores 100 Programs, 100 Combinations, Global configs, and sequencer songs.</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-2">
                  <h4 className="text-xs font-semibold text-sky-300 uppercase tracking-wider">KLM Board Decomposition</h4>
                  <ul className="text-xs text-slate-400 space-y-1 font-mono">
                    <li>• <span className="text-slate-200">KLM-1266:</span> Motherboard (V50 CPU, TG, VDF, MDE, NVRAM, Mask ROM)</li>
                    <li>• <span className="text-slate-200">KLM-1261:</span> Audio Board (Burr-Brown PCM54HP DAC, Output Jacks)</li>
                    <li>• <span className="text-slate-200">KLM-1262:</span> Front Panel Surface (34 tactile buttons, 2x slide VRs)</li>
                    <li>• <span className="text-slate-200">KLM-1264:</span> Dual Card Expansion (BeeCard + MSC 19x2 pin sockets)</li>
                    <li>• <span className="text-slate-200">KLM-1267:</span> Linear PSU (+5V 1.2A, +12V 0.3A, -12V 0.13A)</li>
                  </ul>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-2">
                  <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">MAME Driver & Emulation State</h4>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    MAME includes a verified driver in <code className="text-sky-300 font-mono">src/mame/korg/korgm1.cpp</code> (authored by Angelo Salese & AJR).
                    The driver successfully boots the NEC V50 core, emulates the HD44780 LCD, maps the front-panel switch matrix, and parses SysEx.
                    In this fleet, the official Korg Collection M1 VST serves as the bit-accurate DSP ground truth.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: RESTORATION & PI CARRIER IMPLANT */}
          {activeTab === "restore" && (
            <div className="space-y-6">
              <div className="rounded-lg bg-amber-950/30 border border-amber-600/40 p-4 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-amber-300">
                    Attic M1 Failure Diagnosis: The CR2032 NVRAM Death Trap
                  </div>
                  <p className="text-xs text-amber-200/90 leading-relaxed">
                    Over 95% of non-functional Korg M1s found in attics and studios are <strong>fully functional in hardware</strong>.
                    When the original 3V CR2032 lithium cell drops below ~2.2V, the battery-backed 64 KB SRAM (<code className="font-mono">0x00000–0x0FFFF</code>) decays into random bit-rot.
                    Upon power-up, the M1 boots into blank presets, garbled characters on the HD44780 display, or silent INIT patches.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Restoration Guide */}
                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-3">
                  <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
                    <CheckCircle2 className="h-4 w-4" />
                    Factory Restoration Runbook (3 Steps)
                  </div>
                  <ol className="text-xs text-slate-300 space-y-2.5">
                    <li className="flex items-start gap-2">
                      <span className="font-mono text-emerald-400 font-bold">1.</span>
                      <div>
                        <strong className="text-slate-100">Install Coin-Cell Socket:</strong> Desolder the tabbed CR2032 on KLM-1266. Solder in a standard through-hole coin cell holder for future tool-free replacement.
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-mono text-emerald-400 font-bold">2.</span>
                      <div>
                        <strong className="text-slate-100">Service Mode Hard Reset:</strong> Hold down <code className="bg-slate-800 px-1 rounded text-sky-300">INT</code> + <code className="bg-slate-800 px-1 rounded text-sky-300">BANK HOLD</code> + <code className="bg-slate-800 px-1 rounded text-sky-300">0</code> while powering on to clear corrupted SRAM tables.
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-mono text-emerald-400 font-bold">3.</span>
                      <div>
                        <strong className="text-slate-100">Reload Factory Preload SysEx:</strong> Connect MIDI OUT of your interface to M1 MIDI IN. Transmit the official Korg preload file (<code className="text-amber-300 font-mono">M1_PRELOAD.SYX</code>) at standard 31,250 baud.
                      </div>
                    </li>
                  </ol>
                </div>

                {/* Pi CM5 Carrier Implant */}
                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-4 space-y-3">
                  <div className="flex items-center gap-2 text-sky-400 font-semibold text-sm">
                    <Cpu className="h-4 w-4" />
                    Pi CM5 / Carrier Implant Strategy (Reversible)
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    From our fleet retrofit blueprint (<code className="text-slate-200 font-mono">docs/MEGASYNTH_RETROFIT.md</code>):
                    the M1 keybed, steel chassis, and front panel can be converted into an autonomous modern megasynth without cutting metal:
                  </p>
                  <ul className="text-xs text-slate-400 space-y-1.5 font-mono">
                    <li>• <span className="text-slate-200">Carrier Plate:</span> Drop-in PCB on original KLM-1266 standoffs.</li>
                    <li>• <span className="text-slate-200">Keybed Scanning:</span> Replicate SCAN-port via GPIO + MCP23017.</li>
                    <li>• <span className="text-slate-200">LCD Bus:</span> Drive HD44780 in 4-bit mode directly from Pi GPIO.</li>
                    <li>• <span className="text-slate-200">Panel Matrix:</span> Y0..Y7 mapped 1:1 to <code className="text-sky-300">korgm1::PANEL_MATRIX</code>.</li>
                    <li>• <span className="text-slate-200">Audio Engine:</span> Pi CM5 Lite boots Linux + open CLAP/VST3 or MAME in 3 seconds.</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: CULTURAL IMPACT & 90S HITS */}
          {activeTab === "culture" && (
            <div className="space-y-6">
              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 space-y-3">
                <div className="flex items-center gap-2 text-purple-400 font-bold text-sm">
                  <Disc className="h-4 w-4" />
                  The Sonic Architecture of an Entire Decade
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Between 1988 and 1995, approximately <strong>250,000 units</strong> of the Korg M1 and M1R rack were sold worldwide,
                  surpassing the Yamaha DX7 to become the best-selling synthesizer in music history.
                  Its unmistakable presets became the defining acoustic bedrock of house music, Eurodance, pop, R&B, and Hollywood film scoring.
                </p>
              </div>
            </div>
          )}

          {/* TAB 5: M1 VST3 MODULE & REVERSED EMULATION ARCHITECTURE */}
          {activeTab === "vst" && (
            <div className="space-y-6">
              <div className="rounded-lg bg-slate-950 border border-slate-800 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 text-amber-400 font-bold text-base">
                    <Sliders className="h-5 w-5" />
                    Korg M1 VST3 Module & Reversed Emulation Architecture
                  </div>
                  <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
                    Why the M1 defies simple minisynth filter reconstruction: The M1 is an <strong>AI PCM Rompler</strong>.
                    Its legendary patches (<code className="text-sky-300">03 Ooh/Ahh</code>, <code className="text-sky-300">00 Universe</code>, <code className="text-sky-300">01 Piano 16'</code>)
                    are derived from <strong>4 Megabytes of compressed 16-bit 32 kHz raw studio acoustic recordings</strong> in mask ROMs
                    (<code className="text-amber-300 font-mono">m1_pcm1.bin</code>, <code className="text-amber-300 font-mono">m1_pcm2.bin</code>)
                    streamed by twin Fujitsu MB87402 Tone Generator ASICs.
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs font-mono text-emerald-400 bg-emerald-950/80 px-2.5 py-1 rounded border border-emerald-600/40">
                    Engine: 16-Bit PCM Rompler
                  </span>
                </div>
              </div>

              {/* MIDI Output Router to DAW / VST3 */}
              <div className="rounded-xl border border-sky-900/50 bg-slate-900/90 p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Radio className="h-4 w-4 text-sky-400 animate-pulse" />
                    <span className="text-sm font-bold text-slate-100">
                      Live Web MIDI Output Router (Connect to DAW / VST3)
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-400">
                    Bridges 3D Keybed + PC Keys (A–K) + Program Changes directly to your VST3
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  <div className="space-y-1.5 md:col-span-2">
                    <label className="text-slate-300 font-medium">Select Active MIDI Output Cable / Driver:</label>
                    <select
                      value={selectedMidiOutputId}
                      onChange={(e) => handleSelectMidiOutput(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 font-mono focus:border-sky-500 focus:outline-none"
                    >
                      {midiOutputs.length === 0 ? (
                        <option value="">No MIDI Outputs Detected (Install loopMIDI for virtual DAW cable)</option>
                      ) : (
                        midiOutputs.map((out) => (
                          <option key={out.id} value={out.id}>
                            {out.name} ({out.id})
                          </option>
                        ))
                      )}
                    </select>
                    <p className="text-[11px] text-slate-400 leading-relaxed pt-1">
                      Tip: Use a free virtual MIDI cable like <strong className="text-slate-200">loopMIDI</strong> on Windows.
                      Select the loopMIDI port here and as the MIDI IN in your DAW (Reaper, Ableton, FL Studio, Cubase) on a track loaded with the Korg M1 VST3.
                      Every preset click will automatically send <code className="text-amber-300 font-mono">0xC0 [prog]</code>, and key presses will transmit real Note On/Off!
                    </p>
                  </div>

                  <div className="rounded-lg bg-slate-950 border border-slate-800 p-3 space-y-2 font-mono text-[11px]">
                    <div className="text-slate-400 flex justify-between">
                      <span>Status:</span>
                      <span className={selectedMidiOutputId ? "text-emerald-400 font-bold" : "text-amber-400"}>
                        {selectedMidiOutputId ? "LINKED TO VST3" : "STANDALONE"}
                      </span>
                    </div>
                    <div className="text-slate-400 flex justify-between">
                      <span>MIDI In:</span>
                      <span className="text-sky-300 truncate max-w-[140px]">{midiDeviceName}</span>
                    </div>
                    <div className="text-slate-400 flex justify-between">
                      <span>Active Program:</span>
                      <span className="text-amber-300 font-bold">PROG {selectedProgram.id}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Comparison of the "Reversed" Modules & Engines */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 1. Official KORG Collection M1 VST3 */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-emerald-400 font-mono">1. KORG COLLECTION M1 (VST3/AU)</span>
                    <span className="text-[10px] text-emerald-500 font-mono bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-600/30">
                      REFERENCE ORACLE
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    The gold standard in commercial reverse engineering. Korg's internal software engineering team extracted the exact
                    raw uncompressed PCM sample data from mask ROMs and translated the V50 assembly firmware into 64-bit native C++.
                  </p>

                  <ul className="text-xs text-slate-300 space-y-1.5 font-mono">
                    <li>• <span className="text-slate-400">Patches:</span> All 100 Programs + 100 Combinations + 19 Expansion Cards (&gt;3,300 sounds)</li>
                    <li>• <span className="text-slate-400">Audio Core:</span> Exact MB87404 VDF filter curves &amp; MB87405 24-bit MDE multi-effects</li>
                    <li>• <span className="text-slate-400">SysEx:</span> 100% native bit-accurate SysEx dump import/export (<code className="text-sky-300">.syx</code>)</li>
                    <li>• <span className="text-slate-400">Platform:</span> VST3 / AU / AAX / Standalone (Win / Mac)</li>
                  </ul>
                </div>

                {/* 2. Vintage Emulator Studio (VES) / MAME Core */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-sky-400 font-mono">2. VINTAGE EMULATOR STUDIO (VES VST3)</span>
                    <span className="text-[10px] text-sky-500 font-mono bg-sky-950/80 px-2 py-0.5 rounded border border-sky-600/30">
                      OPEN SOURCE (JUCE)
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    Created by Autodafe (<code className="text-sky-300">antoniograzioli/VintageEmulatorStudio</code> on GitHub).
                    A musician-focused DAW wrapper built in JUCE around the <strong>MAME emulation core</strong> (<code className="text-slate-200">src/mame/korg/korgm1.cpp</code>).
                  </p>

                  <ul className="text-xs text-slate-300 space-y-1.5 font-mono">
                    <li>• <span className="text-slate-400">License:</span> AGPL-3.0 Open Source VST3 &amp; Standalone</li>
                    <li>• <span className="text-slate-400">Hardware Core:</span> Emulates the NEC V50 CPU, memory-mapped I/O, and LCD display</li>
                    <li>• <span className="text-slate-400">ROM Requirement:</span> Requires user to supply MAME <code className="text-amber-300">korgm1.zip</code> ROM set</li>
                    <li>• <span className="text-slate-400">Emulation State:</span> Logic &amp; UI 100%; Fujitsu ASIC audio rendering is in active community development</li>
                  </ul>
                </div>
              </div>

              {/* 3. Official SysEx Preload Data & NVRAM Architecture */}
              <div className="rounded-xl border border-slate-800 bg-slate-950 p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="text-xs font-bold text-amber-400 font-mono">
                    3. KORG M1 64KB SRAM PRELOAD DUMP (<code className="text-slate-200">M1_PRELOAD.SYX</code>)
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">64 KB Battery-Backed NVRAM</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="space-y-2">
                    <p className="text-slate-300 leading-relaxed">
                      Every physical Korg M1 holds its complete 100 Programs and 100 Combinations in battery-backed SRAM located from
                      <code className="bg-slate-900 px-1 py-0.5 rounded text-sky-300 font-mono mx-1">0x00000–0x0FFFF</code>.
                      When the CR2032 battery dies, this entire table is zeroed out.
                    </p>
                    <p className="text-slate-400 leading-relaxed">
                      Restoration is achieved by transmitting the official Korg preload System Exclusive stream.
                      The stream uses Korg's proprietary 7-bit to 8-bit MIDI packing format with header:
                    </p>
                    <div className="bg-slate-900 p-2.5 rounded border border-slate-800 font-mono text-[11px] text-amber-300">
                      F0 42 30 19 4C [Data Blocks: 100 Prog + 100 Combi + Global] F7
                    </div>
                  </div>

                  <div className="rounded bg-slate-900/80 border border-slate-800 p-3 space-y-2">
                    <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                      <Download className="h-3.5 w-3.5 text-sky-400" />
                      Official Preload Resources &amp; Dumps
                    </div>
                    <ul className="text-[11px] text-slate-300 space-y-1.5">
                      <li>
                        • <strong className="text-slate-100">Korg Official Preload Dump:</strong> Available directly from Korg's archive support site (free SysEx download).
                      </li>
                      <li>
                        • <strong className="text-slate-100">SysEx Transfer Tools:</strong> MIDI-OX (Windows), Snoize SysEx Librarian (macOS), or Web MIDI SysEx Utility.
                      </li>
                      <li>
                        • <strong className="text-slate-100">Transmission Speed:</strong> Set buffer size to 256 bytes with 60ms delay between packets to prevent KLM-1266 buffer overrun.
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 6. Footer Info */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500 pt-2 border-t border-slate-800/80">
        <div className="flex items-center gap-1.5">
          <Info className="h-3.5 w-3.5 text-slate-400" />
          <span>Documentation sources: <span className="font-mono text-slate-400">docs/KORG_M1.md</span> · <span className="font-mono text-slate-400">docs/MEGASYNTH_RETROFIT.md</span> · <span className="font-mono text-slate-400">M1_Service_Manual.pdf</span></span>
        </div>
        <div className="font-mono text-slate-500">
          MAME driver: <span className="text-slate-400">src/mame/korg/korgm1.cpp</span> · Reverse Oracle: <span className="text-slate-400">Korg Collection M1</span>
        </div>
      </div>
    </div>
  );
}
