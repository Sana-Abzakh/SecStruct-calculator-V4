
# SecStruct Calculator

Estimate protein secondary structure composition from FTIR spectra. SecStruct Calculator takes the Gaussian-fitted peaks that **PeakFit** produces for the **Amide I band (1600–1700 cm⁻¹)**, assigns each peak to a secondary structure type from its center wavenumber, and reports each type as a percentage of the total fitted area.

**Live version:** <https://sana-abzakh.github.io/SecStruct-calculator-V4/>

**Repository:** <https://github.com/Sana-Abzakh/secstruct-calculator>



| Version | File | Best for |
|---|---|---|
| **Web app** | `secondary_structure_calculator_v4.html` (served as `index.html` on GitHub Pages) | Quick, no-install analysis in the browser. Runs real Python via Pyodide inside a single HTML file |
| **Python engine** | `Secstruct engine.py` | Importing the v4 analysis (Amide I/II/III, H₂O/D₂O, 3₁₀-helix) into your own Python code, with JSON output per sample |

---

## Contents

-  [What it does](#what-it-does)
-   [Calculation framework](#calculation-framework)
-    [Band assignments](#band-assignments)
-    [Web app](#web-app)
-   [Preparing your data in PeakFit](#preparing-your-data-in-peakfit)
-    [Technical details](#technical-details)
-  [Development history](#development-history)
-   [Limitations and things to know](#limitations-and-things-to-know)
-    [AI usage](#ai-usage)
-  [References](#references)
-   [Author](#author)

---

## What it does

1. Reads a PeakFit output file (peak centers and areas).
2. Keeps peaks in the Amide I region.
3. Assigns each peak to a secondary structure group by center wavenumber.
4. Computes each peak's share of the total area, then sums by group.
5. Reports group percentages and the **α-Helix / β-Sheet ratio**.

The underlying principle is that the integrated area under each fitted Gaussian component is proportional to the abundance of the structure it represents.

---

## Calculation framework

```
Total Amide I area = Σ (area of all fitted peaks in the Amide I window)

% Structure = (area of peaks assigned to that structure ÷ total Amide I area) × 100

α/β ratio = % α-Helix ÷ % β-Sheet
```

**Reading the α/β ratio.** It is a conformational indicator. Values below 1 indicate β-sheet dominance, which may reflect aggregation or partial unfolding; values above about 1.5 generally indicate a helix-rich, well-folded protein. Use it comparatively between samples fitted the same way rather than as an absolute threshold.

---

## Band assignments

| Structure | Range (cm⁻¹) | Group |
|---|---|---|
| Aggregated / intermolecular β-sheet | 1600 – 1627.9 | β-Sheet |
| β-Sheet (main) | 1628 – 1642.9 | β-Sheet |
| Random coil / disordered | 1643 – 1649.4 | Random Coil |
| α-Helix | 1649.5 – 1659.9 | α-Helix |
| β-Turns & loops | 1660 – 1699.9 | β-Turns |
| β-Sheet (high-frequency component) | 1680 – 1695 | β-Sheet |

Notes on the rules:

- **High-frequency β-sheet (1680–1695)** sits inside the turns region and is checked first, so peaks there count as β-Sheet. Turns therefore cover 1660–1679.9 and 1695.1–1699.9. The order of the rules matters because the first match wins.
- **Boundary at 1650:** the α-Helix threshold is set at 1649.5, so peaks sitting right on the 1650 boundary are assigned to α-Helix.
- Peaks that fall outside every range are labeled `Unassigned`.
- Assignment ranges are based on Sadat & Joye (2020), Yan et al. (2017) and Sukumaran (2017). Band positions shift with solvent (H₂O vs D₂O), sample state and fitting model, so adjust the ranges to match your own protocol.

---

## Web app

Open the hosted version, or open `secondary_structure_calculator_v4.html` directly in any modern browser. Nothing needs to be installed.

**Layout.** The page is split in two. The left panel holds the downloads (example file and documentation PDF), the file drop zone, and the peak-assignment reference table. The right panel shows the results.

**Features**

- Drag-and-drop or click-to-browse upload of `.csv`, `.txt` and `.tsv` files, several at once.
- For each file: four metric tiles (β-Sheet, α-Helix, β-Turns, Random Coil), a donut chart, a **Group summary** tab and a **Peak detail** tab, and the α/β ratio.
- A **multi-sample comparison** table appears automatically when two or more files are loaded.
- Results export as formatted `.txt` files, one per sample plus a combined comparison file.
- A downloadable **example PeakFit file** and the **documentation PDF** are built into the page.

**Privacy.** Files are read in the browser and processed locally by the Python runtime. Uploaded data is never sent to a server.

**Connection.** The first visit needs an internet connection to fetch the Pyodide runtime (about 10 MB) from the jsDelivr CDN. Browsers normally cache it afterwards, so later visits start quickly and usually work without a connection. Web fonts fall back to system fonts if they cannot be loaded.
---

## Preparing your data in PeakFit

- Fit the **baseline-corrected, second-derivative-guided** Amide I region with Gaussian components.
- Export the peak table so that it includes the **center (a1)** and **area (a0)** of each component.
- Use the **Gaussian area** (not height), since percentages are area-based.
- Use the same fitting protocol (number of components, constraints, solvent) across samples you intend to compare.

PeakFit exports often include components outside the Amide I band (for example side-chain or baseline components near 1490–1590 cm⁻¹ or above 1700 cm⁻¹). These are discarded automatically by the window filter described below.

---

## Technical details

### Architecture of the web app

The whole application is one self-contained `.html` file (about 140 KB, including the embedded documentation PDF) made of three layers:

| Layer | Role |
|---|---|
| **Python** | All scientific logic: parsing, validation, band assignment, percentage calculation. Stored as inert text in `<script id="py-src" type="text/x-python">`, a made-up script type the browser ignores |
| **JavaScript** | Loads the Python engine, reads uploaded files, calls Python, and renders the results (cards, tables, donut chart, downloads) |
| **CSS** | Layout, colour palette and typography |

**Why Pyodide.** Pyodide is CPython compiled to WebAssembly, so the real Python interpreter runs inside the browser tab. The alternatives were a server backend (Flask/FastAPI), which needs hosting and a permanent connection, or Python-to-JavaScript transpilers such as Brython, which support only a subset of Python and cannot run the script's use of `dataclasses`, `re`, `pathlib` and `typing`. With Pyodide the research script runs essentially unchanged and no backend is needed. The app loads Pyodide v0.25.1 (Python 3.11).

### Data flow

```
PeakFit file
   │  file.text()                       (JavaScript)
   ▼
pyodide.globals.set(...)  ──►  analyze_for_web(content, filename)      (Python)
                                 parse → filter → assign → sum
   ▲                                          │
   │  JSON.parse(...)                         │  json.dumps(result)
   └──────────────────────────────────────────┘
   │
   ▼
renderResult(): metric tiles · donut chart · group summary · peak detail · .txt export
```

Python hands its result to JavaScript as a JSON string, the one data format both languages handle natively.

### Python engine

- **Constants.** `PARSE_WINDOW_MIN/MAX = 1590 / 1720`, `AMIDE_I_MIN/MAX = 1600 / 1700`, `AREA_CEILING = 1e7`. Named constants replace repeated literals.
- **`Peak` dataclass.** Validates every peak on construction: area must be positive and the center must lie between 1000 and 4000 cm⁻¹. Invalid peaks are skipped rather than crashing the run.
- **`ASSIGNMENT_ORDER`.** An ordered list of `(label, low, high, group)` tuples. `assign_structure()` returns on the first match, which is why the high-frequency β-sheet range precedes the broader β-turns range.
- **Parsers, tried in order:** comma-, tab- and semicolon-delimited files with a header row; whitespace-delimited with a header row; then a headerless numeric fallback that tries both column orders and uses `AREA_CEILING` to avoid mistaking large numbers for areas.
- **Two-stage windowing (web app).** Peaks are first read within the wider 1590–1720 cm⁻¹ parse window, then filtered to the strict 1600–1700 cm⁻¹ Amide I region before the total area is computed.
- **`calculate()`** sums the areas, assigns each peak, computes per-peak and per-group percentages, and **`_alpha_beta_ratio()`** returns α-Helix ÷ β-Sheet, or `None` when there is no β-sheet.
- **`analyze_for_web()`** is the single entry point called from JavaScript. It returns either a result object or an `error` message.

### Front end

- **Donut chart** drawn with the browser's Canvas 2D API. No charting library is used.
- **Results** are built dynamically (`renderResult()`, `updateComparison()`) with no page reloads; each result card keeps its data on the DOM element for later export.
- **Downloads** (`.txt` results, example CSV, documentation PDF) are generated in the browser as `Blob` objects. The documentation PDF is embedded in the page as base64, so the file needs no companion assets.
- **Design.** Two-column CSS grid (380 px left panel, flexible right panel), CSS custom properties for the colour palette (forest `#0C3B2E`, sage `#6D9773`, tan `#BB8A52`, gold `#FFBA00`), and DM Mono / Syne fonts.

---

## Development history

The calculator was built up in stages.

**1. Research scripts.** The work began as two Python scripts for PeakFit output: a command-line version that parses delimited files and writes CSV results, and a Google Colab version with file upload, a `Peak` dataclass and `.txt` output.

**2. Code review and consolidation.** The scripts were reviewed and the issues found were fixed:

- removed an unused duplicate range table (`STRUCTURE_RANGES`) so there is a single source of truth for assignments
- aligned the documented boundaries with the code (the 1649.4 / 1649.5 split)
- documented why the high-frequency β-sheet range must be evaluated before β-turns
- stopped the headerless fallback parser from adding duplicate peaks, and capped plausible areas with `AREA_CEILING`
- removed a redundant header check and an unused delimiter list
- validated peak areas and centers through the `Peak` dataclass so negative or unrealistic values are rejected
- warned about peaks that fall outside every assignment range
- replaced magic numbers with named constants, factored the α/β ratio into one helper, and added a multi-sample comparison output
- renamed variables that shadowed built-ins or imports and made the type hints consistent

The two scripts were merged into one unified implementation.

**3. Web application.** The unified Python logic was embedded in a single HTML page and run in the browser through Pyodide, so no installation, server or backend is required.

**4. Interface iterations.** The interface grew in steps: drag-and-drop upload, per-sample result cards and a multi-sample comparison table; a donut chart replacing the first bar-chart design; the group summary placed first in the results tabs; a peak-assignment reference table; a downloadable example file and embedded documentation PDF; `.txt` result exports in place of CSV; a two-column layout; a colour palette and logo icon; and author attribution with contact details.

**5. Publication.** The page was published for free on GitHub Pages (see below).


---

## Limitations and things to know

- **Assignment is by peak center only.** Overlapping bands, ambiguous components (for example around 1645–1655 cm⁻¹ in H₂O) and side-chain contributions are not resolved. The result is only as good as the underlying peak fit.
- **Unassigned peaks affect the percentages.** Any parsed peak that falls outside the assignment ranges (for example between 1699.9 and 1700, or in the gaps of the ranges) is labeled `Unassigned`, still counts toward the total area, and lowers the other percentages. Check for them before reporting numbers.
- **Analysis window.** The web app restricts the analysis to 1600–1700 cm⁻¹ before totalling areas. The command-line script, as described above, parses 1590–1720 cm⁻¹ and counts anything outside the assignment ranges as `Unassigned`. For files with components in 1590–1599.9 or 1700.1–1720 cm⁻¹ the two versions can therefore report slightly different percentages. Keep the same tool and window across samples you intend to compare.
- **Percentages are relative area fractions**, not absolute residue counts. Extinction coefficients differ between structure types, and FTIR-derived values are best compared across samples fitted the same way, or against reference methods (CD, X-ray/DSSP) with care.
- **Editing the ranges.** The parsing window and assignment ranges are defined in the code (`ASSIGNMENT_ORDER` and the window constants in both the script and the web app's embedded Python) and can be edited for your own protocol.

---

## AI usage

This project was developed with the assistance of an AI model, **Claude (Anthropic)**, used through the claude.ai chat interface. It is disclosed here for transparency.

**Where AI assisted**

- Reviewing the original Python scripts, identifying bugs and inconsistencies, and proposing the fixes listed in the development history.
- Assist writing the HTML, CSS and JavaScript of the web interface, iterated from the author's design instructions (layout, colour palette, icon, charts, downloads).

**What remains the author's work and responsibility**

- The scientific approach: Amide I peak-area analysis of PeakFit output, and the choice of band assignment ranges, which come from the cited literature rather than from the AI.
- All decisions about features, design and what to publish, and review of the AI-generated code and text.
- The use of the tool in any analysis or publication.

**What the tool itself does**

The calculator contains no AI. Its output comes from fixed, deterministic rules (parsing, range lookup and area arithmetic) that can be read in the source, and uploaded files are processed locally in the browser and are not sent anywhere.

---

## References

- Dong, A., Huang, P. & Caughey, W. S. (1990). Protein secondary structures in water from second-derivative amide I infrared spectra. Biochemistry, 29(13), 3303–3308.
- Susi, H. & Byler, D. M. (1986). Resolution-enhanced Fourier transform infrared spectroscopy of enzymes. Methods in Enzymology, 130, 290–311.
- Yan, Z., Li, Q. & Zhang, P. (2017). Soy protein isolate and glycerol hydrogen bonding using 2D-COS ATR FT-IR spectroscopy. Applied Spectroscopy, 71(11), 2437–2445.

---

## Author

Sana Aiman Abzakh. Developed from FTIR microspectroscopy intrenship at the SESAME IR beamline.

Contact: <sanaabzakh262@gmail.com>
