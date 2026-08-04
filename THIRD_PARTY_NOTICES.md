# Third-party robot descriptions

This repository stores source URLs, selection metadata, and project-authored
fixtures. It does not vendor the external robot repositories.

Running `scripts/fetch_robot_corpus.py` clones upstream sources into a gitignored
folder and records the resolved commit. Every upstream source remains governed
by the license included in that exact snapshot.

Special handling:

- Universal Robots: UR8 Long, UR15, UR20, and UR30 mesh assets have additional
  graphical-documentation terms.
- Fetch: `fetch_description` is licensed CC BY-NC-SA 4.0. Keep it as a local
  research source unless the intended use is confirmed to comply.
- FANUC: the ROS-Industrial package is community supported and is not an OEM
  representation or endorsement.
