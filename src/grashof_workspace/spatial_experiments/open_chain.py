"""Role-aware open-chain source model for fixed-position studies.

Conventions
-----------
- Joint order is proximal ``R1`` through distal tool ``Rn``.
- ``joint_kind_sequence`` records geometric joint letters (all ``R`` for a
  spatial 4R serial source before aggregation).
- ``joint_role_sequence`` records semantic roles such as ``R_phys``.
- Virtual closures (``S_v``) are **not** joints of the open chain; they appear
  only after a fixed-position problem is posed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .serial_chain import SerialRevoluteChain


@dataclass(frozen=True, slots=True)
class OpenChainModel:
    """Physical serial manipulator before task constraint or reduction."""

    architecture_id: str
    chain: SerialRevoluteChain
    joint_kind_sequence: tuple[str, ...]
    joint_role_sequence: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        n = self.chain.n_joints
        if len(self.joint_kind_sequence) != n:
            raise ValueError("joint_kind_sequence length must match n_joints")
        if len(self.joint_role_sequence) != n:
            raise ValueError("joint_role_sequence length must match n_joints")

    @property
    def n_joints(self) -> int:
        return self.chain.n_joints
