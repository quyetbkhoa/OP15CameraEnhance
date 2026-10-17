# OP15 Camera Enhance

Read `.ai/PROJECT.md`, `.ai/NOW.md`, `HANDOFF.md`, and `GUIDE.md` before substantive
work. Inspect Git status/branch; preserve unrelated changes and all candidate
artifacts. Use the project-continuity skill if available; these local records
also stand alone on another machine. Prefer `rg`/`rg --files` for searches.

## Delivery

- `main` is the documentation bootstrap. Experimental source and rc1 are on `dev`.
  Use a task branch from `dev`, self-test, checkpoint, then integrate into `dev`.
- No stable promotion of implementation to `main` until the owner accepts the
  exact candidate and authorizes publication. Publishing the initial handoff is
  not evidence of device acceptance or permission for later arbitrary pushes.
- Preserve the committed `artifacts/0.1.0-rc1/` files byte-for-byte. Put changed
  candidates in new versioned directories. Do not rewrite Git history or inputs.
- No global Git/config changes, extra providers/services or tool installations
  as routine setup. Do not store credentials, live device captures or photos in Git.

## Device work

- The user's current OP15 model, serial, build and root manager are UNKNOWN.
  A stock ROM reference is not a live-device identity. Bind every ADB invocation
  to a freshly confirmed explicit serial; never act on the first attached device.
- The owner will connect the phone after preparation. Start with read-only
  inspection once they confirm it is attached. Root connection is not permission
  to install a module, restart services/adbd, clear data/logs, flash or reboot.
  Present the concrete change and rollback before obtaining mutation approval.
- Do not weaken SELinux, bypass compatibility hashes, spoof model IDs, persist
  tuning properties, force clock/bandwidth/buffer values or transplant OP13/X8U
  libraries/calibration by default. Review and justify any changed scope first.
- Actual camera/cameraserver namespace visibility and correct source contexts
  must be checked; a successful bind in a script namespace is insufficient.
- Keep offline, simulated, installed, reboot-pending, active and user-accepted
  states distinct. Property/file/map presence does not prove algorithm execution
  or improved photos. Require matched stock/enhance captures and stability checks.

## Validation

Follow `GUIDE.md` from a fresh clone. Reference stock config bytes are pinned by
`op15/reference.json`; they must not undergo newline conversion. Raw ROM images,
libraries, calibration partitions and live device captures are not in this repo.
Record actual test results and limitations. Do not claim Android boot or hardware
validation from Python tests or the shell mount simulations.
