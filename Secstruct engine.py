# Extracted verbatim from the <script id="py-src" type="text/x-python"> block
# of secondary_structure_calculator_v4.html (the Pyodide engine).
import re, json
from pathlib import Path

# ── H₂O · Globular (default) ─────────────────────────────────────
ASSIGNMENT_H2O_GLOBULAR = [
    ("Aggregated β-Sheet",    1600.0, 1627.9, "β-Sheet",    "aggregated"),
    ("β-Sheet (Main)",        1628.0, 1642.9, "β-Sheet",    "main"),
    ("Random Coil",           1643.0, 1649.4, "Random Coil", ""),
    ("α-Helix",               1649.5, 1659.9, "α-Helix",    ""),
    ("β-Turns & Loops",       1660.0, 1689.9, "β-Turns",    ""),
    ("Anti-parallel β-Sheet", 1690.0, 1700.0, "β-Sheet",    "antiparallel"),
]

# ── H₂O · 3₁₀-Helix rich ─────────────────────────────────────────
# 1660–1666 carved out for 3₁₀-Helix; remainder stays β-Turns
ASSIGNMENT_H2O_310 = [
    ("Aggregated β-Sheet",    1600.0, 1627.9, "β-Sheet",    "aggregated"),
    ("β-Sheet (Main)",        1628.0, 1642.9, "β-Sheet",    "main"),
    ("Random Coil",           1643.0, 1649.4, "Random Coil", ""),
    ("α-Helix",               1649.5, 1659.9, "α-Helix",    ""),
    ("3₁₀-Helix",             1660.0, 1666.0, "3₁₀-Helix",  ""),   # ← new sub-range
    ("β-Turns & Loops",       1666.1, 1689.9, "β-Turns",    ""),
    ("Anti-parallel β-Sheet", 1690.0, 1700.0, "β-Sheet",    "antiparallel"),
]

# ── D₂O · Globular (default) ─────────────────────────────────────
ASSIGNMENT_D2O_GLOBULAR = [
    ("Aggregated β-Sheet",    1600.0, 1625.9, "β-Sheet",    "aggregated"),
    ("β-Sheet (Main)",        1630.0, 1642.9, "β-Sheet",    "main"),
    ("Random Coil",           1643.0, 1649.4, "Random Coil", ""),
    ("α-Helix",               1649.5, 1659.9, "α-Helix",    ""),
    ("β-Turns & Loops",       1660.0, 1679.9, "β-Turns",    ""),
    ("Anti-parallel β-Sheet", 1680.0, 1695.0, "β-Sheet",    "antiparallel"),
]

# ── D₂O · 3₁₀-Helix rich ─────────────────────────────────────────
# Isotopic shift: 3₁₀-Helix moves to 1639–1643 cm⁻¹ in D₂O
# This overlaps β-Sheet (Main) / Random Coil region, so we carve it out
ASSIGNMENT_D2O_310 = [
    ("Aggregated β-Sheet",    1600.0, 1625.9, "β-Sheet",    "aggregated"),
    ("β-Sheet (Main)",        1626.0, 1638.9, "β-Sheet",    "main"),
    ("3₁₀-Helix",             1639.0, 1643.0, "3₁₀-Helix",  ""),   # ← D₂O isotopic shift
    ("Random Coil",           1643.1, 1649.4, "Random Coil", ""),
    ("α-Helix",               1649.5, 1659.9, "α-Helix",    ""),
    ("β-Turns & Loops",       1660.0, 1679.9, "β-Turns",    ""),
    ("Anti-parallel β-Sheet", 1680.0, 1695.0, "β-Sheet",    "antiparallel"),
]

ASSIGNMENT_AMIDE2 = [
    ("α-Helix (II)",   1540.0, 1550.0, "α-Helix"),
    ("β-Sheet (II)",   1525.0, 1535.0, "β-Sheet"),
    ("β-Turn (II)",    1510.0, 1524.9, "β-Turns"),
    ("β-Turn (II)",    1570.0, 1580.0, "β-Turns"),
    ("Amide II",       1510.0, 1580.0, "Unassigned II"),
]
ASSIGNMENT_AMIDE3 = [
    ("α-Helix (III)",        1290.0, 1335.0, "α-Helix"),
    ("β-Sheet (III)",        1220.0, 1255.0, "β-Sheet"),
    ("Unordered+Turn (III)", 1244.0, 1292.0, "Random Coil"),
]

GROUP_ORDER_A1_GLOBULAR = ["β-Sheet","α-Helix","Random Coil","β-Turns","Unassigned"]
GROUP_ORDER_A1_310      = ["β-Sheet","α-Helix","3₁₀-Helix","Random Coil","β-Turns","Unassigned"]
GROUP_ORDER_A2 = ["α-Helix","β-Sheet","β-Turns","Unassigned II"]
GROUP_ORDER_A3 = ["α-Helix","β-Sheet","Random Coil"]

def get_a1_table(solvent, protein_type):
    if solvent == "H2O":
        return (ASSIGNMENT_H2O_310       if protein_type == "310helix"
                else ASSIGNMENT_H2O_GLOBULAR)
    else:
        return (ASSIGNMENT_D2O_310       if protein_type == "310helix"
                else ASSIGNMENT_D2O_GLOBULAR)

def get_group_order(protein_type):
    return GROUP_ORDER_A1_310 if protein_type == "310helix" else GROUP_ORDER_A1_GLOBULAR

def assign(wn, table):
    for entry in table:
        lo, hi, group = entry[1], entry[2], entry[3]
        if lo <= wn <= hi:
            return entry[0], group, (entry[4] if len(entry) > 4 else "")
    return "Unassigned", "Unassigned", ""

def _try_float(v):
    try: return float(str(v).replace(",", "."))
    except: return None

def _find_hdrs(headers):
    ai = ci = None
    for i, h in enumerate(headers):
        h = h.strip().lower()
        if re.search(r"\ba0\b|area", h): ai = i
        if re.search(r"\ba1\b|center|wavenumber|position", h): ci = i
    return ai, ci

def _parse_delim(lines, delim):
    peaks, hrow, ai, ci = [], None, None, None
    for no, line in enumerate(lines):
        if not line.strip() or line.strip().startswith("#"): continue
        parts = [p.strip() for p in line.split(delim)]
        if len(parts) < 2: continue
        if hrow is None:
            a, c = _find_hdrs([p.lower() for p in parts])
            if a is not None and c is not None: hrow, ai, ci = no, a, c
            continue
        if len(parts) <= max(ai, ci): continue
        ar = _try_float(parts[ai]); ce = _try_float(parts[ci])
        if ar and ce and 1200 <= ce <= 1800 and ar > 0:
            peaks.append({"area": ar, "center": ce})
    return peaks

def _parse_ws(lines):
    peaks, hrow, ai, ci = [], None, None, None
    for no, line in enumerate(lines):
        if not line.strip() or line.strip().startswith("#"): continue
        parts = line.split()
        if len(parts) < 2: continue
        if hrow is None:
            a, c = _find_hdrs([p.lower() for p in parts])
            if a is not None and c is not None: hrow, ai, ci = no, a, c
            continue
        if len(parts) <= max(ai, ci): continue
        ar = _try_float(parts[ai]); ce = _try_float(parts[ci])
        if ar and ce and 1200 <= ce <= 1800 and ar > 0:
            peaks.append({"area": ar, "center": ce})
    return peaks

def _parse_fallback(lines):
    peaks = []
    for line in lines:
        fs = [f for p in line.split() if (f := _try_float(p)) is not None]
        if len(fs) < 2: continue
        for f1, f2 in [(fs[0], fs[1]), (fs[1], fs[0])]:
            if 1200 <= f1 <= 1800 and 0 < f2 < 1e7:
                peaks.append({"area": f2, "center": f1}); break
    return peaks

def parse_all(content):
    lines = [l.rstrip() for l in content.splitlines()]
    for d in (",", "\t", ";"):
        try:
            p = _parse_delim(lines, d)
            if p: return p
        except: pass
    try:
        p = _parse_ws(lines)
        if p: return p
    except: pass
    return _parse_fallback(lines)

def region(peaks, lo, hi):
    return [p for p in peaks if lo <= p["center"] <= hi]

def calc(peaks, tbl, group_order):
    if not peaks: return [], {}, 0.0, {}
    tot = sum(p["area"] for p in peaks)
    if tot == 0: return [], {}, 0.0, {}
    det, gt, bs = [], {}, {}
    for i, p in enumerate(peaks):
        lbl, grp, sub = assign(p["center"], tbl)
        pct = p["area"] / tot * 100
        det.append({"peak": i+1, "area": p["area"], "center": p["center"],
                    "detail_label": lbl, "group": grp, "sub": sub, "pct": pct})
        gt[grp] = gt.get(grp, 0) + p["area"]
        if grp == "β-Sheet" and sub:
            bs[sub] = bs.get(sub, 0) + p["area"]
    gs = {g: v/tot*100 for g, v in gt.items()}
    bsp = {k: v/tot*100 for k, v in bs.items()}
    return det, gs, tot, bsp

def analyze_for_web(content, filename, solvent, protein_type):
    sn = Path(filename).stem
    all_peaks = parse_all(content)
    if not all_peaks: return json.dumps({"error": "No peaks parsed."})
    a1_tbl = get_a1_table(solvent, protein_type)
    go     = get_group_order(protein_type)
    a1p = region(all_peaks, 1599, 1700)
    a2p = region(all_peaks, 1510, 1580)
    a3p = region(all_peaks, 1210, 1360)
    a1d, a1gs, a1tot, a1bs = calc(a1p, a1_tbl, go)       if a1p else ([], {}, 0, {})
    a2d, a2gs, a2tot, _    = calc(a2p, ASSIGNMENT_AMIDE2, GROUP_ORDER_A2) if a2p else ([], {}, 0, {})
    a3d, a3gs, a3tot, _    = calc(a3p, ASSIGNMENT_AMIDE3, GROUP_ORDER_A3) if a3p else ([], {}, 0, {})
    alpha = a1gs.get("α-Helix", 0); beta = a1gs.get("β-Sheet", 0)
    ratio = alpha / beta if beta > 0 else None
    return json.dumps({
        "sample_name": sn, "filename": filename,
        "solvent": solvent, "protein_type": protein_type,
        "amide1": {"details": a1d, "group_summary": a1gs, "total_area": a1tot,
                   "beta_sub": a1bs, "group_order": go},
        "amide2": {"details": a2d, "group_summary": a2gs, "total_area": a2tot,
                   "group_order": GROUP_ORDER_A2},
        "amide3": {"details": a3d, "group_summary": a3gs, "total_area": a3tot,
                   "group_order": GROUP_ORDER_A3},
        "ratio": ratio,
    })