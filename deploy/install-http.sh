#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root." >&2
  exit 2
fi
if [[ $# -ne 0 ]]; then
  echo "Usage: $0" >&2
  exit 2
fi

source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
unit=/etc/systemd/system/harmonize-http.service
installed_tool=/opt/harmonize/app/tools/harmonize_http.py
installed_doc=/opt/harmonize/app/docs/milestone-8-http.md

[[ -f /etc/systemd/system/harmonize.service ]] || {
  echo "harmonize.service is not installed." >&2
  exit 2
}
[[ -f /opt/harmonize/app/harmonize_core/local_control.py ]] || {
  echo "The installed Harmonize local-control client was not found." >&2
  exit 2
}
[[ ! -e "$unit" ]] || {
  echo "Refusing to replace existing path: $unit" >&2
  exit 2
}
[[ ! -e "$installed_tool" ]] || {
  echo "Refusing to replace existing path: $installed_tool" >&2
  exit 2
}
[[ ! -e "$installed_doc" ]] || {
  echo "Refusing to replace existing path: $installed_doc" >&2
  exit 2
}
account=$(getent passwd harmonize || true)
[[ "$account" == harmonize:*:/var/lib/harmonize:/usr/sbin/nologin ]] || {
  echo "Refusing to use an unrecognized harmonize account." >&2
  exit 2
}

install -o root -g root -m 0755 \
  "$source_root/tools/harmonize_http.py" "$installed_tool"
install -o root -g root -m 0644 \
  "$source_root/docs/milestone-8-http.md" "$installed_doc"
install -o root -g root -m 0644 \
  "$source_root/deploy/harmonize-http.service" "$unit"
systemctl daemon-reload
systemctl enable --now harmonize-http.service
