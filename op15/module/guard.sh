#!/system/bin/sh
# Sourced by the installer and boot script. No changes to device state here.
op15_hash() {
  sha256sum "$1" 2>/dev/null | awk '{print $1}'
}

op15_check() {
  OP15_ERROR=
  [ -s "$OP15_DIR/stock.sha256" ] && [ -s "$OP15_DIR/payload.sha256" ] || {
    OP15_ERROR='Missing compatibility/payload manifests'; return 1;
  }
  [ "$(wc -l < "$OP15_DIR/stock.sha256" | tr -d ' ')" = 10 ] &&
  [ "$(wc -l < "$OP15_DIR/payload.sha256" | tr -d ' ')" = 3 ] || {
    OP15_ERROR='Incomplete compatibility/payload manifests'; return 1;
  }
  [ "$(getprop ro.product.manufacturer)" = OnePlus ] || {
    OP15_ERROR='Not a OnePlus device'; return 1;
  }
  [ "$(getprop ro.product.oplus.cpuinfo)" = SM8850 ] || {
    OP15_ERROR='Expected OP15 SM8850 ODM identity'; return 1;
  }
  [ "$(getprop ro.vendor.product.oem)" = CPH2745 ] || {
    OP15_ERROR='Reference candidate requires CPH2745 ODM'; return 1;
  }
  [ "$(getenforce)" = Enforcing ] || {
    OP15_ERROR='Restore SELinux Enforcing before testing'; return 1;
  }
  # An existing camera mod can change properties/libs even with matching configs.
  for OP15_OTHER in /data/adb/modules/* /data/adb/modules_update/*; do
    [ -d "$OP15_OTHER" ] || continue
    [ "${OP15_OTHER##*/}" = op15_camera_enhance ] && continue
    [ -f "$OP15_OTHER/disable" ] && continue
    case "${OP15_OTHER##*/}" in
      *ocvm*|*OCVM*|*CamMod*|*cammod*|*camera*|*Camera*)
        OP15_ERROR="Other camera module present: ${OP15_OTHER##*/}"; return 1 ;;
    esac
  done
  while IFS=' ' read -r OP15_EXPECTED OP15_PATH; do
    [ -n "$OP15_EXPECTED" ] || continue
    [ "$(op15_hash "$OP15_PATH")" = "$OP15_EXPECTED" ] || {
      OP15_ERROR="Stock mismatch: $OP15_PATH (different firmware or overlay)"; return 1;
    }
  done < "$OP15_DIR/stock.sha256"
  while IFS=' ' read -r OP15_EXPECTED OP15_REL; do
    [ -n "$OP15_EXPECTED" ] || continue
    [ "$(op15_hash "$OP15_DIR/payload/$OP15_REL")" = "$OP15_EXPECTED" ] || {
      OP15_ERROR="Payload mismatch: $OP15_REL"; return 1;
    }
  done < "$OP15_DIR/payload.sha256"
}
