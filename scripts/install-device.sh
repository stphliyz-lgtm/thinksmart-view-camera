#!/bin/sh
# Install the S5KC505A driver and the camera DTB on a ThinkSmart View
# running postmarketOS. Build both first (see README.md).
#
#   sudo sh scripts/install-device.sh           install
#   sudo sh scripts/install-device.sh --undo    restore the original boot config
#
# Expects driver/s5kc505a.ko and dts/apq8053-lenovo-cd-18781y-camera.dtb.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
kernel=$(uname -r)
backup=/root/thinksmart-camera-backup
dtb=apq8053-lenovo-cd-18781y-camera.dtb
conf=/boot/extlinux/extlinux.conf

mkdir -p "$backup"

if [ "${1:-}" = "--undo" ]; then
    cp -p "$backup/extlinux.conf.original" "$conf"
    rm -f "/boot/$dtb" "/usr/lib/modules/$kernel/extra/s5kc505a.ko"
    rm -f /etc/modules-load.d/thinksmart-camera.conf
    depmod -a "$kernel"
    sync
    echo "Camera removed. Reboot now."
    exit 0
fi

test -f "$here/driver/s5kc505a.ko"
test -f "$here/dts/$dtb"
modinfo -F vermagic "$here/driver/s5kc505a.ko" | grep -q "^$kernel " ||
    { echo "s5kc505a.ko was not built for $kernel"; exit 1; }

test -e "$backup/extlinux.conf.original" || cp -p "$conf" "$backup/extlinux.conf.original"

mkdir -p "/usr/lib/modules/$kernel/extra"
install -m 644 "$here/driver/s5kc505a.ko" "/usr/lib/modules/$kernel/extra/s5kc505a.ko"
install -m 644 "$here/dts/$dtb" "/boot/$dtb"
depmod -a "$kernel"

# Point the boot entry at the camera DTB; keep everything else unchanged.
sed "s|^\([[:space:]]*\)fdtdir /\$|\1fdt /$dtb|" "$backup/extlinux.conf.original" > "$conf.new"
grep -q "fdt /$dtb" "$conf.new"
mv "$conf.new" "$conf"

printf '%s\n' qcom_camss i2c_qcom_cci s5kc505a > /etc/modules-load.d/thinksmart-camera.conf
sync
echo "Camera installed. Reboot now."
