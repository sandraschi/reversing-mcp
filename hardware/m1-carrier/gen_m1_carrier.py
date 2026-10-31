"""Generate M1-CARRIER rev A outline + placement draft via KiCad 10 pcbnew.

Provisional geometry: 250x180 outline, M3 holes inset 6 mm, placement zones
for CM5 / GPIO / LCD / DAC / MIDI. VERIFY KLM-1266 OUTLINE + STANDOFFS WITH
CALIPERS BEFORE FAB. Run with KiCad's bundled python (10.0.x).
"""

import pcbnew

MM = pcbnew.FromMM


def silk_rect(board, x0, y0, x1, y1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
    s.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    s.SetLayer(pcbnew.F_SilkS)
    s.SetWidth(MM(0.1))
    s.SetFilled(False)
    board.Add(s)


def silk_text(board, text, x, y, size=2.0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(size / 5.0))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)


def mounting_hole(board, ref, x, y):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetValue("M3")
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    fp.SetLayer(pcbnew.F_Cu)
    pad = pcbnew.PAD(fp)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pad.SetSize(pcbnew.VECTOR2I(MM(4.2), MM(4.2)))
    pad.SetDrillSize(pcbnew.VECTOR2I(MM(3.2), MM(3.2)))
    pad.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    layers = pcbnew.LSET()
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.F_Mask, pcbnew.B_Mask):
        layers.addLayer(layer)
    pad.SetLayerSet(layers)
    fp.Add(pad)
    board.Add(fp)


OUT = "D:/Dev/repos/reversing-mcp/hardware/m1-carrier/m1-carrier-revA.kicad_pcb"

board = pcbnew.BOARD()
tb = board.GetTitleBlock()
tb.SetTitle("M1-CARRIER rev A (PROVISIONAL outline + placement)")
tb.SetCompany("sandraschi fleet")
tb.SetRevision("A")
tb.SetDate("2026-10-31")
tb.SetComment(1, "KLM-1266 replacement. VERIFY ALL DIMS BEFORE FAB.")

edge = pcbnew.PCB_SHAPE(board)
edge.SetShape(pcbnew.SHAPE_T_RECT)
edge.SetStart(pcbnew.VECTOR2I(MM(0), MM(0)))
edge.SetEnd(pcbnew.VECTOR2I(MM(250), MM(180)))
edge.SetLayer(pcbnew.Edge_Cuts)
edge.SetWidth(MM(0.15))
edge.SetFilled(False)
board.Add(edge)

for ref, x, y in (("H1", 6, 6), ("H2", 244, 6), ("H3", 6, 174), ("H4", 244, 174)):
    mounting_hole(board, ref, x, y)

silk_rect(board, 20, 20, 75, 60)
silk_text(board, "CM5 55x40 + J2/J3 BOTTOM", 22, 30)
silk_rect(board, 85, 20, 160, 60)
silk_text(board, "GPIO + MCP23017 x2 (Y0..Y7)", 87, 30)
silk_rect(board, 20, 75, 120, 90)
silk_text(board, "HD44780 16x1 HDR", 22, 82)
silk_rect(board, 140, 75, 200, 105)
silk_text(board, "I2S DAC", 142, 88)
silk_rect(board, 140, 115, 200, 145)
silk_text(board, "MIDI UART+OPTO + USB", 142, 128)
silk_text(board, "PROVISIONAL - VERIFY KLM-1266 WITH CALIPERS BEFORE FAB", 20, 160, 2.5)
silk_text(board, "PSU: reuse TX, new 5V/3A + LCD bias", 20, 168)

ok = board.Save(OUT)
if not ok:
    raise SystemExit("board.Save failed: " + OUT)
