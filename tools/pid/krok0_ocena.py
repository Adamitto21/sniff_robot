#!/usr/bin/env python3
"""
SNIFF — ocena wyniku KROK 0 oraz kalibracja jednostki licznika odl/odr.

Odpowiada na dwa pytania:
  1. Czy pętla prędkości jest zamknięta? Porównuje średnią prędkość przed
     podmianą nastaw na zerowe i po niej. Jeśli po podmianie prędkość spada,
     regulator działał. Jeśli nie drgnęła, sterowanie jest w otwartej pętli.
  2. Ile metrów przypada na jednostkę licznika odl/odr? Porównuje przyrost
     licznika ze scałkowaną prędkością.

    python3 krok0_ocena.py krok0.csv
    python3 krok0_ocena.py krok0.csv --podmiana 6.03
"""
import argparse
import csv
import sys

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", help="plik z pid_step_test.py --pid-mid")
    ap.add_argument("--podmiana", type=float, default=None,
                    help="chwila podmiany nastaw [s]. Domyślnie środek drugiej fazy, "
                         "czyli tak jak liczy to pid_step_test.py.")
    args = ap.parse_args()

    t, cmd, vl, vr, odl, odr = [], [], [], [], [], []
    with open(args.csv) as f:
        for row in csv.DictReader(f):
            try:
                t.append(float(row["t"]))
                cmd.append(float(row["cmd"]))
                vl.append(float(row["vL"]))
                vr.append(float(row["vR"]))
            except (ValueError, TypeError):
                continue
            odl.append(float(row.get("odl") or "nan"))
            odr.append(float(row.get("odr") or "nan"))
    t = np.array(t); cmd = np.array(cmd)
    vl = np.array(vl); vr = np.array(vr)
    odl = np.array(odl); odr = np.array(odr)
    if len(t) < 20:
        print("[!] Za mało próbek.")
        return 1

    d = np.flatnonzero(np.diff(cmd) != 0)
    if len(d) == 0:
        print("[!] Brak skoku w kolumnie cmd.")
        return 1
    t_step = t[d[0] + 1]
    t_mid = args.podmiana if args.podmiana is not None else (t_step + t[-1]) / 2.0

    print(f"== KROK 0, plik {args.csv} ==")
    print(f"  skok wartości zadanej w t = {t_step:.2f} s, na {cmd[-1]:g}")
    print(f"  podmiana nastaw na zerowe w t = {t_mid:.2f} s")

    # okna: ostatnia sekunda przed podmianą, ostatnia sekunda przed końcem
    przed = (t > t_mid - 1.0) & (t < t_mid - 0.05)
    po = t > t[-1] - 1.0
    if przed.sum() < 5 or po.sum() < 5:
        print("[!] Za krótkie okna. Wydłuż fazę po skoku.")
        return 1

    for nazwa, v in (("lewe", vl), ("prawe", vr)):
        a, b = float(np.mean(v[przed])), float(np.mean(v[po]))
        spadek = (a - b) / a * 100 if a > 1e-6 else 0.0
        print(f"  koło {nazwa}: {a:.3f} m/s przed podmianą -> {b:.3f} m/s po "
              f"({spadek:+.0f} %)")

    a = float(np.mean(vl[przed])); b = float(np.mean(vl[po]))
    spadek = (a - b) / a * 100 if a > 1e-6 else 0.0
    print("\n  WERDYKT:")
    if spadek > 40:
        print("    Pętla ZAMKNIĘTA. Zerowe nastawy odebrały napęd, czyli regulator")
        print("    faktycznie liczy sterowanie. Nastawy z Etapu 2 zadziałają.")
    elif spadek < 10:
        print("    Pętla OTWARTA. Podmiana nastaw nic nie zmieniła, więc firmware")
        print("    przelicza wartość zadaną wprost na PWM z pominięciem regulatora.")
        print("    Zanim zrobisz Etap 3, trzeba wgrać łatkę z sekcji 3 instrukcji")
        print("    PID_KOLA_INSTRUKCJA.md albo użyć pid_jetson_pi.py.")
    else:
        print(f"    Niejednoznacznie, spadek {spadek:.0f} %. Obejrzyj przebieg vL")
        print("    w czasie i powtórz test z dłuższą drugą fazą.")

    if np.isfinite(odl).all() and np.ptp(odl) > 0:
        dt = np.diff(t, prepend=t[0])
        droga_L = float(np.sum(vl * dt))
        droga_R = float(np.sum(vr * dt))
        skala_L = droga_L / (odl[-1] - odl[0])
        skala_R = droga_R / (odr[-1] - odr[0]) if odr[-1] != odr[0] else float("nan")
        print(f"\n  Kalibracja licznika odometrii:")
        print(f"    droga z całki prędkości: L {droga_L:.3f} m, R {droga_R:.3f} m")
        print(f"    przyrost licznika:       L {odl[-1]-odl[0]:.0f}, "
              f"R {odr[-1]-odr[0]:.0f}")
        print(f"    1 jednostka licznika =   L {skala_L:.4e} m, R {skala_R:.4e} m")
        if abs(skala_L - 3.81e-4) < 1e-4:
            print("    -> licznik zlicza impulsy enkodera (0.381 mm na impuls)")
        elif abs(skala_L - 0.01) < 0.003:
            print("    -> licznik jest w centymetrach")
        elif abs(skala_L - 0.001) < 0.0003:
            print("    -> licznik jest w milimetrach")
        elif abs(skala_L - 1.0) < 0.3:
            print("    -> licznik jest w metrach")
        else:
            print("    -> jednostka nietypowa, ale pid_identify2.py i tak kalibruje "
                  "ją sam przy każdym przebiegu")
    else:
        print("\n  [!] Brak użytecznych kolumn odl/odr w tym pliku.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
