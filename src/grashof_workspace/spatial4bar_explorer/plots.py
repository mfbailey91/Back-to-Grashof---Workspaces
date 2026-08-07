from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

from .analysis import summarize_winding_pairs
from .descriptors import sample_descriptor_values
from .families import ORDERED_FAMILIES
from .models import BranchResult, GeometrySample


def plot_family_case_counts(outpath: Path) -> None:
    labels = [family.value for family in ORDERED_FAMILIES]
    counts = [2 for _ in ORDERED_FAMILIES]
    plt.figure(figsize=(8, 4.5))
    plt.bar(labels, counts)
    plt.xlabel("Ordered one-DOF family")
    plt.ylabel("Virtual tool-axis tests")
    plt.title("Twelve virtual-crank cases across six ordered families")
    plt.tight_layout()
    plt.savefig(outpath, dpi=160)
    plt.close()


def plot_descriptor_histogram(samples: list[GeometrySample], descriptor_name: str, outpath: Path) -> None:
    values = sample_descriptor_values(samples, descriptor_name)
    plt.figure(figsize=(7, 4.5))
    plt.hist(values, bins=12)
    plt.xlabel(descriptor_name)
    plt.ylabel("count")
    plt.title(f"Sampled descriptor distribution: {descriptor_name}")
    plt.tight_layout()
    plt.savefig(outpath, dpi=160)
    plt.close()


def plot_classification_counts(results: list[BranchResult], outpath: Path) -> None:
    counter: Counter[str] = Counter()
    for result in results:
        counter[result.class_alpha.value] += 1
        counter[result.class_beta.value] += 1
    labels = list(counter.keys())
    values = [counter[label] for label in labels]
    plt.figure(figsize=(8, 4.5))
    plt.bar(labels, values)
    plt.xlabel("Classification")
    plt.ylabel("count")
    plt.title("Mock branch classifications across sampled mechanisms")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(outpath, dpi=160)
    plt.close()


def plot_winding_pair_counts(results: list[BranchResult], outpath: Path) -> None:
    pair_counts = summarize_winding_pairs(results)
    labels = list(pair_counts.keys())
    values = [pair_counts[label] for label in labels]
    plt.figure(figsize=(8, 4.5))
    plt.bar(labels, values)
    plt.xlabel("Mock winding pair (w_alpha, w_beta)")
    plt.ylabel("count")
    plt.title("Mock winding-pair counts (placeholder until true continuation)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(outpath, dpi=160)
    plt.close()


def plot_case_schematic(case_name: str, outpath: Path) -> None:
    joints = list(case_name)
    x = list(range(len(joints)))
    y = [0 for _ in joints]
    plt.figure(figsize=(7.5, 1.8))
    plt.plot(x, y, marker="o")
    for idx, joint in enumerate(joints):
        plt.text(x[idx], y[idx] + 0.05, joint, ha="center", va="bottom", fontsize=12)
    plt.yticks([])
    plt.xticks(x, [f"J{i+1}" for i in x])
    plt.title(f"Ordered family schematic: {case_name}")
    plt.tight_layout()
    plt.savefig(outpath, dpi=160)
    plt.close()
