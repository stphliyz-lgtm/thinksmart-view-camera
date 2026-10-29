#!/usr/bin/env python3
"""Turn a MIPI-packed RAW10 capture from the S5KC505A into PNGs.

Usage: raw2png.py capture.raw WIDTH HEIGHT OUT_PREFIX [frame_index]

Writes OUT_PREFIX-<order>.png for each Bayer order (simple 2x2 debayer,
gray-world white balance, gamma 2.2) and prints per-site channel means, so
the correct order can be picked by eye and by numbers.
"""
import sys

import numpy as np
from PIL import Image


def unpack(buf, w, h):
    stride = len(buf) // h
    rows = np.frombuffer(buf[: stride * h], np.uint8).reshape(h, stride)
    groups = rows[:, : w * 5 // 4].reshape(h, -1, 5).astype(np.uint16)
    out = np.empty((h, groups.shape[1], 4), np.uint16)
    for i in range(4):
        out[:, :, i] = (groups[:, :, i] << 2) | ((groups[:, :, 4] >> (2 * i)) & 3)
    return out.reshape(h, -1)[:, :w]


def debayer(raw, order):
    sites = {"RGGB": "RGGB", "GRBG": "GRBG", "GBRG": "GBRG", "BGGR": "BGGR"}[order]
    planes = {
        (0, 0): raw[0::2, 0::2], (0, 1): raw[0::2, 1::2],
        (1, 0): raw[1::2, 0::2], (1, 1): raw[1::2, 1::2],
    }
    pos = [(0, 0), (0, 1), (1, 0), (1, 1)]
    r = planes[pos[sites.index("R")]].astype(np.float32)
    b = planes[pos[sites.index("B")]].astype(np.float32)
    gs = [planes[p] for p, c in zip(pos, sites) if c == "G"]
    g = (gs[0].astype(np.float32) + gs[1]) / 2
    rgb = np.stack([r, g, b], -1) - 64.0  # black level guess
    rgb = np.clip(rgb, 0, None)
    rgb *= rgb[..., 1].mean() / np.maximum(rgb.reshape(-1, 3).mean(0), 1e-3)
    rgb = rgb / max(np.percentile(rgb, 99.5), 1.0)
    return (np.clip(rgb, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)


def main():
    path, w, h, prefix = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    idx = int(sys.argv[5]) if len(sys.argv) > 5 else -1
    data = open(path, "rb").read()
    stride = -(-(w * 5 // 4) // 8) * 8
    for s in (stride, ((w * 5 // 4 + 63) // 64) * 64, w * 5 // 4):
        if len(data) % (s * h) == 0:
            stride = s
            break
    frame_size = stride * h
    n = len(data) // frame_size
    frame = data[(idx % n) * frame_size:(idx % n + 1) * frame_size]
    raw = unpack(frame, w, h)
    print(f"frames={n} stride={stride} min={raw.min()} max={raw.max()} mean={raw.mean():.1f}")
    for name, sl in (("(0,0)", raw[0::2, 0::2]), ("(0,1)", raw[0::2, 1::2]),
                     ("(1,0)", raw[1::2, 0::2]), ("(1,1)", raw[1::2, 1::2])):
        print(f"site {name} mean={sl.mean():.1f}")
    for order in ("RGGB", "GRBG", "GBRG", "BGGR"):
        Image.fromarray(debayer(raw, order)).save(f"{prefix}-{order}.png")


if __name__ == "__main__":
    main()
