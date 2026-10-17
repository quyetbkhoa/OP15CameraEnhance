#!/system/bin/sh
# Manager installation only. No MMT addons or source-repo root hooks are used.
[ "$BOOTMODE" = true ] || abort 'Install using the root manager in Android.'
OP15_DIR="$MODPATH"
. "$OP15_DIR/guard.sh"
op15_check || abort "$OP15_ERROR"

# Match the existing file labels instead of guessing a vendor SELinux type.
while IFS=' ' read -r OP15_EXPECTED OP15_REL; do
  [ -n "$OP15_EXPECTED" ] || continue
  OP15_CONTEXT=$(ls -Zd "/$OP15_REL" 2>/dev/null | awk '{print $1}')
  case "$OP15_CONTEXT" in
    u:object_r:*:s0) ;;
    *) abort "Cannot read source SELinux context: /$OP15_REL" ;;
  esac
  set_perm "$OP15_DIR/payload/$OP15_REL" 0 0 0644 "$OP15_CONTEXT"
  [ "$(ls -Zd "$OP15_DIR/payload/$OP15_REL" 2>/dev/null | awk '{print $1}')" = "$OP15_CONTEXT" ] ||
    abort "Cannot preserve source SELinux context: /$OP15_REL"
done < "$OP15_DIR/payload.sha256"
set_perm "$OP15_DIR/post-fs-data.sh" 0 0 0755
ui_print 'OP15 reference hashes match. Three config files only.'
ui_print 'Activation requires a separately approved reboot.'
ui_print 'Experimental: confirm actual camera visibility and compare images.'
