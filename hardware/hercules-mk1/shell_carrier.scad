// Hercules DJ Console (MK1 - 2003) Replacement Faceplate Deck-Saver & Carrier Frame
// Parametric OpenSCAD Model to replace the lost polycarbonate clamshell and strap loops.
//
// Console Physical Dimensions:
// Width: 235mm, Depth: 200mm, Base Height: 45mm, Knobs/Jog Protrusion: 20mm (Total 65mm)

$fn = 60;

console_w = 236.0;   // 1mm clearance
console_d = 201.0;   // 1mm clearance
cover_h   = 28.0;    // Clear jog wheels and EQ pots
wall_t    = 3.2;     // Robust printable shell thickness
corner_r  = 12.0;    // Corner radius of console aluminum bevel
strap_w   = 26.0;    // 25mm nylon webbing slot
strap_t   = 4.0;

module rounded_box(w, d, h, r) {
    hull() {
        translate([r, r, 0]) cylinder(r=r, h=h);
        translate([w - r, r, 0]) cylinder(r=r, h=h);
        translate([r, d - r, 0]) cylinder(r=r, h=h);
        translate([w - r, d - r, 0]) cylinder(r=r, h=h);
    }
}

module hercules_mk1_deck_saver() {
    difference() {
        // Outer protective perimeter
        rounded_box(console_w + 2*wall_t, console_d + 2*wall_t, cover_h + wall_t, corner_r + wall_t);

        // Inner cavity protecting jog wheels & knobs
        translate([wall_t, wall_t, -0.1])
            rounded_box(console_w, console_d, cover_h, corner_r);

        // Side carry strap loop slots (Left and Right)
        translate([-1, (console_d + 2*wall_t - strap_w)/2, cover_h/2])
            cube([wall_t + 2, strap_w, strap_t]);

        translate([console_w + wall_t - 1, (console_d + 2*wall_t - strap_w)/2, cover_h/2])
            cube([wall_t + 2, strap_w, strap_t]);

        // Front headphone jack clearance notch
        translate([(console_w + 2*wall_t - 60)/2, -1, 0])
            cube([60, wall_t + 2, 12]);
    }
}

hercules_mk1_deck_saver();
