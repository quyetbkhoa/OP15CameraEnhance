OP15 Camera Enhance 0.1.0-rc1 -- AWAITING DEVICE VALIDATION

Reference: OnePlus 15, CPH2745 ODM, 16.0.10.601(EX01), SM8850.
This is an experimental configuration candidate, not a proven quality upgrade.
The owner's current OP15 firmware has not been inspected.

Exactly 30 scalar edits in three stock sensor configuration files:
infinitimain, infinititele, infinitiultrawide.
In aps.params.snapshot.couplehdr and its .face table, SharpLevel 50 -> 40
for the five active ISO <= 800 rows. High-ISO rows and denoise stay stock.
Shared algorithm tables can affect more than one UI mode; live routing is unknown.
Portrait-specific tables, front camera, video, color, AWB, sensor topology,
libraries, neural models, buffer counts and performance policy are untouched.

Install only after reviewing a read-only capture of this exact phone, its active
modules and firmware hashes. Root manager install only; no recovery installer.
The installer and every boot check identity, SELinux Enforcing, stock config
hashes and payload hashes. A mismatch blocks activation.

No mount provider/metamodule is installed. skip_mount is intentional: this
module's own post-fs-data script binds three individual files AFTER its checks.
Mount visibility in Camera/cameraserver namespaces still needs device testing.
runtime-status.txt reports only the boot script namespace, not quality or use.

Installation does not clear Camera data, write persistent properties, restart
cameraserver, modify SELinux policy or reboot the device. Activation requires a
separately approved reboot. If a mount fails, partial binds are unmounted.

Rollback: disable/remove op15_camera_enhance in the root manager and reboot.
Stock partitions are never overwritten. Do not restore old OP13 modules.
After an OTA, repeat capture and rebuild; do not bypass the hash checks.
