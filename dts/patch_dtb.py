#!/usr/bin/env python3
"""Add the front camera to the stock CD-18781Y DTB.

Usage: python3 -I patch_dtb.py stock.dts camera-s5kc505a.dtsi > camera.dts
Then:  dtc -I dts -O dtb -o camera.dtb camera.dts

stock.dts is `dtc -I dtb -O dts` of /boot/apq8053-lenovo-cd-18781y.dtb.
The decompiled tree has no labels, so this adds the few the snippet needs.
Each node name below must appear exactly once.
"""
import re
import sys

LABELS = {
    "clock-controller@1800000": "gcc",
    "pinctrl@1000000": "tlmm",
    "camss@1b00020": "camss",
    "cci@1b0c000": "cci",
    "camss-mclk0-default-state": "camss_mclk0_default",
    "s3": "pm8953_s3",
    "l2": "pm8953_l2",
    "l6": "pm8953_l6",
    "l17": "pm8953_l17",
}


def main():
    dts = open(sys.argv[1]).read()
    snippet = open(sys.argv[2]).read()

    for node, label in LABELS.items():
        pat = re.compile(r"^(\s*)" + re.escape(node) + r" \{$", re.M)
        hits = pat.findall(dts)
        if len(hits) != 1:
            raise SystemExit(f"{node}: expected 1 match, got {len(hits)}")
        dts = pat.sub(lambda m: f"{m.group(1)}{label}: {node} {{", dts)

    # CCI bus 0 is the first i2c-bus child of the cci node.
    start = dts.index("cci: cci@1b0c000 {")
    pos = dts.index("i2c-bus@0 {", start)
    dts = dts[:pos] + "cci_i2c0: " + dts[pos:]

    sys.stdout.write(dts.rstrip() + "\n\n" + snippet)


if __name__ == "__main__":
    main()
