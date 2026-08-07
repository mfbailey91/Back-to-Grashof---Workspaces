from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .models import BranchClass
from .winding import WindingClassification


def plot_unwrapped_tool_angles(classification: WindingClassification, outpath: Path) -> None:
    cycle = classification.cycle
    arclength = [point.arclength for point in cycle.points]
    unwrapped = np.asarray(cycle.unwrapped_q, dtype=float)
    names = list(cycle.coordinate_names)
    alpha = unwrapped[:, names.index("tool_alpha")]
    beta = unwrapped[:, names.index("tool_beta")]
    figure = plt.figure(figsize=(9.0, 5.0))
    axis = figure.add_subplot(111)
    axis.plot(arclength, alpha, label="tool_alpha (unwrapped)")
    axis.plot(arclength, beta, label="tool_beta (unwrapped)")
    if cycle.return_index is not None:
        axis.axvline(arclength[cycle.return_index], color="0.4", linestyle="--", label="return")
    axis.set_xlabel("Continuation arclength")
    axis.set_ylabel("Unwrapped angle [rad]")
    axis.set_title(
        f"{classification.sample_id}: W=({classification.w_alpha}, {classification.w_beta}) "
        f"[{classification.class_alpha.value}/{classification.class_beta.value}]"
    )
    axis.legend(loc="best", fontsize="small")
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def plot_winding_summary(classifications: list[WindingClassification], outpath: Path) -> None:
    labels = [item.sample_id.replace("uuur_physical_", "p") for item in classifications]
    alpha_vals = [0 if item.w_alpha is None else item.w_alpha for item in classifications]
    beta_vals = [0 if item.w_beta is None else item.w_beta for item in classifications]
    index = np.arange(len(labels))
    width = 0.38
    figure = plt.figure(figsize=(10.0, 4.8))
    axis = figure.add_subplot(111)
    axis.bar(index - width / 2, alpha_vals, width, label="w_alpha")
    axis.bar(index + width / 2, beta_vals, width, label="w_beta")
    axis.set_xticks(index)
    axis.set_xticklabels(labels, rotation=30, ha="right")
    axis.set_ylabel("Winding")
    axis.set_title("V04 UUUR true windings from returned cycles")
    axis.axhline(0.0, color="0.5", linewidth=0.8)
    axis.legend(loc="best")
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)


def plot_classification_cards(
    classifications: list[WindingClassification],
    outpath: Path,
) -> None:
    counts = {label.value: 0 for label in BranchClass}
    for item in classifications:
        counts[item.class_alpha.value] += 1
        counts[item.class_beta.value] += 1
    labels = list(counts.keys())
    values = [counts[label] for label in labels]
    figure = plt.figure(figsize=(8.5, 4.5))
    axis = figure.add_subplot(111)
    axis.bar(labels, values)
    axis.set_xlabel("BranchClass (tool-axis instances)")
    axis.set_ylabel("count")
    axis.set_title("V04 UUUR crank/rocker counts from continued windings")
    figure.tight_layout()
    figure.savefig(outpath, dpi=170)
    plt.close(figure)
