"""Visualization package exports."""

from .comparisons import plot_architecture_panel, plot_residual_sweeps
from .robot_plot import format_geometry_report, plot_robot_axes, plot_robot_with_links
from .spherical_linkage import (
    plot_architecture_a_worked_closure,
    plot_sign_type_table,
    plot_spherical_fourbar,
    plot_type_fixture_gallery,
)

__all__ = [
    "format_geometry_report",
    "plot_architecture_a_worked_closure",
    "plot_architecture_panel",
    "plot_residual_sweeps",
    "plot_robot_axes",
    "plot_robot_with_links",
    "plot_sign_type_table",
    "plot_spherical_fourbar",
    "plot_type_fixture_gallery",
]
