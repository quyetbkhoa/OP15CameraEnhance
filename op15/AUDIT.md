# Source review and decisions

Reviewed upstream main 09391e981a6874cbee395214e673f50e49b033dd and dev
88dcbfc286f6e2f103e50228100e5c1c03efc1da on 2026-10-17.

The main branch README describes the original separation between enhancement and
an X8U processing addon. Current main hooks also contain donor pipeline activation:
`post-fs-data.sh` sets HDR/bokeh/video properties, calls `setenforce 0`, forces
clock/bandwidth/buffer values, and removes diagnostic files. `common/install.sh`
clears Camera app data; `service.sh` persists properties and restarts cameraserver.
These root hooks and the MMT addon archive are excluded from the OP15 ZIP.

The inspected dev root has OP13 `dodge*` configs, tuned sensor blobs and libraries.
No such OP13 data is a suitable drop-in OP15 payload. The preserved OP15 ODM has
`infiniti*` config names and SM8850 identity. Original inputs are preserved.

Reference stock is CPH2745_16.0.10.601(EX01), derived from the extraction metadata
in H:/ColorNT-work/port-v14-donor-odm-20261014-000001/donor/extraction.json.
`reference.json` records SHA256 of the ten files actually used as guards. This is
content pinning of an existing extraction, not independent authentication of the
entire firmware archive, and not proof that the owner's phone uses this build.

The six selected stock tables are Float/Count=153: three header fields followed
by fifteen ten-value records. The active-record header is 11. Each table has
five active low-ISO records (ISO <= 800); their annotated SharpLevel is 50.
rc1 changes only these values to 40. The native file format uses literal
multiline JSON strings, so parsing allows string control characters but rejects
duplicate keys. Numeric positions, counts, annotations and header are checked;
source bytes outside the thirty numeric spans must be identical.

The existing table's denoiseEnable is 0; rc1 does not enable it or claim changes
to denoising. No new table or property is invented. The parameter label and table
structure motivate the experiment, but runtime consumption, scene selection,
mode sharing and quality impact remain unverified until rooted-device inspection
and controlled captures. Do not equate a 20% lower numeric value with a measured
20% reduction in sharpening, or claim all main-module features are implemented.

Module mounting is deliberately explicit and conditional. Three individual bind
mounts are attempted only after all checks pass. Any failed bind/readback triggers
rollback of successful mounts from that invocation. No global unmount, persistent
property cleanup, cameraserver restart or partition write is part of this build.
Boot-script namespace success does not establish visibility in camera processes.

30 offline regressions passed on Windows/Python 3.11 with Git Bash. Actual Android
root-manager installation, SELinux access, real bind mount rollback, boot, camera
stability and image quality were NOT RUN. Candidate remains AWAITING_DEVICE.
