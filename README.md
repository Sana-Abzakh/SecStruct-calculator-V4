# SecStruct Calculator

Estimate protein secondary structure composition from FTIR spectra. SecStruct Calculator takes the Gaussian-fitted peaks that **PeakFit** produces for the **Amide I band (1600–1700 cm⁻¹)**, assigns each peak to a secondary structure type from its center wavenumber, and reports each type as a percentage of the total fitted area.

It comes in two forms that share the same assignment logic:

| Version | File | Best for |
|---|---|---|
| **Web app** | `secondary_structure_calculator_v4.html` | Quick, no-install analysis in the browser (runs Python via Pyodide, fully offline-capable single file) |
| **Command-line script** | `secondary_structure_calculator.py` | Batch processing many samples, scripting, reproducible pipelines |

Repository: <https://github.com/Sana-Abzakh/secstruct-calculator>

---

## What it does

1. Reads a PeakFit output file (peak centers and areas).
2. Keeps peaks in the Amide I region (centers between 1590 and 1720 cm⁻¹).
3. Assigns each peak to a secondary structure group by center wavenumber.
4. Computes each peak's share of the total area, then sums by group.
5. Reports group percentages and the **α-Helix / β-Sheet ratio**.

Percentage for a peak = `peak area / total area of all parsed peaks × 100`.

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

- **High-frequency β-sheet (1680–1695)** sits inside the turns region and is checked first, so peaks there count as β-Sheet. Turns therefore cover 1660–1679.9 and 1695.1–1699.9.
- **Boundary at 1650:** the α-Helix threshold is set at 1649.5, so peaks sitting right on the 1650 boundary are assigned to α-Helix.
- Peaks that fall outside every range (for example 1590–1599.9 or above 1699.9) are labeled `Unassigned`.
- Assignment ranges are based on Sadat & Joye (2020), Yan et al. (2017) and Sukumaran (2017). Band positions shift with solvent (H₂O vs D₂O), sample state and fitting model, so adjust the ranges to match your own protocol.

---

## Web app

Open `secondary_structure_calculator_v4.html` in any modern browser (or use the hosted version from the repository). Load your PeakFit output, and the app displays the per-peak assignments, group percentages and α/β ratio. Results can be exported as a formatted `.txt` file.

It is a single self-contained HTML file built with Python (Pyodide / WebAssembly), HTML and CSS, so nothing needs to be installed.

---

## Command-line script

### Requirements

- Python 3.9+ (uses built-in type hints such as `list[dict]`)
- No third-party packages, standard library only

### Usage

```bash
python secondary_structure_calculator.py <peakfit_output_file> [<file2> ...]
```

Example, several samples at once:

```bash
python secondary_structure_calculator.py Pa1_amide1.txt 135control_amide1.txt
```

Running with no arguments prints the built-in help.

### Accepted input formats

The parser tries these in order, so most PeakFit exports work without editing:

1. **Delimited files with a header row** (comma, tab or semicolon). Headers are matched case-insensitively:
   - Area column: any header containing `area`
   - Center column: any header containing `a1`, `center`, `wavenumber` or `position`
2. **Whitespace-delimited files with the same headers.**
3. **Headerless fallback:** any row containing at least two numbers, where one is a wavenumber in 1590–1720 and the other is a positive area (either column order).

Decimal commas (`1652,3`) are accepted. Lines starting with `#` and blank lines are ignored.

Example of a minimal two-column input:

```
1618.4   0.0231
1637.9   0.0452
1654.2   0.0388
1675.1   0.0127
```

### Output

**Console:** a per-sample table of peaks (center, area, structure detail, group, % of total), a group summary, and the α/β ratio.

**CSV:** one file per input, written next to the input file as `<input_name>_secondary_structure.csv`, containing:

- sample name and total Amide I area
- per-peak details (center, area, structure detail, group, % contribution)
- group summary
- α/β ratio (when β-sheet > 0)

Example console output (illustrative):

```
=================================================================
  Sample: Pa1_amide1
  Total Amide I Area: 0.119800
=================================================================
  Peak  Center (cm⁻¹)  Area  Structure Detail  Group  %
  ...
  Secondary Structure Group   % Contribution
  α-Helix                           32.39%
  β-Sheet                           51.85%
  β-Turns                           10.60%
  Random Coil                        5.16%

  α-Helix / β-Sheet ratio: 0.625
```

---

## Preparing your data in PeakFit

- Fit the **baseline-corrected, second-derivative-guided** Amide I region with Gaussian components.
- Export the peak table so that it includes the **center (a1)** and **area** of each component.
- Use the **Gaussian area** (not height), since percentages are area-based.
- Use the same fitting protocol (number of components, constraints, solvent) across samples you intend to compare.

---

## Limitations and things to know

- **Assignment is by peak center only.** Overlapping bands, ambiguous components (for example around 1645–1655 cm⁻¹ in H₂O) and side-chain contributions are not resolved. The result is only as good as the underlying peak fit.
- **The total area is the sum of all parsed peaks in 1590–1720 cm⁻¹, including any `Unassigned` ones.** If you have peaks outside the assignment ranges, they lower the other percentages and appear as an `Unassigned` group, so check for them before reporting numbers.
- **Percentages are relative area fractions**, not absolute residue counts. Extinction coefficients differ between structure types, and FTIR-derived values are best compared across samples fitted the same way, or against reference methods (CD, X-ray/DSSP) with care.
- The `1590–1720` parsing window and the assignment ranges are defined in the script (`ASSIGNMENT_ORDER`, and the `1590 <= center <= 1720` checks) and can be edited for your own protocol.

---


## References

- Dong, A., Huang, P. & Caughey, W. S. (1990). Protein secondary structures in water from second-derivative amide I infrared spectra. Biochemistry, 29(13), 3303–3308.
- Susi, H. & Byler, D. M. (1986). Resolution-enhanced Fourier transform infrared spectroscopy of enzymes. Methods in Enzymology, 130, 290–311.
- Yan, Z., Li, Q. & Zhang, P. (2017). Soy protein isolate and glycerol hydrogen bonding using 2D-COS ATR FT-IR spectroscopy. Applied Spectroscopy, 71(11), 2437–2445.


---

## Author

Sana Aiman Abzakh. Developed from FTIR microspectroscopy work at the SESAME IR beamline.
