# Back to Grashof — Mechanism-Based Workspace Characterization

A research codebase for characterizing manipulator orientation capability through
fixed-position kinematic decomposition: fix the tool position, form the exact
virtual closed source mechanism, certify lower-dimensional mechanism behaviors
where valid, and reconstruct orientation or pointing coverage under an explicit
compatibility contract.

## 1. Project question

At a Cartesian point \(p^*\):

1. what configurations remain after \(p(q)=p^*\)?
2. what orientation or pointing image do those configurations generate?
3. can the source mechanism be reduced into verified lower-dimensional families?
4. do certified mechanism behaviors, under coverage stitching, recover the parent task image?

```text
open chain
  -> fixed-position fiber/parent
  -> exact virtual closure
  -> orientation/pointing image
  -> certified kinematic decomposition
  -> mechanism behavior certificate
  -> coverage/compatibility stitching
  -> independent workspace validation
```

## 2. Trusted result and current status

The planar 3R implementation is the trusted analytical reference. The active
spatial program is the L3–L7 fixed-position decomposition ladder. L5 currently
has a hardened but incomplete parent implementation, no accepted child family,
and a rejected fixed-axis `UUUR` hypothesis. L6 and L7 remain blocked/deferred.

Live ledger: [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md).

## 3. What “Grashof” means here

Classical Grashof classification is one mechanism-behavior description used in
the planar reference. The general program does not assume that every spatial
workspace admits one universal Grashof inequality.

## 4. Repository map

```text
README.md                 this entry page
docs/README.md            documentation navigation authority
docs/PROJECT_THESIS.md    scientific thesis
docs/CURRENT_STATUS.md    status ledger
docs/ROADMAP.md           future gates only
docs/theory/              framework, ladder, stitching, math notes
docs/methods/             implementation contracts
docs/reference/           ADRs and evidence index
docs/archive/             historical programs, sprints, workshops, audits
src/grashof_workspace/    package (name retained; branding migration deferred)
tests/                    mathematical and research-contract tests
results/                  reproducible readouts
```

Start with [`docs/README.md`](docs/README.md).

## 5. Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" --config-settings editable_mode=strict
pytest
ruff check .
mypy src
grashof-workspace --l1 2.0 --l2 2.0 --l3 1.0 --output workspace.png
grashof-workspace --atlas --output-dir outputs/atlas
```

Package name, console scripts, and import paths remain `grashof_workspace` /
`grashof-workspace` in this cleanup; renaming is a separate future PR.

## 6. Scientific claim boundaries

- Matching DOF counts or visually similar topologies do not establish equivalence.
- Spatial four-bar explorer results are mechanism-lab evidence, not workspace evidence, without source provenance and reconstruction.
- A collection of one-dimensional fibers is not a complete higher-dimensional parent.
- Descriptor discovery and broad atlas rules stay blocked until reconstruction succeeds.
- `dexterous_workspace` means full declared orientation coverage; pointing-complete is an explicit \(S^2\) claim when roll is excluded.
