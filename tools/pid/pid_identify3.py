#!/usr/bin/env python3
"""
SNIFF — identyfikacja FOPDT metodą najmniejszych kwadratów na sygnale DROGI.

Dlaczego inaczej niż pid_identify2.py: różniczkowanie licznika o kwancie 1 cm
wzmacnia kwantyzację i zabija sygnał. Uśrednianie przebiegów nie pomaga, bo
kwantyzacja jest deterministyczna (identyczne przebiegi -> identyczny schodek).
Tu dopasowujemy model do surowego licznika, bez różniczkowania.

Model drogi dla skoku PWM w chwili t_s, z opóźnieniem theta i stałą tau:
    s(t) = A + v0*t                                   dla t < t_s + theta
    s(t) = A + v0*t + dv*[ (t-t_s-theta) - tau*(1 - exp(-(t-t_s-theta)/tau)) ]

Model jest LINIOWY względem A, v0, dv przy ustalonych (theta, tau), więc:
  - przeszukujemy siatkę (theta, tau),
  - dla każdego węzła rozwiązujemy liniowy problem najmniejszych kwadratów,
  - wybieramy węzeł o najmniejszym błędzie.
Nie wymaga scipy.

Użycie:
    python3 pid_identify3.py ident_*.csv
    python3 pid_identify3.py ident_*.csv --kolo R --jednostka 0.00972
    python3 pid_identify3.py ident_*.csv --plot dopasowanie.png
"""
import argparse
import csv
import sys

import numpy as np


def wczytaj(path, kolumna):
    t, cmd, od = [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            if kolumna not in row:
                return None
            try:
                t.append(float(row["t"]))
                cmd.append(float(row["cmd"]))
                od.append(float(row[kolumna]))
            except (ValueError, TypeError):
                continue
    return np.array(t), np.array(cmd), np.array(od)


def dopasuj(t, s, t_step, theta_grid, tau_grid):
    """Zwraca (theta, tau, v0, dv, sse, model)."""
    best = None
    for theta in theta_grid:
        tp = t - t_step - theta
        aktywne = tp > 0
        for tau in tau_grid:
            g = np.zeros_like(t)
            x = tp[aktywne]
            g[aktywne] = x - tau * (1.0 - np.exp(-x / tau))
            # macierz bazy: [1, t, g]
            M = np.column_stack([np.ones_like(t), t, g])
            wsp, *_ = np.linalg.lstsq(M, s, rcond=None)
            resid = s - M @ wsp
            sse = float(resid @ resid)
            if best is None or sse < best[0]:
                best = (sse, theta, tau, wsp, M @ wsp)
    sse, theta, tau, wsp, model = best
    A, v0, dv = wsp
    return theta, tau, v0, dv, sse, model


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pliki", nargs="+")
    ap.add_argument("--kolo", choices=["L", "R"], default="L")
    ap.add_argument("--jednostka", type=float, default=0.01005,
                    help="metry na jednostkę licznika (domyślnie 0.01005 dla L)")
    ap.add_argument("--plot", help="zapisz wykres dopasowania do PNG")
    args = ap.parse_args()

    kolumna = "odl" if args.kolo == "L" else "odr"

    # siatka przeszukiwania
    theta_grid = np.arange(0.0, 0.301, 0.005)
    tau_grid = np.concatenate([np.arange(0.02, 0.50, 0.005),
                               np.arange(0.50, 1.51, 0.02)])

    wyniki = []
    do_wykresu = None

    for path in args.pliki:
        dane = wczytaj(path, kolumna)
        if dane is None:
            print(f"[!] {path}: brak kolumny '{kolumna}'. Czy to nowy format CSV?")
            return 1
        t, cmd, od = dane
        if len(t) < 30:
            print(f"[!] {path}: za mało próbek.")
            continue

        skok = np.flatnonzero(np.diff(cmd) != 0)
        if len(skok) == 0:
            print(f"[!] {path}: brak skoku w kolumnie cmd.")
            continue
        i_s = skok[0] + 1
        t_step = t[i_s]
        du = cmd[i_s] - cmd[i_s - 1]

        # analizujemy tylko fazę przed i po pierwszym skoku (bez rampy hamowania)
        koniec = t[-1]
        drugi = skok[1] + 1 if len(skok) > 1 else None
        if drugi is not None:
            koniec = t[drugi]
        maska = t <= koniec
        tm, sm = t[maska], od[maska] * args.jednostka
        sm = sm - sm[0]

        theta, tau, v0, dv, sse, model = dopasuj(tm, sm, t_step,
                                                 theta_grid, tau_grid)
        k = dv / du
        rms = float(np.sqrt(sse / len(tm)))
        wyniki.append((path, k, tau, theta, v0, v0 + dv, rms))
        if do_wykresu is None:
            do_wykresu = (tm, sm, model, path, t_step)

    if not wyniki:
        print("[!] Brak wyników.")
        return 1

    print(f"== Identyfikacja FOPDT z sygnału drogi, koło {args.kolo} ==")
    print(f"  jednostka licznika: {args.jednostka:.5f} m")
    print(f"  metoda: najmniejsze kwadraty na drodze (bez różniczkowania)\n")
    print(f"  {'plik':<16}{'k [(m/s)/PWM]':>15}{'tau [s]':>10}{'theta [s]':>11}"
          f"{'v0 [m/s]':>10}{'v1 [m/s]':>10}{'RMS [mm]':>10}")
    for p, k, tau, th, v0, v1, rms in wyniki:
        print(f"  {p[:15]:<16}{k:>15.6f}{tau:>10.3f}{th:>11.3f}"
              f"{v0:>10.3f}{v1:>10.3f}{rms*1000:>10.2f}")

    arr = np.array([[w[1], w[2], w[3]] for w in wyniki])
    sr = arr.mean(axis=0)
    sd = arr.std(axis=0, ddof=1) if len(arr) > 1 else np.zeros(3)
    print(f"\n  {'ŚREDNIA':<16}{sr[0]:>15.6f}{sr[1]:>10.3f}{sr[2]:>11.3f}")
    if len(arr) > 1:
        print(f"  {'odch. std':<16}{sd[0]:>15.6f}{sd[1]:>10.3f}{sd[2]:>11.3f}")
        for i, nazwa in enumerate(["k", "tau", "theta"]):
            if sr[i] != 0:
                print(f"    rozrzut {nazwa:<6}: {100*sd[i]/abs(sr[i]):.1f} %")

    k, tau, theta = sr
    print(f"\n  Model: G(s) = {k:.6f} * exp(-{theta:.3f}s) / ({tau:.3f}s + 1)")
    print(f"  Stosunek theta/tau = {theta/tau:.2f}" if tau > 0 else "")

    print("\n== Nastawy SIMC (PI) ==")
    for nazwa, tc in (("tau_c = theta  (agresywne)", theta),
                      ("tau_c = 3*theta (łagodne)", 3 * theta)):
        if k == 0 or (tc + theta) == 0:
            continue
        Kc = tau / (k * (tc + theta))
        Ti = min(tau, 4.0 * (tc + theta))
        print(f"  {nazwa}:")
        print(f"    Kc = {Kc:.1f}   Ti = {Ti:.3f} s")
        print(f"    P = {Kc:.1f}   I = {Kc/Ti:.1f}")
        print('    {"T":2,"P":%.1f,"I":%.1f,"D":0,"L":255}' % (Kc, Kc / Ti))

    if args.plot and do_wykresu:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        tm, sm, model, nazwa, t_step = do_wykresu
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True,
                                     gridspec_kw={"height_ratios": [3, 1]})
        a1.plot(tm, sm, ".", ms=3, alpha=0.5, label="pomiar (licznik drogi)")
        a1.plot(tm, model, "r-", lw=2, label="model FOPDT (dopasowany)")
        a1.axvline(t_step, color="gray", ls=":", label="skok PWM")
        a1.set_ylabel("droga [m]"); a1.legend(); a1.grid(alpha=0.3)
        a1.set_title(f"Dopasowanie modelu do drogi — {nazwa}, koło {args.kolo}")
        a2.plot(tm, (sm - model) * 1000, "k-", lw=0.8)
        a2.axhline(0, color="gray", lw=0.5)
        a2.set_xlabel("t [s]"); a2.set_ylabel("reszta [mm]"); a2.grid(alpha=0.3)
        fig.tight_layout(); fig.savefig(args.plot, dpi=150)
        print(f"\n[OK] wykres -> {args.plot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
