#!/usr/bin/env python3
"""
SNIFF — porównanie jakości regulacji dla kilku zestawów nastaw.

Wejście: >=1 plików CSV z pid_step_test.py (--mode speed) lub pid_jetson_pi.py.
Liczy od momentu skoku: IAE, ISE, przeregulowanie [%], czas narastania 10-90%,
czas ustalania (pasmo ±2% wartości zadanej).

Użycie:
  python3 pid_compare.py a.csv b.csv c.csv --labels fabryczne SIMC SIMC-1.5 --plot cmp.png
"""
import argparse
import csv
import sys

import numpy as np


def load(path, wheel):
    t, cmd, v = [], [], []
    col = "vL" if wheel == "L" else "vR"
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                t.append(float(row["t"]))
                cmd.append(float(row["cmd"]))
                v.append(float(row[col]))
            except (ValueError, TypeError):
                continue
    return np.array(t), np.array(cmd), np.array(v)


def metrics(t, sp, v_raw):
    # mediana z 5 — szum enkoderów zawyża czas ustalania
    v = np.copy(v_raw)
    for i in range(2, len(v) - 2):
        v[i] = np.median(v_raw[i - 2:i + 3])
    dstep = np.flatnonzero(np.diff(sp) != 0)
    if len(dstep) == 0:
        return None
    i0 = dstep[0] + 1
    t0 = t[i0]
    sp0, sp1 = sp[i0 - 1], sp[i0]
    dsp = sp1 - sp0
    m = t >= t0
    tt, vv, ss = t[m] - t0, v[m], sp[m]
    e = ss - vv
    dt = np.diff(tt, prepend=tt[0])
    iae = float(np.sum(np.abs(e) * dt))
    ise = float(np.sum(e**2 * dt))
    sgn = np.sign(dsp) if dsp != 0 else 1.0
    ovr = float(max(0.0, (sgn * (vv - sp1)).max()) / abs(dsp) * 100.0)

    yn = sgn * (vv - sp0) / abs(dsp)  # znormalizowane 0..1
    def cross(level):
        idx = np.argmax(yn >= level) if np.any(yn >= level) else None
        return float(tt[idx]) if idx not in (None, 0) else None
    t10, t90 = cross(0.10), cross(0.90)
    rise = (t90 - t10) if (t10 is not None and t90 is not None) else float("nan")

    band = 0.02 * abs(sp1) if sp1 != 0 else 0.02 * abs(dsp)
    inside = np.abs(vv - sp1) <= band
    settle = float("nan")
    for i in range(len(inside)):
        if inside[i:].all():
            settle = float(tt[i]); break
    return dict(t0=t0, sp1=sp1, iae=iae, ise=ise, overshoot=ovr,
                rise=rise, settle=settle, tt=tt, vv=vv, ss=ss)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csvs", nargs="+")
    ap.add_argument("--labels", nargs="*", default=None)
    ap.add_argument("--wheel", choices=["L", "R"], default="L")
    ap.add_argument("--plot", help="zapisz wspólny wykres do PNG")
    args = ap.parse_args()

    labels = args.labels or [f"run{i+1}" for i in range(len(args.csvs))]
    if len(labels) != len(args.csvs):
        print("[!] Liczba --labels != liczba plików."); return 1

    results = []
    for path, lab in zip(args.csvs, labels):
        t, sp, v = load(path, args.wheel)
        r = metrics(t, sp, v)
        if r is None:
            print(f"[!] {path}: brak skoku w cmd — pomijam."); continue
        results.append((lab, r))

    print(f"{'nastawy':<14}{'IAE':>10}{'ISE':>10}{'przereg.%':>11}"
          f"{'t_nar 10-90':>13}{'t_ust 2%':>10}")
    for lab, r in results:
        print(f"{lab:<14}{r['iae']:>10.4f}{r['ise']:>10.5f}{r['overshoot']:>11.1f}"
              f"{r['rise']:>13.3f}{r['settle']:>10.3f}")

    if args.plot and results:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 5))
        lab0, r0 = results[0]
        ax.step(r0["tt"], r0["ss"], "k--", lw=1.5, where="post",
                label="wartość zadana")
        for lab, r in results:
            ax.plot(r["tt"], r["vv"], lw=1.4,
                    label=f"{lab} (IAE={r['iae']:.3f})")
        ax.set_xlabel("t od skoku [s]"); ax.set_ylabel("v [m/s]")
        ax.grid(alpha=0.3); ax.legend()
        ax.set_title(f"Odpowiedź skokowa pętli prędkości — koło {args.wheel}")
        fig.tight_layout(); fig.savefig(args.plot, dpi=150)
        print(f"[OK] wykres -> {args.plot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
