# OP15 Camera Enhance

Standalone repository: https://github.com/quyetbkhoa/OP15CameraEnhance.git
Goal: enhance native OnePlus 15 imaging with stock-derived, bounded changes and
actual-device evidence. Do not transplant OP13/X8U pipelines by default.

Profile: staged. main is a documentation-only bootstrap; dev holds the initial
experimental handoff; use feat/fix task branches from dev. No implementation
promotion to main until exact-candidate device acceptance and publication scope.

User explicitly authorized publishing source, guide and agent handoff to this
new remote on 2026-10-17. This publication is not device acceptance or permission
to install/reboot. No deployment or future arbitrary push authority is inferred.

Frozen rc1: see HANDOFF.md and artifacts/0.1.0-rc1/. Reference stock is CPH2745
16.0.10.601(EX01), not the owner's currently uninspected phone. Ten minimal pinned
OEM configs are included to make clone/build/tests portable. Live captures/photos
remain ignored and local. Preserve stock and prior candidates.

Acceptance requires real identity/build/root-manager review, installation only
with authorization, correct camera namespace/context/hash visibility, runtime
algorithm evidence where obtainable, stable capture flows and controlled A/B
images. Offline tests and mapped files alone cannot satisfy these requirements.
