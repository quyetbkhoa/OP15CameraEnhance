# Current state

State: AWAITING_USER
Date: 2026-10-17 (Asia/Bangkok)
Gate: owner connects OP15 for read-only inspection; no device acceptance yet.
Integration branch: dev; main remains documentation bootstrap.

Candidate: artifacts/0.1.0-rc1/OP15-Camera-Enhance-0.1.0-rc1-CPH2745-601.zip
SHA256: 90eb0eddfbd23f52b1f9c4d6a7cf322309097c8e2fd7bce910b3ced6426831d0
Reference: CPH2745_16.0.10.601(EX01), SM8850; current phone identity UNKNOWN.
Exact scope: 30 low-ISO HDR SharpLevel edits (50 -> 40), no other source bytes.

Original candidate: 30/30 offline tests; static ZIP validation and reproducibility
passed. Mount/rollback tests simulated. See PUBLISH_VALIDATION.json for the clean
handoff-clone verification; HANDOFF.md for limitations and operational context.
ADB/install/Android boot/SELinux/actual namespace visibility/algorithm activation/
capture stability/image quality: NOT RUN. Do not report them as passing.

The owner authorized upload of this handoff to OP15CameraEnhance. Implementation
source, frozen ZIP, minimal pinned stock configs, GUIDE and HANDOFF_PROMPT are
included. OP13-OCVM remote/history are untouched. Git commit identity in this
checkout uses the verified authenticated GitHub login and its ID-based noreply
address; global Git settings were not changed.

Next: read AGENTS/PROJECT/HANDOFF/GUIDE, verify clone/tests, wait for the owner to
connect the phone. Then read fresh adb devices -l, use explicit serial, run the
read-only capture, inspect conflicts/build/schema/context/namespaces. Firmware
mismatch requires a new stock-specific candidate. Present a concrete install and
rollback plan before requesting device-mutation approval. Preserve rc1 and inputs.
