"""
Arkavathy sub-basin: exploratory groundwater-management model (lumped aquifer).

For every sampled combination of uncertainties (recharge fraction, specific yield, baseline pumping,
bootstrapped rainfall sequence) the script simulates each management strategy and reports
  - deepest water table (m), share of years with net storage loss, cumulative storage change (mm)
  - satisficing robustness and regret per strategy, plus optional CART scenario discovery.

Usage (run from the repository root)
    python code/arkavathy_exploratory_model.py data/processed/arkavathy_annual_rainfall.csv
    python code/arkavathy_exploratory_model.py --demo     # SYNTHETIC rainfall, only tests the pipeline

Input CSV: year, rain_mm   (basin-average annual rainfall from IMD)

!! Every value marked PLACEHOLDER is an assumed number used to exercise the model.
!! Replace it with a data-based range (GEC-2015 norms, water-table-fluctuation estimates, CGWB / well-census
!! pumping estimates) before reading anything into the results.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- uncertainty ranges (X): PLACEHOLDER, uniform sampling ---------------------------------------
RANGES = {
    "recharge_frac": (0.03, 0.15),   # fraction of annual rainfall that becomes recharge
    "sy": (0.01, 0.04),              # specific yield of the hard-rock aquifer
    "pump_mm": (60.0, 200.0),        # baseline pumping, mm/yr over the sub-basin
}
# ---- other model constants: PLACEHOLDER -----------------------------------------------------------
START_DEPTH_M = 30.0       # initial depth to water table
BASEFLOW_CUTOFF_M = 10.0   # baseflow stops once the water table is deeper than this
BASEFLOW_FRAC = 0.3        # share of recharge leaving as baseflow when the water table is at the surface
CRIT_DEPTH_M = 60.0        # failure if the water table ever gets deeper than this ...
# ... or if cumulative storage change over the period is negative

# ---- levers (L): pumping cap (mm/yr ceiling), managed aquifer recharge (mm/yr), crop-demand shift ----
# PLACEHOLDER lever sizes
INF = float("inf")
STRATEGIES = {
    "baseline":              dict(cap_mm=INF,   mar=0.0,  shift=0.0),
    "pumping cap 100 mm/yr": dict(cap_mm=100.0, mar=0.0,  shift=0.0),
    "pumping cap 70 mm/yr":  dict(cap_mm=70.0,  mar=0.0,  shift=0.0),
    "MAR 20 mm/yr":          dict(cap_mm=INF,   mar=20.0, shift=0.0),
    "crop shift 20%":        dict(cap_mm=INF,   mar=0.0,  shift=0.2),
    "combined":              dict(cap_mm=100.0, mar=20.0, shift=0.1),
}


def simulate(rain, f, sy, pump, cap_mm, mar, shift, d0=START_DEPTH_M):
    """Annual lumped water balance.  dS = R + MAR - Pump - Qb (mm);  d = depth to water table (m)."""
    d, dS_all, d_all = d0, [], []
    for P in rain:
        recharge = f * P
        pumping = min(pump * (1 - shift), cap_mm)   # crop shift cuts demand; the cap is a ceiling
        qb = BASEFLOW_FRAC * recharge * max(0.0, 1 - d / BASEFLOW_CUTOFF_M)
        dS = recharge + mar - pumping - qb
        d = max(0.0, d - dS / (1000.0 * sy))
        dS_all.append(dS)
        d_all.append(d)
    dS_all = np.array(dS_all)
    return dict(max_depth_m=max(d_all), frac_years_loss=float((dS_all < 0).mean()), cum_dS_mm=float(dS_all.sum()))


def run(rain, n=2000, seed=1):
    rng = np.random.default_rng(seed)
    states = pd.DataFrame({k: rng.uniform(*v, n) for k, v in RANGES.items()})
    seqs = [rng.choice(rain, len(rain), replace=True) for _ in range(n)]  # rainfall uncertainty: bootstrap
    states["mean_rain_mm"] = [s.mean() for s in seqs]
    rows = []
    for i in range(n):
        s = states.iloc[i]
        for name, lev in STRATEGIES.items():
            m = simulate(seqs[i], s.recharge_frac, s.sy, s.pump_mm, **lev)
            rows.append(dict(state=i, strategy=name, **m))
    res = pd.DataFrame(rows)
    res["success"] = (res.max_depth_m <= CRIT_DEPTH_M) & (res.cum_dS_mm >= 0)
    res["regret_mm"] = res.groupby("state").cum_dS_mm.transform("max") - res.cum_dS_mm
    return states, res


def summarise(res):
    g = res.groupby("strategy", sort=False)
    return pd.DataFrame({
        "satisficing": g.success.mean(),
        "median_cum_dS_mm": g.cum_dS_mm.median(),
        "p90_regret_mm": g.regret_mm.quantile(0.9),
        "median_max_depth_m": g.max_depth_m.median(),
    }).round(3)


def scenario_discovery(states, res, strategy="baseline"):
    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
    except ImportError:
        print("scikit-learn not installed: skipping CART scenario discovery")
        return
    fail = (~res[res.strategy == strategy].success).values
    X = states[["recharge_frac", "sy", "pump_mm", "mean_rain_mm"]]
    tree = DecisionTreeClassifier(max_depth=2, min_samples_leaf=50, random_state=0).fit(X, fail)
    print(f"\nCART rules for failure under '{strategy}':")
    print(export_text(tree, feature_names=list(X.columns)))


def main(path, prefix=""):
    os.makedirs("results", exist_ok=True)
    os.makedirs("figures", exist_ok=True)
    rain = pd.read_csv(path)["rain_mm"].dropna().values
    states, res = run(rain)
    summ = summarise(res)
    print(summ.to_string())
    scenario_discovery(states, res)
    states.to_csv(f"results/{prefix}sampled_states.csv", index=False)
    res.to_csv(f"results/{prefix}strategy_outcomes.csv", index=False)
    summ.to_csv(f"results/{prefix}strategy_summary.csv")

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].barh(summ.index[::-1], summ.satisficing[::-1] * 100, color="#2f7fc1")
    ax[0].set_xlabel("States where the strategy meets both criteria (%)")
    ax[0].set_title("Satisficing robustness", loc="left", fontsize=10, weight="bold")
    data = [res[res.strategy == s].cum_dS_mm.values for s in summ.index]
    ax[1].boxplot(data, vert=False, showfliers=False)
    ax[1].set_yticklabels(summ.index)
    ax[1].axvline(0, color="k", lw=0.8, ls=":")
    ax[1].invert_yaxis()
    ax[1].set_xlabel("Cumulative storage change over the period (mm)")
    ax[1].set_title("Outcome spread across uncertainty", loc="left", fontsize=10, weight="bold")
    fig.suptitle(f"{prefix}Arkavathy strategies across sampled uncertainties", fontsize=11)
    fig.tight_layout()
    fig.savefig(f"figures/{prefix}robustness.png", dpi=200)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        os.makedirs("results", exist_ok=True)
        rng = np.random.default_rng(0)
        mean, sd = 830.0, 210.0   # published basin rainfall statistics (Srinivasan et al., 2015)
        k, theta = (mean / sd) ** 2, sd ** 2 / mean
        pd.DataFrame({"year": range(2000, 2023), "rain_mm": rng.gamma(k, theta, 23)}).to_csv("results/DEMO_rain.csv", index=False)
        main("results/DEMO_rain.csv", prefix="DEMO_")
    elif len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print(__doc__)
