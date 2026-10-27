# CE 766 Watershed Management: Groundwater Management Under Uncertain Recharge

## Arkavathy Sub-basin, Bengaluru Rural & Ramanagara, Karnataka

**Student:** <YOUR NAME> | **Roll:** <YOUR ROLL NO>
**Course:** CE 766 Watershed Management (Autumn 2026)
**Instructor:** Riddhi Singh
**Submission Date:** <DATE>

> **STATUS (read first):** Code is written and tested on **synthetic** rainfall only.
> Acquisition of IMD rainfall and WRIS/CGWB well records is **in progress**.
> All numbers and figures below are pipeline tests with **placeholder parameters**, not observed results.

---

## Overview

Exploratory-modelling study of which groundwater management strategies (pumping caps, managed aquifer
recharge, crop-water demand shift) keep the Arkavathy aquifer sustainable across a wide range of plausible
recharge conditions over 2000-2022, and under what conditions each strategy fails.

A lumped annual aquifer water balance is simulated for 2,000 sampled combinations of uncertainties
(recharge fraction, specific yield, baseline pumping, bootstrapped rainfall sequence) under six strategies.
Strategies are compared with satisficing robustness and regret, and CART scenario discovery identifies the
uncertainty combinations that cause failure.

---

## Files

### Data
- `data/processed/arkavathy_annual_rainfall_TEMPLATE.csv` - empty template (`year, rain_mm`) for basin-average annual IMD rainfall, 2000-2022. **To be filled from IMD data (in progress).**
- `data/DEMO_rain.csv` - **synthetic** annual rainfall (gamma distribution, mean 830 mm, SD 210 mm, Srinivasan et al., 2015) used only to test the pipeline.

### Code
- `code/arkavathy_exploratory_model.py` - lumped aquifer model, strategy simulation, robustness/regret and CART scenario discovery (Python 3.8+)
- `requirements.txt` - dependencies (scikit-learn optional, for CART only)

### Figures
- `figures/DEMO_robustness.png` - Figure 1: pipeline test on **synthetic** rainfall (not observations)

### Results (synthetic test run)
- `results/DEMO_strategy_summary.csv`, `results/DEMO_strategy_outcomes.csv`, `results/DEMO_sampled_states.csv`

---

## Quick Start

```
pip install -r requirements.txt

# 1. Pipeline test on synthetic rainfall
python code/arkavathy_exploratory_model.py --demo

# 2. Real run, once data/processed/arkavathy_annual_rainfall.csv exists
python code/arkavathy_exploratory_model.py data/processed/arkavathy_annual_rainfall.csv
```

Outputs are written to `results/` and `figures/`.

---

## Model

```
dS(t)  = f * P(t) + MAR - min[Pump * (1 - shift), Cap] - Qb(t)
Qb(t)  = 0.3 * f * P(t) * max(0, 1 - d(t)/10)
d(t+1) = max(0, d(t) - dS(t) / (1000 * Sy))
```

| Symbol | Meaning |
|---|---|
| dS | annual storage change (mm) |
| f, P | recharge fraction, annual rainfall (mm) |
| MAR | managed aquifer recharge (mm/yr) |
| Pump, shift, Cap | baseline pumping (mm/yr), crop-demand reduction, pumping ceiling (mm/yr) |
| Qb | baseflow (mm), reduced as the water table deepens |
| d, Sy | depth to water table (m), specific yield |

**XLRM.** Levers: pumping cap, MAR, crop-demand shift. Uncertainties: f, Sy, pumping, rainfall.
Metrics: maximum water-table depth, share of years with storage loss, cumulative storage change.
Success = max depth <= 60 m and cumulative storage change >= 0.

**Strategies:** baseline; pumping cap 100 mm/yr; pumping cap 70 mm/yr; MAR 20 mm/yr; crop shift 20%; combined (cap 100 + MAR 20 + shift 10%).

---

## Pipeline test results (SYNTHETIC rainfall, PLACEHOLDER parameters)

| Strategy | Satisficing | Median cum. dS (mm) | P90 regret (mm) |
|---|---|---|---|
| baseline | 0.116 | -1419.6 | 2616.5 |
| pumping cap 100 mm/yr | 0.226 | -544.6 | 690.0 |
| pumping cap 70 mm/yr | 0.500 | 0.7 | 413.5 |
| MAR 20 mm/yr | 0.220 | -959.6 | 2156.5 |
| crop shift 20% | 0.216 | -807.4 | 1757.3 |
| combined | 0.486 | -34.4 | 230.0 |

These show only that the pipeline runs end to end. They carry no hydrological meaning until the
placeholder ranges and observed rainfall are in place.

![Figure 1](figures/DEMO_robustness.png)

*Figure 1. Pipeline test on synthetic rainfall with placeholder parameters (not observations): (left) share of sampled uncertainty states in which each strategy meets both sustainability criteria; (right) spread of cumulative storage change across states.*

---

## Data Sources

- **Rainfall (in progress):** IMD gridded rainfall - https://imdweb.lwcc.in/
- **Groundwater levels (in progress):** WRIS - https://indiawris.gov.in/wris/ ; CGWB - https://cgwb.gov.in/
- **Planned:** land cover (Bhuvan), soils (ISRIC), GRACE storage trend (consistency check only)
- **Synthetic rainfall statistics:** Srinivasan et al. (2015)

## Limitations

- Parameter ranges and lever sizes are placeholders, not yet tied to GEC-2015 norms, WTF estimates or CGWB pumping data
- Single recharge-fraction parameter; WTF, rainfall-infiltration and soil-water-balance methods not yet implemented
- Annual time step ignores seasonality; no calibration against well levels yet

## Next Steps

1. Download IMD rainfall, build basin-average annual series, run on observed rainfall
2. Obtain WRIS/CGWB well records; estimate recharge by water-table fluctuation; replace placeholder ranges
3. Final report with robustness and scenario-discovery interpretation

## References

Healy & Cook (2002), *Hydrogeology Journal*; Kasprzyk et al. (2013), *Environ. Model. Softw.*; Bryant & Lempert (2010), *Technol. Forecast. Soc. Change*; Srinivasan et al. (2015), *Hydrol. Earth Syst. Sci.*
