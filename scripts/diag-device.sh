#!/bin/sh
# Print camera bring-up diagnostics. Run on the device as root:
#   sudo sh scripts/diag-device.sh > diag.txt
echo "== kernel"; uname -a
echo "== boot dtb"; grep -E "fdt" /boot/extlinux/extlinux.conf
echo "== modules"; lsmod | grep -E "s5kc505a|camss|cci|v4l2|videodev"
echo "== dmesg"; dmesg | grep -iE "s5kc505a|camss|cci|csiphy|csid|vfe|ispif|cam_front|-0037"
echo "== regulators"
for r in /sys/class/regulator/*; do
    n=$(cat "$r/name" 2>/dev/null)
    case "$n" in cam_front*) echo "$n state=$(cat "$r/state" 2>/dev/null) users=$(cat "$r/num_users" 2>/dev/null)";; esac
done
echo "== i2c"; ls -l /sys/bus/i2c/devices/ | grep -i 0037
echo "== media"; ls -l /dev/media* /dev/v4l-subdev* 2>&1
