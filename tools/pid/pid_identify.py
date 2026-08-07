#!/usr/bin/env python3
"""
SNIFF — identyfikacja FOPDT z odpowiedzi skokowej + nastawy SIMC.

Wejście: CSV z pid_step_test.py (tryb --mode pwm zalecany do identyfikacji).
Model:   G(s) = k * exp(-theta*s) / (tau*s + 1)
Metoda:  dwóch punktów (t28.3%, t63.2%):  tau = 1.5*(t63 - t28),  theta = t63 - tau
SIMC PI: Kc = tau / (k*(tauc+theta)),  Ti = min(tau, 4*(tauc+theta))
Firmware (PID_v2, forma równoległa): P = Kc, I = Kc/Ti, D = 0.

Użycie: python3 pid_identify.py ident.csv [--wheel L|R] [--plot ident.png]
"""
import argparse
import csv
import sys

import numpy as np


def load(path):
    t, cmd, vl, vr = [], [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                t.append(float(row["t"]))
                cmd.append(float(row["cmd"]))
                vl.append(float(row["vL"]))
                vr.append(float(row["vR"]))
            except (ValueError, TypeError):
                continue
    return (np.array(t), np.array(cmd), np.array(vl), np.array(vr))


def first_crossing(t, y, level, t_from):
    m = t >= t_from
    ti, yi = t[m], y[m]
    idx = np.argmax(yi >= level) if np.any(yi >= level) else None
    if idx is None or idx == 0:
        return None
    # interpolacja liniowa między próbkami
    t0, t1 = ti[idx - 1], ti[idx]
    y0, y1 = yi[idx - 1], yi[idx]
    return t0 + (level - y0) * (t1 - t0) / max(y1 - y0, 1e-12)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv")
    ap.add_argument("--wheel", choices=["L", "R"], default="L")
    ap.add_argument("--plot", help="zapisz wykres do PNG")
    args = ap.parse_args()

    t, cmd, vl, vr = load(args.csv)
    if len(t) < 20:
        print("[!] Za mało próbek.")
        return 1
    y_raw = vl if args.wheel == "L" else vr

    # lekka filtracja (mediana z 5) — enkodery szumią
    y = np.copy(y_raw)
    for i in range(2, len(y) - 2):
        y[i] = np.median(y_raw[i - 2:i + 3])

    # moment skoku = zmiana kolumny cmd
    dcmd = np.flatnonzero(np.diff(cmd) != 0)
    if len(dcmd) == 0:
        print("[!] Brak skoku w kolumnie cmd.")
        return 1
    i_step = dcmd[0] + 1
    t_step = t[i_step]
    u0, u1 = cmd[i_step - 1], cmd[i_step]
    du = u1 - u0

    y0 = float(np.mean(y[t < t_step][max(0, i_step - 20):i_step]))
    tail = y[t > t[-1] - 0.25 * (t[-1] - t_step)]
    y1 = float(np.mean(tail))
    dy = y1 - y0
    if abs(du) < 1e-9 or abs(dy) < 1e-9:
        print("[!] Zerowy skok wejścia lub brak reakcji wyjścia.")
        return 1

    k = dy / du
    sgn = np.sign(dy)
    t28 = first_crossing(t, sgn * (y - y0), sgn * dy * 0.283, t_step)
    t63 = first_crossing(t, sgn * (y - y0), sgn * dy * 0.632, t_step)
    if t28 is None or t63 is None or t63 <= t28:
        print("[!] Nie udało się wyznaczyć t28/t63 — obejrzyj dane (--plot).")
        return 1

    tau = 1.5 * (t63 - t28)
    theta = max((t63 - t_step) - tau, 0.005)  # nie mniej niż 5 ms

    print(f"== Identyfikacja FOPDT (koło {args.wheel}) ==")
    print(f"  skok wejścia : {u0:g} -> {u1:g}   (du = {du:g})")
    print(f"  wyjście      : {y0:.4f} -> {y1:.4f} m/s   (dy = {dy:.4f})")
    print(f"  k     = {k:.6f}  [ (m/s) / jedn. wejścia ]")
    print(f"  tau   = {tau:.3f} s")
    print(f"  theta = {theta:.3f} s")
    print()
    print("== Nastawy SIMC (PI) -> forma firmware {'T':2,...} ==")
    for name, tauc in (("tauc = theta (agresywne)", theta),
                       ("tauc = 1.5*theta (łagodne)", 1.5 * theta)):
        kc = tau / (k * (tauc + theta))
        ti = min(tau, 4.0 * (tauc + theta))
        P, I = kc, kc / ti
        print(f"  {name}:")
        print(f"    Kc = {kc:.1f}, Ti = {ti:.3f} s")
        print('    {"T":2,"P":%.1f,"I":%.1f,"D":0,"L":255}' % (P, I))
    print("\n[i] Nastawy fabryczne dla porównania: "
          '{"T":2,"P":20,"I":2000,"D":0,"L":255}')

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        tm = np.linspace(t[0], t[-1], 800)
        ym = np.where(tm < t_step + theta, y0,
                      y0 + dy * (1 - np.exp(-(tm - t_step - theta) / tau)))
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(t, y_raw, ".", ms=3, alpha=0.4, label="pomiar (raw)")
        ax.plot(t, y, "-", lw=1, label="pomiar (mediana 5)")
        ax.plot(tm, ym, "r--", lw=2,
                label=f"FOPDT: k={k:.4g}, tau={tau:.3f}s, th={theta:.3f}s")
        ax.axvline(t_step, color="gray", ls=":", label="skok wejścia")
        ax.set_xlabel("t [s]"); ax.set_ylabel("v [m/s]")
        ax.legend(); ax.grid(alpha=0.3)
        ax.set_title(f"Identyfikacja koła {args.wheel} — {args.csv}")
        fig.tight_layout(); fig.savefig(args.plot, dpi=150)
        print(f"[OK] wykres -> {args.plot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
