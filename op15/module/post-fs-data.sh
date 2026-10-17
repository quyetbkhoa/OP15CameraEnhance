#!/system/bin/sh
OP15_DIR=${0%/*}
. "$OP15_DIR/guard.sh"
OP15_STATUS="$OP15_DIR/runtime-status.txt"
if ! op15_check; then
  printf 'BLOCKED: %s\n' "$OP15_ERROR" > "$OP15_STATUS"
  exit 1
fi

# skip_mount prevents automatic overlaying before compatibility checks.
# Bind only the three existing config files; never remount /odm writable.
OP15_MOUNTED=
OP15_FAILED=false
while IFS=' ' read -r OP15_EXPECTED OP15_REL; do
  [ -n "$OP15_EXPECTED" ] || continue
  if mount -o bind "$OP15_DIR/payload/$OP15_REL" "/$OP15_REL"; then
    OP15_MOUNTED="$OP15_REL $OP15_MOUNTED"
  else
    OP15_FAILED=true
    break
  fi
  if [ "$(op15_hash "/$OP15_REL")" != "$OP15_EXPECTED" ]; then
    OP15_FAILED=true
    break
  fi
done < "$OP15_DIR/payload.sha256"

if "$OP15_FAILED"; then
  OP15_ROLLBACK_FAILED=false
  for OP15_REL in $OP15_MOUNTED; do
    # Only unmount files this invocation successfully bound.
    umount "/$OP15_REL" || OP15_ROLLBACK_FAILED=true
  done
  if "$OP15_ROLLBACK_FAILED"; then
    printf '%s\n' 'ERROR: partial mount rollback failed; disable module and reboot.' > "$OP15_STATUS"
  else
    printf '%s\n' 'BLOCKED: bind/readback failed; partial mounts rolled back.' > "$OP15_STATUS"
  fi
  exit 1
fi
printf '%s\n' 'MOUNTED_IN_BOOT_SCRIPT_NAMESPACE: camera process visibility and image quality NOT VERIFIED.' > "$OP15_STATUS"
