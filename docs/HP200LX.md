# HP 200LX Palmtop PC — Technical Dossier & Frankendingus Hardware Station

> **Target**: Hewlett-Packard HP 200LX Palmtop PC (1994)  
> **Classification**: Frankendingus Tier 0 (Attic specimen & intact daily driver)  
> **Interactive Station**: `/hardware-hp200lx` in `reversing-mcp/web_sota`  
> **Emulation Core**: PALM186 / DOSBox-X (640×200 CGA) / MAME `hp200lx`

---

## 1. Machine Overview

The **HP 200LX** (codenamed *Felix*, released August 1994 at $549 MSRP) represents the pinnacle of DOS-based handheld computing. Engineered by Hewlett-Packard's Corvallis, Oregon workstation division, it packed a full IBM PC XT compatible personal computer and complete office suite into a clamshell pocket form factor weighing just 312 grams (11 oz).

Unlike modern battery-hungry portable devices, the 200LX runs on **two standard 1.5V AA alkaline or NiMH cells for 30 to 40 hours of active continuous operation**, backed by a single CR2032 lithium coin cell that preserves volatile system RAM and real-time clock state across main battery hot-swaps.

```
┌──────────────────────────────────────────────────────────────────┐
│                   HP 200LX PALMTOP PC (1994)                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 640×200 CGA Monochrome Transflective LCD (Adjustable Pot)  │  │
│  │ Sunlight readable · 80 cols × 25 rows text · 40×16 zoom   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Blue Application Keys: [LOTUS 1-2-3] [CALC] [FILER] [MEMO] │  │
│  │ 80-key chiclet QWERTY keybed + dedicated numeric keypad    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  [PCMCIA Type II Slot]   [115.2 kbps Serial Port]   [IrDA FIR]   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Silicon Architecture

### 2.1 The Hornet ASIC (Intel 80186-Compatible SoC)
At the heart of the HP 200LX is the custom **"Hornet" ASIC** (HP part number 1820-9118 / 1820-9119), a static CMOS system-on-chip manufactured on an HP 0.8µm process. Hornet integrates:
- **Intel 80186-compatible 16-bit CPU core**: Running at **7.91 MHz** (derived from a 15.82 MHz master crystal divided by 2).
- **Static CMOS Design**: Capable of stopping the internal clock completely (`HALT` instruction drops core draw to under 1.5 mA).
- **CGA Graphics Controller**: Drives the 640×200 1-bit monochrome LCD panel with hardware horizontal/vertical smooth scrolling and font zoom logic (80×25 standard, 40×16 high-legibility mode).
- **Integrated DRAM Controller**: Manages 1 MB, 2 MB, or 4 MB internal static or pseudo-static RAM.
- **Interrupt & DMA Controllers**: 8259-compatible interrupt handling and custom serial transfer engines.
- **16550-Compatible UART**: Full RS-232 serial engine communicating through the proprietary 10-pin mini-serial connector at speeds up to 115,200 baud.
- **Infrared (SIR/IrDA) Transceiver**: HP 95LX / 100LX / 200LX line-of-sight wireless file transfer at 115.2 kbps.

### 2.2 Memory Map (3 MB Mask ROM & System RAM)
The 200LX memory space is divided between onboard RAM (configured dynamically via System Manager into conventional DOS memory and a RAM disk drive `C:`) and a **3 Megabyte Mask ROM** mapped from `D000:0000` to `FFFF:FFFF`:

| Memory Range | Region / Purpose | Contents |
|---|---|---|
| `0000:0000` – `0000:03FF` | Interrupt Vector Table | 256 hardware/software x86 interrupt vectors |
| `0000:0400` – `0000:04FF` | BIOS Data Area (BDA) | Equipment flags, keyboard buffer, COM/LPT bases |
| `0000:0500` – `9FFF:FFFF` | Conventional DOS RAM | 640 KB conventional DOS memory for user executables |
| `A000:0000` – `B7FF:FFFF` | CGA Video RAM | Screen buffer (640×200 1-bit graphics / 80×25 text) |
| `B800:0000` – `BFFF:FFFF` | CGA Text Mode Buffer | Emulated color-burst text memory window |
| `C000:0000` – `CFFF:FFFF` | PCMCIA Window | Configurable memory-mapped PCMCIA / CF card window |
| `D000:0000` – `FFFF:FFFF` | 3 MB System Mask ROM (`D:`) | MS-DOS 5.00, System Manager, Lotus 1-2-3, Quicken |

---

## 3. Built-In ROM Software Suite

The 3 MB Mask ROM (`Drive D:`) contains a full standalone computing suite that instant-boots in under 0.5 seconds with zero disk spinning latency:

1. **Lotus 1-2-3 Release 2.4**:
   - Complete, unabridged commercial release of the industry standard spreadsheet.
   - Supports 256 columns × 8192 rows (`.WK1` file format).
   - Full `@SUM`, `@NPV`, `@IRR`, `@LOOKUP`, financial calculations, matrix operations, and macro scripting engine.
   - Lotus Add-in Manager (WYSIWYG graphing and reporting).
2. **HP 19BII Business Consultant II Calculator**:
   - Advanced financial calculator supporting both algebraic and **RPN (Reverse Polish Notation)** modes.
   - Time Value of Money (TVM), cash flows (NPV/IRR), amortization schedules, depreciation, and statistical regression.
   - HP Solve equation solver allowing arbitrary formula entry and variable resolution.
3. **Microsoft MS-DOS 5.00**:
   - Full MS-DOS kernel and standard utilities (`COMMAND.COM`, `FDISK`, `FORMAT`, `DEBUG`, `EDLIN`).
   - Native FAT16 file system driver.
4. **Pocket Quicken (Intuit)**:
   - Handheld personal and business accounting ledger with checkbook reconciliation.
5. **cc:Mail Remote Mobile Client**:
   - Enterprise messaging terminal connecting over Hayes-compatible modem / serial.
6. **System Manager PIM Utilities**:
   - Appointment Book, Phone Book, World Time Clock, Memo Editor, Data Base engine, and Filer.
   - Single-key instant context-switching across all applications via dedicated blue top-row keys.

---

## 4. Hardware Storage & The PCMCIA Ecosystem

The left side of the chassis features a full **PCMCIA Type II (Release 2.01)** expansion card slot:
- **CompactFlash Compatibility**: With a passive mechanical PCMCIA-to-CF adapter, any standard CompactFlash card functions as fixed drive `A:`.
- **FAT16 Partition Limits**: MS-DOS 5.0 natively addresses FAT16 volumes up to **2.0 Gigabytes** (32 KB cluster size). A 512 MB, 1 GB, or 2 GB CF card provides virtually infinite storage for retro DOS tools, games, compilers, and databases.
- **SRAM Cards**: Supports battery-backed 512 KB to 2 MB PCMCIA SRAM cards using rechargeable internal coin cells.
- **Modems & Ethernet**: Compatible with Megahertz X-Jack PCMCIA 14.4/28.8k modems and NE2000-compatible PCMCIA Ethernet adapters (e.g., D-Link DE-660) via packet drivers (`NE2000.COM`) for telnet and FTP over TCP/IP.

---

## 5. The Hardware Overclocking Mod (32 MHz Crystal Mod)

The stock 200LX runs at 7.91 MHz. Because the static CMOS Hornet SoC and SRAM chips possess generous timing margins, enthusiast hardware hackers routinely execute the **Double-Speed Crystal Mod**:

1. **Procedure**:
   - Unscrew the clamshell lower housing (six Torx T6 screws).
   - Locate the 15.82 MHz cylindrical crystal oscillator (`Y1`) adjacent to the Hornet ASIC.
   - Desolder `Y1` using a temperature-controlled fine-tip iron.
   - Solder a low-profile **31.64 MHz or 32.00 MHz** surface-mount quartz crystal oscillator in its place.
   - (Optional) Install a miniature SPDT slide switch in the battery compartment to toggle between stock 15.82 MHz and modded 32.00 MHz.
2. **Resulting Performance**:
   - Core clock increases from **7.91 MHz to 15.82 MHz or 16.00 MHz** (a 100% throughput gain).
   - Landmark Speed benchmark jumps from 0.77× IBM PC/AT to **1.55× PC/AT**.
   - Lotus 1-2-3 complex financial recalculation times are cut in half.
   - Battery life reduces modestly by ~15% (still achieving 25–30 hours on NiMH cells).
   - High-speed serial terminal throughput becomes rock-solid at 115,200 baud without FIFO buffer overruns.

---

## 6. Amateur Radio, Packet TNC & Terminal Cult Status

Decades after its 1999 end-of-life, the HP 200LX remains an active cult tool among network engineers, telecommunications technicians, and **Ham Radio (Amateur Radio)** emergency operators:

- **True Hardware RS-232 UART**: Unlike modern USB-serial dongles with driver latency and power negotiation issues, the 200LX serial port is a direct hardware UART capable of immediate zero-delay bit banging.
- **Field Terminal for TNCs**: Radio amateurs connect the 200LX via serial cable (HP F1015A) to VHF/UHF Terminal Node Controllers (such as the AEA PK-88, Kantronics KPC-3 Plus, or Byonics TinyTrak).
- **AX.25 Packet & APRS**: Running MS-DOS terminal applications like **Procomm Plus**, **Telix**, or specialized DOS packet programs (**Graphic Packet**, **APRSdos**), emergency search-and-rescue teams transmit GPS beacons and tactical text packets over mountain summits with zero reliance on cellular infrastructure.
- **Survival Runtime**: In an emergency grid failure, two AA batteries keep the terminal operational for weeks of intermittent daily field dispatch.

---

## 7. Interactive 3D Web Station (`/hardware-hp200lx`)

The web station in `web_sota` provides a comprehensive interactive simulation:
1. **PBR 3D Clamshell Model**: Textured charcoal body, dual hinge pivots with dynamic opening angle slider (0° closed to 180° flat), and reflective transflective LCD glass.
2. **Dynamic 640×200 CGA Screen Renderer**: Live HTML5 2D canvas dynamically rendered into a WebGL CanvasTexture, simulating the real 80-column green/olive transflective character matrix.
3. **App Switching Matrix**: Real-time hot-switching between Lotus 1-2-3 Rel 2.4, HP 19BII Financial Calculator, MS-DOS 5.0 Command Prompt, and Filer.
4. **Rotary Contrast & Lamp Simulation**: Adjustable hardware contrast dial modifying character luminance ratios, plus desk lamp ambient illumination sliders.
5. **Piezo Audio Synthesis**: Web Audio square-wave piezo buzzer generating authentic 2400 Hz keyboard click blips and error warbles.
6. **Physical Keyboard Capture**: Typing on the host PC keyboard in Fullscreen mode directly enters commands into the DOS and Calc engines.
