"""Create the two labelled submission figures from the synthetic demo outputs.

Run from the repository root after running:
    python code/arkavathy_exploratory_model.py --demo

The outputs are synthetic pipeline-test visuals, not observed Arkavathy results.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"

DISCLAIMER_1 = (
    "Synthetic demonstration only: 2,000 uncertainty states; synthetic 2000–2022 rainfall; "
    "assumed parameter and intervention ranges. Not observed Arkavathy results."
)
DISCLAIMER_2 = (
    "Synthetic demonstration only: distributions across 2,000 sampled states per strategy. "
    "Values depend on placeholder parameters; not observed groundwater storage."
)


def main() -> None:
    summary_path = RESULTS / "DEMO_strategy_summary.csv"
    outcomes_path = RESULTS / "DEMO_strategy_outcomes.csv"
    if not summary_path.exists() or not outcomes_path.exists():
        raise FileNotFoundError(
            "Demo result files are missing. First run: "
            "python code/arkavathy_exploratory_model.py --demo"
        )

    summary = pd.read_csv(summary_path)
    outcomes = pd.read_csv(outcomes_path)
    FIGURES.mkdir(parents=True, exist_ok=True)

    # Figure 1: satisficing robustness.
    labels = summary["strategy"].tolist()
    percentages = summary["satisficing"].to_numpy() * 100
    display_labels = [
        label.replace("pumping cap", "Pumping cap").replace("MAR", "MAR")
        for label in labels
    ]
    fig, ax = plt.subplots(figsize=(12, 7.5))
    bars = ax.barh(display_labels[::-1], percentages[::-1])
    ax.set_xlim(0, max(60, float(percentages.max()) + 10))
    ax.set_xlabel("Satisficing robustness (% of 2,000 sampled states)", fontsize=12)
    ax.set_title(
        "Figure 1. Strategy performance under sampled uncertainty",
        fontsize=16,
        weight="bold",
        pad=16,
    )
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, percentages[::-1]):
        ax.text(
            bar.get_width() + 0.7,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%",
            va="center",
            fontsize=11,
        )
    fig.text(0.02, 0.015, DISCLAIMER_1, fontsize=9)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(
        FIGURES / "Figure_1_satisficing_robustness_SYNTHETIC.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)

    # Figure 2: cumulative storage-change distributions.
    ordered = labels[::-1]
    data = [
        outcomes.loc[outcomes["strategy"] == label, "cum_dS_mm"].dropna().to_numpy()
        for label in ordered
    ]
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.boxplot(data, vert=False, labels=ordered, showfliers=False)
    ax.axvline(0, linestyle="--", linewidth=1.2)
    ax.set_xlabel("Cumulative storage change over 2000–2022 (mm; modelled)", fontsize=12)
    ax.set_title(
        "Figure 2. Spread of cumulative storage outcomes across uncertainty",
        fontsize=16,
        weight="bold",
        pad=16,
    )
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    fig.text(0.02, 0.015, DISCLAIMER_2, fontsize=9)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(
        FIGURES / "Figure_2_storage_outcomes_SYNTHETIC.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)

    print("Created:")
    print(FIGURES / "Figure_1_satisficing_robustness_SYNTHETIC.png")
    print(FIGURES / "Figure_2_storage_outcomes_SYNTHETIC.png")


if __name__ == "__main__":
    main()
