#!/usr/bin/env python3
"""Build a stock-derived OP15 experiment. Standard-library only; no device writes."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import stat
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SENSORS = ("infinitimain", "infinititele", "infinitiultrawide")
TAGS = ("aps.params.snapshot.couplehdr", "aps.params.snapshot.couplehdr.face")
TARGETS = tuple(f"etc/camera/config/{name}" for name in SENSORS)
GUARDS = (
    "build.prop", "etc/camera/CameraHWConfiguration.config",
    "etc/camera/config/camera_unit_config", "etc/camera/config/oplus_camera_config",
    "etc/camera/config/oplus_camera_aps_config",
    "etc/camera/config/oplus_camera_algo_switch_config",
    "etc/camera/conf_tuning_params.json", *TARGETS,
)
NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
COMMENTS = re.compile(r"/\*.*?\*/", re.S)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def loads(text: str):
    # Native Oplus configs contain literal newlines inside JSON strings.
    # This relaxes ONLY string control characters, not duplicate object keys.
    return json.loads(text, strict=False, object_pairs_hook=no_duplicates)


def value_numbers(value: str):
    masked = COMMENTS.sub(lambda m: " " * len(m.group()), value)
    tokens = list(NUMBER.finditer(masked))
    if NUMBER.sub("", masked).strip(" ,\t\r\n"):
        raise ValueError("Unexpected nonnumeric table content")
    return tokens


def patch_config(data: bytes):
    """Byte-preserving edit of six allowlisted HDR tables across three files."""
    text = data.decode("utf-8")
    parsed = loads(text)
    decoder = json.JSONDecoder(strict=False, object_pairs_hook=no_duplicates)
    start = re.search(r'"file_data"\s*:\s*\[', text)
    if not start or not isinstance(parsed.get("file_data"), list):
        raise ValueError("Missing file_data array")
    cursor = start.end()
    edits, seen = [], set()
    while True:
        cursor += len(text[cursor:]) - len(text[cursor:].lstrip())
        if text[cursor] == "]":
            break
        row, end = decoder.raw_decode(text, cursor)
        tag = row.get("VendorTag")
        if tag in TAGS:
            if tag in seen:
                raise ValueError(f"Duplicate table: {tag}")
            seen.add(tag)
            if row.get("Type") != "Float" or str(row.get("Count")) != "153":
                raise ValueError(f"Unknown table shape: {tag}")
            value_match = re.search(r'"Value"\s*:\s*', text[cursor:end])
            if not value_match:
                raise ValueError("Missing Value")
            value_start = cursor + value_match.end()
            value, value_end = decoder.raw_decode(text, value_start)
            if not isinstance(value, str) or "\\" in text[value_start:value_end]:
                raise ValueError("Escaped/unknown table representation")
            tokens = value_numbers(value)
            if len(tokens) != 153 or [float(t.group()) for t in tokens[:3]] != [0, 11, 0]:
                raise ValueError(f"Unsupported header/length: {tag}")
            changed_rows = 0
            for index in range(15):
                base = 3 + index * 10
                iso, sharp = tokens[base], tokens[base + 3]
                if not re.match(r"\s*/\*iso\*/", value[iso.end():]):
                    raise ValueError("ISO annotation/layout mismatch")
                if not re.match(r"\s*/\*SharpLevel\*/", value[sharp.end():]):
                    raise ValueError("Sharpness annotation/layout mismatch")
                old = float(sharp.group())
                if index < 11 and float(iso.group()) <= 800 and old:
                    if old != 50:
                        raise ValueError("Unexpected stock sharpening level")
                    a, b = value_start + 1 + sharp.start(), value_start + 1 + sharp.end()
                    edits.append(dict(start=a, end=b, before=sharp.group(), after="40",
                                      table=tag, row=index, iso=float(iso.group()),
                                      line=text.count("\n", 0, a) + 1))
                    changed_rows += 1
            if changed_rows != 5:
                raise ValueError(f"Unexpected low-ISO row count in {tag}: {changed_rows}")
        cursor = end
        cursor += len(text[cursor:]) - len(text[cursor:].lstrip())
        if text[cursor] == ",":
            cursor += 1
        elif text[cursor] != "]":
            raise ValueError("Invalid file_data delimiter")
    if seen != set(TAGS):
        raise ValueError("Required HDR tables not found")
    patched = text
    for edit in sorted(edits, key=lambda e: e["start"], reverse=True):
        patched = patched[:edit["start"]] + edit["after"] + patched[edit["end"]:]
    # Scalar replacements are equal length, so invert and prove all other bytes.
    restored = patched
    for edit in sorted(edits, key=lambda e: e["start"], reverse=True):
        restored = restored[:edit["start"]] + edit["before"] + restored[edit["end"]:]
    if restored.encode("utf-8") != data:
        raise ValueError("Unexpected change outside scalar allowlist")
    after = loads(patched)
    expected = copy.deepcopy(parsed)
    for row in expected["file_data"]:
        relevant = [e for e in edits if e["table"] == row.get("VendorTag")]
        if relevant:
            old_tokens = value_numbers(row["Value"])
            v = row["Value"]
            for e in reversed(relevant):
                token = old_tokens[3 + e["row"] * 10 + 3]
                v = v[:token.start()] + e["after"] + v[token.end():]
            row["Value"] = v
    if after != expected:
        raise ValueError("Structural verification failed")
    return patched.encode("utf-8"), edits


def reference():
    return json.loads((HERE / "reference.json").read_text(encoding="utf-8"))


def verify_stock(stock: Path):
    ref = reference()
    if set(ref["files"]) != set(GUARDS):
        raise ValueError("Reference file allowlist mismatch")
    for rel, digest in ref["files"].items():
        path = stock / rel
        if not path.is_file() or sha(path.read_bytes()) != digest:
            raise ValueError(f"Stock reference mismatch: {rel}")
    return ref


def import_stock(source: Path, dest: Path):
    # Verify every input before creating a new snapshot. Never write into source.
    ref = verify_stock(source)
    dest.mkdir(parents=True, exist_ok=False)
    for rel in GUARDS:
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((source / rel).read_bytes())
    (dest / "provenance.json").write_text(json.dumps(ref, indent=2) + "\n", encoding="utf-8")
    verify_stock(dest)


def archive(entries: dict[str, bytes], path: Path):
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 17, 0, 0, 0))
            info.create_system = 3
            mode = 0o755 if name.endswith(".sh") else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)


def build(stock: Path, output: Path):
    ref = verify_stock(stock)
    # Build into a fresh versioned directory, preserving every prior candidate.
    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    entries, changes = {}, []
    for file in sorted((HERE / "module").iterdir()):
        if file.is_file():
            entries[file.name] = file.read_bytes().replace(b"\r\n", b"\n")
    for rel in TARGETS:
        payload, edits = patch_config((stock / rel).read_bytes())
        if sha(payload) != ref["expected_payload_sha256"]["odm/" + rel]:
            raise ValueError(f"Unreviewed patch result: {rel}")
        entries[f"payload/odm/{rel}"] = payload
        changes.extend(dict(file="/odm/" + rel, **e) for e in edits)
    entries["stock.sha256"] = "".join(
        f"{digest} /odm/{rel}\n" for rel, digest in sorted(ref["files"].items())
    ).encode()
    payloads = {name.removeprefix("payload/"): sha(data)
                for name, data in entries.items() if name.startswith("payload/")}
    entries["payload.sha256"] = "".join(
        f"{digest} {name}\n" for name, digest in sorted(payloads.items())
    ).encode()
    report = dict(schema=1, version="0.1.0-rc1", state="AWAITING_DEVICE",
                  reference=ref, changed_scalars=len(changes), changes=changes,
                  payload_sha256=payloads,
                  runtime="NOT RUN", image_quality="NOT RUN",
                  scope="Low-ISO coupleHDR tables; mode routing is not yet verified")
    entries["candidate.json"] = (json.dumps(report, indent=2) + "\n").encode()
    entries["README.txt"] = (HERE / "MODULE_README.txt").read_bytes()
    output.mkdir(parents=True)
    path = output / "OP15-Camera-Enhance-0.1.0-rc1-CPH2745-601.zip"
    archive(entries, path)
    validate_zip(path)
    (output / "candidate.json").write_bytes(entries["candidate.json"])
    (output / "SHA256SUMS.txt").write_text(f"{sha(path.read_bytes())}  {path.name}\n", encoding="ascii")
    # Human review: exactly what changes, without checking OEM inputs into Git.
    import difflib
    diff = []
    for rel in TARGETS:
        diff.extend(difflib.unified_diff(
            (stock / rel).read_text(encoding="utf-8").splitlines(keepends=True),
            entries[f"payload/odm/{rel}"].decode().splitlines(keepends=True),
            fromfile="stock/odm/" + rel, tofile="enhanced/odm/" + rel))
    (output / "changes.diff").write_text("".join(diff), encoding="utf-8", newline="\n")
    return path


def validate_zip(path: Path):
    with zipfile.ZipFile(path) as z:
        if len(z.namelist()) != len(set(z.namelist())) or z.testzip():
            raise ValueError("Duplicate members or ZIP CRC failure")
        expected = {p.name for p in (HERE / "module").iterdir() if p.is_file()}
        expected |= {"stock.sha256", "payload.sha256", "candidate.json", "README.txt"}
        expected |= {f"payload/odm/{rel}" for rel in TARGETS}
        if set(z.namelist()) != expected:
            raise ValueError("Unexpected archive payload")
        report = json.loads(z.read("candidate.json"))
        if report["reference"] != reference() or report["changed_scalars"] != 30:
            raise ValueError("Candidate reference/change count mismatch")
        for file in z.infolist():
            mode = (file.external_attr >> 16) & 0o777
            if mode != (0o755 if file.filename.endswith(".sh") else 0o644):
                raise ValueError("Incorrect archive permissions")
            if file.filename.endswith(".sh") and b"\r" in z.read(file):
                raise ValueError("CRLF shell file")
        expected_stock = "".join(f"{digest} /odm/{rel}\n"
                                 for rel, digest in sorted(reference()["files"].items()))
        if z.read("stock.sha256").decode() != expected_stock:
            raise ValueError("Stock manifest mismatch")
        expected_payload = "".join(f"{digest} {rel}\n"
                                   for rel, digest in sorted(report["payload_sha256"].items()))
        if z.read("payload.sha256").decode() != expected_payload:
            raise ValueError("Payload manifest mismatch")
        if set(report["payload_sha256"]) != {f"odm/{rel}" for rel in TARGETS}:
            raise ValueError("Unexpected changed paths")
        if report["payload_sha256"] != reference()["expected_payload_sha256"]:
            raise ValueError("Payload digests differ from reviewed reference")
        for rel, digest in report["payload_sha256"].items():
            if sha(z.read("payload/" + rel)) != digest:
                raise ValueError("Payload digest mismatch")
        for file in (HERE / "module").iterdir():
            if z.read(file.name) != file.read_bytes().replace(b"\r\n", b"\n"):
                raise ValueError("Module source/archive mismatch")


PROPS = ("ro.product.manufacturer", "ro.product.model", "ro.product.device",
         "ro.product.oplus.cpuinfo", "ro.vendor.product.oem", "ro.build.fingerprint",
         "ro.vendor.build.fingerprint", "ro.build.version.release", "ro.build.version.sdk",
         "ro.build.display.id", "ro.build.display.full_id", "ro.oplus.image.odm.version")


def adb_run(adb: str, serial: str, args, data=None):
    result = subprocess.run([adb, "-s", serial, *args], input=data,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if result.returncode:
        raise ValueError(f"ADB failed ({result.returncode}): {result.stderr.decode(errors='replace')[:400]}")
    return result.stdout


def capture(adb: str, serial: str, output: Path):
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", serial):
        raise ValueError("Invalid explicit device serial")
    if output.exists():
        raise ValueError("Capture output already exists")
    root_args = ["exec-out", "sh"]
    identity = adb_run(adb, serial, root_args, b"id -u\n").strip()
    if identity != b"0":
        root_args = ["exec-out", "su", "-c", "sh"]
        identity = adb_run(adb, serial, root_args, b"id -u\n").strip()
    if identity != b"0":
        raise ValueError("ADB shell/root grant is not uid 0; no daemon restart attempted")
    def read(script: str):
        return adb_run(adb, serial, root_args, script.encode())
    output.mkdir(parents=True)
    props = {key: read(f"getprop {key}\n").decode().strip() for key in PROPS}
    report = dict(schema=1, time_utc=datetime.now(timezone.utc).isoformat(), serial=serial,
                  properties=props, root_uid=0, root_transport=root_args, files={}, errors=[])
    for rel in GUARDS:
        try:
            data = read(f"cat /odm/{rel}\n")
            if not data:
                raise ValueError("empty file")
            path = output / "odm" / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            report["files"][rel] = sha(data)
        except ValueError as exc:
            report["errors"].append(f"{rel}: {exc}")
    # Explicit, read-only diagnostics. No logcat -c, camera launch or service calls.
    scripts = {
        "selinux.txt": "getenforce\n",
        "camera-service.txt": "dumpsys media.camera\n",
        "camera-package.txt": "dumpsys package com.oplus.camera\n",
        "modules.txt": "for d in /data/adb/modules/*; do [ -f \"$d/module.prop\" ] || continue; echo \"$d\"; cat \"$d/module.prop\"; for f in disable remove skip_mount; do [ ! -f \"$d/$f\" ] || echo \"flag=$f\"; done; done; true\n",
        "camera-mounts.txt": "for p in $(pidof com.oplus.camera cameraserver); do echo \"PID=$p\"; cat /proc/$p/mountinfo; done; true\n",
        "camera-contexts.txt": "ls -Zd /odm/etc/camera/config/infinitimain /odm/etc/camera/config/infinititele /odm/etc/camera/config/infinitiultrawide\n",
    }
    for name, script in scripts.items():
        try:
            (output / name).write_bytes(read(script))
        except ValueError as exc:
            report["errors"].append(f"{name}: {exc}")
    report["matches_reference"] = report["files"] == reference()["files"]
    report["note"] = "Files are from the currently visible mount namespace; overlays may be present. Review modules and process mountinfo."
    (output / "capture.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["errors"]:
        raise ValueError(f"Incomplete capture; retained at {output}. See capture.json")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import-stock")
    imp.add_argument("--odm", type=Path, required=True)
    imp.add_argument("--out", type=Path, required=True)
    make = sub.add_parser("build")
    make.add_argument("--stock", type=Path, required=True)
    make.add_argument("--out", type=Path, required=True)
    check = sub.add_parser("validate")
    check.add_argument("zip", type=Path)
    cap = sub.add_parser("capture")
    cap.add_argument("--adb", default="adb")
    cap.add_argument("--serial", required=True)
    cap.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "import-stock":
            import_stock(args.odm, args.out)
            print("Stock snapshot verified:", args.out)
        elif args.command == "build":
            print("Built and statically verified:", build(args.stock, args.out))
        elif args.command == "validate":
            validate_zip(args.zip)
            print("PASS: archive structure, permissions, manifests and digests")
        elif args.command == "capture":
            report = capture(args.adb, args.serial, args.out)
            print("Read-only capture saved:", args.out)
            print("Reference config hashes match:", report["matches_reference"])
    except (ValueError, OSError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
