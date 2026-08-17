"""Leaf re-seeding: moving along one leaf does not create a new leaf."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.leaf_family import reseed_audit


def test_reseed_same_branch_passes() -> None:
    qs = tuple((float(i) * 0.01, 0.0, 0.0, 0.0, 0.0) for i in range(9))
    ds = tuple((1.0, 0.0, 0.0) for _ in qs)
    audit = reseed_audit(qs, ds, q_tol=0.05, p_tol=0.05)
    assert audit.status == "PASS"
    assert audit.n_reseeds == 3
