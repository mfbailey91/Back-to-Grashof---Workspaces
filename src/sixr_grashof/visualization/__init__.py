"""Visualization package exports."""

from .comparisons import plot_architecture_panel, plot_residual_sweeps
from .experiments import (
    plot_agreement_map,
    plot_confusion_heatmap,
    plot_connectivity_components,
    plot_gate2_coverage_convergence,
    plot_offset_sweeps,
    plot_orientation_sample_cloud,
    plot_residual_vs_error,
    plot_solver_diagnostics,
)
from .reductions import (
    plot_exact_vs_offset_reduction,
    plot_hand_link_sensitivity,
    plot_linkage_type_map,
    plot_prediction_card,
    plot_regional_reduction_panel,
    plot_spherical_reduction_panel,
)
from .robot_plot import format_geometry_report, plot_robot_axes, plot_robot_with_links
from .spherical_linkage import (
    plot_architecture_a_worked_closure,
    plot_sign_type_table,
    plot_spherical_fourbar,
    plot_type_fixture_gallery,
)

__all__ = [
    "format_geometry_report",
    "plot_agreement_map",
    "plot_architecture_a_worked_closure",
    "plot_architecture_panel",
    "plot_confusion_heatmap",
    "plot_connectivity_components",
    "plot_exact_vs_offset_reduction",
    "plot_gate2_coverage_convergence",
    "plot_hand_link_sensitivity",
    "plot_linkage_type_map",
    "plot_offset_sweeps",
    "plot_orientation_sample_cloud",
    "plot_prediction_card",
    "plot_regional_reduction_panel",
    "plot_residual_sweeps",
    "plot_residual_vs_error",
    "plot_robot_axes",
    "plot_robot_with_links",
    "plot_sign_type_table",
    "plot_solver_diagnostics",
    "plot_spherical_fourbar",
    "plot_spherical_reduction_panel",
    "plot_type_fixture_gallery",
]
