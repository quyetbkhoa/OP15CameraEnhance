import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import enhance as e

STOCK = e.HERE / "inputs" / "CPH2745-601-odm"
BASH = Path(os.environ.get("OP15_TEST_BASH") or
            (r"C:\Program Files\Git\bin\bash.exe" if os.name == "nt" else "/bin/bash"))


class RealStockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not STOCK.is_dir():
            raise RuntimeError("Import the pinned OEM stock snapshot before running tests")
        e.verify_stock(STOCK)

    def test_real_configs_have_exactly_thirty_allowed_edits(self):
        total = 0
        for rel in e.TARGETS:
            before = (STOCK / rel).read_bytes()
            after, edits = e.patch_config(before)
            self.assertEqual(len(edits), 10)
            self.assertEqual(len(before), len(after))
            self.assertEqual({x["before"] for x in edits}, {"50"})
            self.assertEqual({x["after"] for x in edits}, {"40"})
            self.assertTrue(all(x["iso"] <= 800 and 6 <= x["row"] <= 10 for x in edits))
            self.assertEqual(len([i for i, pair in enumerate(zip(before, after)) if pair[0] != pair[1]]), 10)
            a, b = e.loads(before.decode()), e.loads(after.decode())
            for old, new in zip(a["file_data"], b["file_data"]):
                if old.get("VendorTag") not in e.TAGS:
                    self.assertEqual(old, new)
                else:
                    ot = e.value_numbers(old["Value"])
                    nt = e.value_numbers(new["Value"])
                    self.assertEqual(len(nt), int(new["Count"]))
                    for i in range(153):
                        if i not in {3 + row * 10 + 3 for row in range(6, 11)}:
                            self.assertEqual(ot[i].group(), nt[i].group())
            total += len(edits)
        self.assertEqual(total, 30)

    def test_repatch_is_rejected(self):
        result, _ = e.patch_config((STOCK / e.TARGETS[0]).read_bytes())
        with self.assertRaisesRegex(ValueError, "Unexpected stock"):
            e.patch_config(result)

    def test_wrong_table_count_rejected(self):
        text = (STOCK / e.TARGETS[0]).read_text()
        target = text.index('"VendorTag": "' + e.TAGS[0] + '"')
        altered = text[:target] + text[target:].replace('"Count": "153"', '"Count": "152"', 1)
        with self.assertRaisesRegex(ValueError, "shape"):
            e.patch_config(altered.encode())

    def test_unknown_header_rejected(self):
        text = (STOCK / e.TARGETS[0]).read_bytes().replace(b"11 /*isoZoneNumber*/", b"12 /*isoZoneNumber*/", 1)
        with self.assertRaisesRegex(ValueError, "header"):
            e.patch_config(text)

    def test_unknown_annotation_rejected(self):
        text = (STOCK / e.TARGETS[0]).read_bytes().replace(b"/*SharpLevel*/", b"/*OtherLevel*/", 1)
        with self.assertRaisesRegex(ValueError, "annotation"):
            e.patch_config(text)

    def test_missing_table_rejected(self):
        text = (STOCK / e.TARGETS[0]).read_bytes().replace(e.TAGS[0].encode(), b"unknown.table", 1)
        with self.assertRaisesRegex(ValueError, "not found"):
            e.patch_config(text)

    def test_duplicate_table_rejected(self):
        parsed = e.loads((STOCK / e.TARGETS[0]).read_text())
        parsed["file_data"].append(copy.deepcopy(next(x for x in parsed["file_data"] if x.get("VendorTag") == e.TAGS[0])))
        # Preserve literal newlines so this test reaches duplicate detection.
        text = json.dumps(parsed).replace("\\n", "\n")
        with self.assertRaisesRegex(ValueError, "Duplicate table"):
            e.patch_config(text.encode())

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            e.loads('{"file_data": [], "file_data": []}')

    def test_numeric_table_rejects_unknown_content(self):
        with self.assertRaises(ValueError):
            e.value_numbers("50, potato, 11")

    def test_wrong_stock_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(STOCK, root / "bad")
            (root / "bad" / e.TARGETS[0]).write_bytes(b"wrong firmware")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                e.build(root / "bad", root / "out")
            self.assertFalse((root / "out").exists())

    def test_archive_reproducibility_validation_and_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = e.build(STOCK, root / "a")
            b = e.build(STOCK, root / "b")
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with self.assertRaisesRegex(ValueError, "exists"):
                e.build(STOCK, root / "a")
            e.validate_zip(a)
            with zipfile.ZipFile(a) as z:
                self.assertNotIn("system.prop", z.namelist())
                self.assertNotIn("persist.prop", z.namelist())
                self.assertEqual(len([n for n in z.namelist() if n.startswith("payload/")]), 3)

    def test_archive_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = e.build(STOCK, root / "source")
            with zipfile.ZipFile(source) as z:
                entries = {name: z.read(name) for name in z.namelist()}
            entries["payload/odm/" + e.TARGETS[0]] += b"modified"
            e.archive(entries, root / "tampered.zip")
            with self.assertRaisesRegex(ValueError, "digest"):
                e.validate_zip(root / "tampered.zip")

    def test_rewritten_archive_manifests_still_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = e.build(STOCK, root / "source")
            with zipfile.ZipFile(source) as z:
                entries = {name: z.read(name) for name in z.namelist()}
            rel = "odm/" + e.TARGETS[0]
            entries["payload/" + rel] += b"modified"
            report = json.loads(entries["candidate.json"])
            report["payload_sha256"][rel] = e.sha(entries["payload/" + rel])
            entries["candidate.json"] = json.dumps(report).encode()
            entries["payload.sha256"] = "".join(
                f"{digest} {name}\n" for name, digest in sorted(report["payload_sha256"].items())
            ).encode()
            e.archive(entries, root / "tampered.zip")
            with self.assertRaisesRegex(ValueError, "reviewed reference"):
                e.validate_zip(root / "tampered.zip")


class ShellTests(unittest.TestCase):
    def setUp(self):
        if not BASH.is_file():
            raise RuntimeError("A real shell is required for safety regression tests")
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root_posix = self.root.as_posix()
        if os.name == "nt":
            self.root_posix = "/" + self.root_posix[0].lower() + self.root_posix[2:]
        self.pkg = e.build(STOCK, self.root / "build")
        self.mod = self.root / "module"
        with zipfile.ZipFile(self.pkg) as z:
            z.extractall(self.mod)
        shutil.copytree(STOCK, self.root / "device" / "odm")
        (self.root / "device" / "data" / "adb" / "modules").mkdir(parents=True)
        # Redirect absolute device paths in TEST COPIES only. Production scripts
        # have no environment switch that could bypass real path verification.
        guard = (self.mod / "guard.sh").read_text()
        guard = guard.replace("/data/adb/", self.root_posix + "/device/data/adb/")
        (self.mod / "guard.sh").write_text(guard, newline="\n")
        manifest = (self.mod / "stock.sha256").read_text().replace(" /odm/", " " + self.root_posix + "/device/odm/")
        (self.mod / "stock.sha256").write_text(manifest, newline="\n")

    def tearDown(self):
        self.temp.cleanup()

    def run_shell(self, script, cpu="SM8850", oem="CPH2745", enforcing="Enforcing", failure=0):
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"
        prelude = f'''set -eu
OP15_DIR='{self.root_posix}/module'
getprop() {{
 case "$1" in
 ro.product.manufacturer) echo OnePlus ;;
 ro.product.oplus.cpuinfo) echo '{cpu}' ;;
 ro.vendor.product.oem) echo '{oem}' ;;
 esac
}}
getenforce() {{ echo '{enforcing}'; }}
. "$OP15_DIR/guard.sh"
'''
        return subprocess.run([str(BASH), "-c", prelude + script], env=env, capture_output=True, text=True, timeout=30)

    def check_guard(self, **kwargs):
        return self.run_shell('if op15_check; then echo PASS; else echo "$OP15_ERROR"; exit 1; fi', **kwargs)

    def test_matching_reference_passes(self):
        result = self.check_guard()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_wrong_soc_blocked(self):
        self.assertNotEqual(self.check_guard(cpu="SM8750").returncode, 0)

    def test_wrong_oem_blocked(self):
        self.assertNotEqual(self.check_guard(oem="CPH2747").returncode, 0)

    def test_permissive_blocked(self):
        self.assertNotEqual(self.check_guard(enforcing="Permissive").returncode, 0)

    def test_stock_mismatch_blocked(self):
        (self.root / "device" / "odm" / "build.prop").write_bytes(b"changed")
        result = self.check_guard()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Stock mismatch", result.stdout)

    def test_payload_mismatch_blocked(self):
        (self.mod / "payload" / "odm" / e.TARGETS[0]).write_bytes(b"changed")
        result = self.check_guard()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Payload mismatch", result.stdout)

    def test_empty_manifest_blocked(self):
        (self.mod / "stock.sha256").write_bytes(b"")
        self.assertNotEqual(self.check_guard().returncode, 0)

    def test_incomplete_manifest_blocked(self):
        lines = (self.mod / "stock.sha256").read_text().splitlines(keepends=True)
        (self.mod / "stock.sha256").write_text("".join(lines[:-1]), newline="\n")
        self.assertNotEqual(self.check_guard().returncode, 0)

    def test_other_camera_module_blocked(self):
        (self.root / "device" / "data" / "adb" / "modules" / "old_ocvm").mkdir()
        self.assertNotEqual(self.check_guard().returncode, 0)

    def test_disabled_other_camera_module_allowed(self):
        other = self.root / "device" / "data" / "adb" / "modules" / "old_ocvm"
        other.mkdir()
        (other / "disable").touch()
        self.assertEqual(self.check_guard().returncode, 0)

    def test_shell_syntax(self):
        for file in (e.HERE / "module").glob("*.sh"):
            result = subprocess.run([str(BASH), "-n", str(file)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def boot_simulation(self, fail_mount):
        script = (e.HERE / "module" / "post-fs-data.sh").read_text()
        script = script.replace('OP15_DIR=${0%/*}', "OP15_DIR='" + self.root_posix + "/module'")
        script = script.replace('"/$OP15_REL"', '"' + self.root_posix + '/device/$OP15_REL"')
        (self.mod / "boot-test.sh").write_text(script, newline="\n")
        # These shell functions SIMULATE bind/unmount using private temp copies.
        # They cannot invoke real mount or umount and never touch /odm.
        mock = f'''
OP15_CALLS=0
mount() {{
 OP15_CALLS=$((OP15_CALLS + 1))
 [ "$OP15_CALLS" -ne {fail_mount} ] || return 1
 cp "$4" "$4.backup"
 cp "$3" "$4"
}}
umount() {{ cp "$1.backup" "$1"; }}
. "$OP15_DIR/boot-test.sh"
'''
        return self.run_shell(mock)

    def test_boot_success_mounts_only_expected_files_simulated(self):
        result = self.boot_simulation(99)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for rel in e.TARGETS:
            expected, _ = e.patch_config((STOCK / rel).read_bytes())
            self.assertEqual((self.root / "device" / "odm" / rel).read_bytes(), expected)
        self.assertIn("NOT VERIFIED", (self.mod / "runtime-status.txt").read_text())

    def test_boot_second_mount_failure_rolls_back_first_simulated(self):
        result = self.boot_simulation(2)
        self.assertNotEqual(result.returncode, 0)
        for rel in e.TARGETS:
            self.assertEqual((self.root / "device" / "odm" / rel).read_bytes(), (STOCK / rel).read_bytes())
        self.assertIn("rolled back", (self.mod / "runtime-status.txt").read_text())

    def test_boot_mismatch_does_not_mount_simulated(self):
        (self.root / "device" / "odm" / "build.prop").write_bytes(b"OTA")
        result = self.boot_simulation(99)
        self.assertNotEqual(result.returncode, 0)
        for rel in e.TARGETS:
            self.assertEqual((self.root / "device" / "odm" / rel).read_bytes(), (STOCK / rel).read_bytes())


class CaptureTests(unittest.TestCase):
    def test_adb_always_binds_explicit_serial_and_preserves_binary(self):
        response = subprocess.CompletedProcess([], 0, stdout=b"a\x00b\r\n", stderr=b"")
        with patch("enhance.subprocess.run", return_value=response) as run:
            self.assertEqual(e.adb_run("adb", "serial-one", ["exec-out", "sh"], b"id\n"), b"a\x00b\r\n")
            self.assertEqual(run.call_args.args[0][:3], ["adb", "-s", "serial-one"])

    def test_capture_refuses_non_root_before_creating_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "capture"
            with patch("enhance.adb_run", return_value=b"2000\n"):
                with self.assertRaisesRegex(ValueError, "uid 0"):
                    e.capture("adb", "serial-one", output)
            self.assertFalse(output.exists())

    def test_capture_rejects_invalid_serial(self):
        with self.assertRaisesRegex(ValueError, "serial"):
            e.capture("adb", "serial;echo", Path("unused"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
