#!/usr/bin/env python3
"""
SNIFF — identyfikacja FOPDT z odpowiedzi skokowej. Wersja odporna na kwantyzację.

Dlaczego nie pid_identify.py: pole L/R w ramce T:1001 jest skwantowane co
0.381 m/s (jeden impuls enkodera na cykl pętli firmware). Przy skoku dającym
zmianę rzędu 0.4 m/s cała odpowiedź mieści się w jednym kwancie i metoda dwóch
punktów nie ma czego szukać. Ten skrypt bierze licznik odometrii odl/odr,
czyli scałkowaną drogę, i różniczkuje go po oknie symetrycznym. Kwantyzacja
uśrednia się w drodze, rozdzielczość rośnie o dwa rzędy wielkości.

Model:  G(s) = k * exp(-theta*s) / (tau*s + 1)
Metoda: dwóch punktów, t_28 = theta + tau/3 oraz t_63 = theta + tau, stąd
        tau = 1.5 * (t_63 - t_28),  theta = t_63 - tau,  k = dy / du
SIMC:   K_c = tau / (k * (tau_c + theta)),  T_i = min(tau, 4 * (tau_c + theta))
Firmware (forma równoległa): P = K_c, I = K_c / T_i, D = 0

Użycie:
    python3 pid_identify2.py ident_1.csv ident_2.csv ident_3.csv --plot ident.png
    python3 pid_identify2.py ident_1.csv --wheel R --okno 0.12
"""
import argparse
import csv
import sys

import numpy as np

LEVEL_28 = 1.0 - np.exp(-1.0 / 3.0)   # 0.2835
LEVEL_63 = 1.0 - np.exp(-1.0)         # 0.6321
DROGA_NA_IMPULS = 3.81e-4             # pi * 0.080 / 660 [m]


def wczytaj(path, wheel):
    kol_v = "vL" if wheel == "L" else "vR"
    kol_o = "odl" if wheel == "L" else "odr"
    t, cmd, v, o = [], [], [], []
    with open(path) as f:
        czytnik = csv.DictReader(f)
        if kol_o not in (czytnik.fieldnames or []):
            raise ValueError(f"{path}: brak kolumny {kol_o}. Zbierz dane nowym "
                             f"pid_step_test.py.")
        for row in czytnik:
            try:
                t.append(float(row["t"]))
                cmd.append(float(row["cmd"]))
                v.append(float(row[kol_v]))
                o.append(float(row[kol_o]))
            except (ValueError, TypeError):
                continue
    return np.array(t), np.array(cmd), np.array(v), np.array(o)


def skala_licznika(t, v, o):
    """Ile metrów przypada na jednostkę licznika. Kalibracja przez porównanie
    z całką prędkości, która jako całka jest wiarygodna mimo kwantyzacji."""
    d_o = o[-1] - o[0]
    if abs(d_o) < 1e-9:
        raise ValueError("licznik odometrii nie drgnął")
    dt = np.diff(t, prepend=t[0])
    d_s = float(np.sum(v * dt))
    return d_s / d_o


def predkosc(t, s, okno):
    """Pochodna po oknie symetrycznym. Filtr o zerowym przesunięciu fazowym,
    więc nie zafałszowuje mierzonego opóźnienia theta."""
    out = np.full_like(s, np.nan)
    for i in range(len(t)):
        a = np.searchsorted(t, t[i] - okno / 2.0)
        b = np.searchsorted(t, t[i] + okno / 2.0) - 1
        if b > a:
            out[i] = (s[b] - s[a]) / (t[b] - t[a])
    ok = np.isfinite(out)
    return np.interp(t, t[ok], out[ok])


def przygotuj(path, wheel, okno):
    t, cmd, v, o = wczytaj(path, wheel)
    if len(t) < 20:
        raise ValueError(f"{path}: za mało próbek")
    d = np.flatnonzero(np.diff(cmd) != 0)
    if len(d) == 0:
        raise ValueError(f"{path}: brak skoku w kolumnie cmd")
    i_step = d[0] + 1
    t_step = t[i_step]
    du = cmd[i_step] - cmd[i_step - 1]
    skala = skala_licznika(t, v, o)
    s = (o - o[0]) * skala
    y = predkosc(t, s, okno)
    return dict(t=t - t_step, y=y, y_raw=v, du=du, skala=skala, path=path)


def usrednij(przebiegi, krok=0.02):
    t_min = max(p["t"][0] for p in przebiegi)
    t_max = min(p["t"][-1] for p in przebiegi)
    siatka = np.arange(t_min, t_max, krok)
    stos = np.vstack([np.interp(siatka, p["t"], p["y"]) for p in przebiegi])
    return siatka, stos.mean(axis=0), stos


def przejscie(tt, yn, poziom):
    """Pierwsze przekroczenie poziomu, które się utrzymuje. Interpolacja liniowa."""
    idx = np.flatnonzero((yn[:-1] < poziom) & (yn[1:] >= poziom))
    for i in idx:
        if float(np.mean(yn[i + 1:])) > poziom:
            t0, t1 = tt[i], tt[i + 1]
            y0, y1 = yn[i], yn[i + 1]
            return t0 + (poziom - y0) * (t1 - t0) / max(y1 - y0, 1e-12)
    return None


def dopasuj_lsq(tt, y, y0, dy, tau0, theta0):
    """Kontrolne dopasowanie całej krzywej, przeszukiwanie siatki."""
    m = tt >= 0
    ttp, yp = tt[m], y[m]
    naj = (np.inf, tau0, theta0)
    for tau in np.linspace(0.02, max(1.5, 3.0 * tau0), 150):
        for theta in np.linspace(0.0, max(0.3, 2.0 * theta0), 60):
            mod = np.where(ttp < theta, y0,
                           y0 + dy * (1 - np.exp(-(ttp - theta) / tau)))
            err = float(np.sum((yp - mod) ** 2))
            if err < naj[0]:
                naj = (err, tau, theta)
    return naj[1], naj[2]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csvs", nargs="+", help="przebiegi tego samego skoku")
    ap.add_argument("--wheel", choices=["L", "R"], default="L")
    ap.add_argument("--okno", type=float, default=0.12,
                    help="okno różniczkowania drogi [s], domyślnie 0.12")
    ap.add_argument("--plot", help="zapisz wykres do PNG")
    args = ap.parse_args()

    przebiegi = []
    for p in args.csvs:
        try:
            przebiegi.append(przygotuj(p, args.wheel, args.okno))
        except ValueError as e:
            print(f"[!] {e}")
    if not przebiegi:
        return 1

    du = przebiegi[0]["du"]
    if any(abs(p["du"] - du) > 1e-9 for p in przebiegi):
        print("[!] Przebiegi mają różne skoki wejścia, nie uśredniam.")
        return 1

    skala = float(np.mean([p["skala"] for p in przebiegi]))
    jednostka = ("impulsy" if abs(skala - DROGA_NA_IMPULS) < 0.3 * DROGA_NA_IMPULS
                 else "metry" if abs(skala - 1.0) < 0.3 else "nieznana")

    tt, y, stos = usrednij(przebiegi)

    print(f"== Identyfikacja FOPDT, koło {args.wheel} ==")
    print(f"  przebiegi      : {len(przebiegi)}  ({', '.join(p['path'] for p in przebiegi)})")
    print(f"  licznik odometrii: 1 jednostka = {skala:.3e} m  ({jednostka})")
    print(f"  okno różniczkowania: {args.okno:.2f} s")

    przed = tt < -args.okno
    ogon = tt > 0.7 * tt[-1]
    if przed.sum() < 5 or ogon.sum() < 5:
        print("[!] Za krótkie fazy przed lub po skoku.")
        return 1
    y0 = float(np.mean(y[przed]))
    y1 = float(np.mean(y[ogon]))
    dy = y1 - y0
    if abs(dy) < 1e-6:
        print("[!] Brak reakcji wyjścia.")
        return 1
    k = dy / du

    print(f"  skok wejścia   : {du:g} PWM")
    print(f"  wyjście        : {y0:.4f} -> {y1:.4f} m/s   (dy = {dy:.4f})")
    if len(przebiegi) > 1:
        koncowe = stos[:, ogon].mean(axis=1)
        print(f"  wartość ustalona per przebieg: "
              f"{', '.join(f'{x:.3f}' for x in koncowe)}  "
              f"(odch. std {np.std(koncowe):.4f} m/s)")

    yn = (y - y0) / dy
    szum = float(np.std(yn[przed]))
    ocena = "OK" if szum < 0.08 else "ZA DUZY, zwieksz skok albo liczbe powtorzen"
    print(f"  szum przed skokiem: +-{szum*100:.0f}% zmiany  ({ocena})")

    po = tt >= 0.0
    t28 = przejscie(tt[po], yn[po], LEVEL_28)
    t63 = przejscie(tt[po], yn[po], LEVEL_63)
    if t28 is None or t63 is None or t63 <= t28:
        print("[!] Nie da się wyznaczyć t_28 albo t_63. Obejrzyj wykres.")
        return 1

    tau = 1.5 * (t63 - t28)
    theta = max(t63 - tau, 0.005)
    tau_l, theta_l = dopasuj_lsq(tt, y, y0, dy, tau, theta)

    print(f"\n  t_28 = {t28:.3f} s, t_63 = {t63:.3f} s   (od chwili skoku)")
    print(f"    k     = {k:.6f}  [(m/s)/PWM]")
    print(f"    tau   = {tau:.3f} s")
    print(f"    theta = {theta:.3f} s      theta/tau = {theta/tau:.2f}")
    print(f"  kontrola LSQ (dopasowanie całej krzywej):"
          f"  tau = {tau_l:.3f} s, theta = {theta_l:.3f} s")
    if abs(tau_l - tau) > 0.5 * tau:
        print("    [!] Rozbieżność ponad 50%. Metoda dwóch punktów jest wrażliwa "
              "na szum, obejrzyj wykres przed użyciem tych liczb.")

    print("\n== Nastawy SIMC (PI) ==")
    for nazwa, tauc in (("tau_c = theta      (agresywny)", theta),
                        ("tau_c = 3 * theta  (łagodny)", 3.0 * theta)):
        kc = tau / (k * (tauc + theta))
        ti = min(tau, 4.0 * (tauc + theta))
        print(f"  {nazwa}:  K_c = {kc:.1f}, T_i = {ti:.3f} s")
        print('    {"T":2,"P":%.1f,"I":%.1f,"D":0,"L":255}' % (kc, kc / ti))
    print('\n[i] Fabryczne dla odniesienia: {"T":2,"P":20,"I":2000,"D":0,"L":255}'
          '   (T_i = 0.01 s)')

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        mod = np.where(tt < theta, y0, y0 + dy * (1 - np.exp(-(tt - theta) / tau)))
        fig, ax = plt.subplots(figsize=(9, 5))
        for p in przebiegi:
            ax.plot(p["t"], p["y_raw"], ".", ms=2, alpha=0.2, color="gray")
        for i in range(stos.shape[0]):
            ax.plot(tt, stos[i], lw=0.8, alpha=0.45)
        ax.plot(tt, y, "b-", lw=2,
                label=f"z odometrii, średnia z {len(przebiegi)}")
        ax.plot(tt, mod, "r--", lw=2,
                label=f"FOPDT k={k:.4g} tau={tau:.3f}s theta={theta:.3f}s")
        for lvl, opis, tc in ((LEVEL_28, "28.3%", t28), (LEVEL_63, "63.2%", t63)):
            ax.axhline(y0 + lvl * dy, color="green", ls=":", lw=0.8)
            ax.axvline(tc, color="green", ls=":", lw=0.8)
            ax.annotate(opis, (tc, y0 + lvl * dy), fontsize=8, color="green")
        ax.axvline(0, color="k", ls=":", lw=1, label="skok wejścia")
        ax.set_xlabel("t od skoku [s]")
        ax.set_ylabel("v [m/s]")
        ax.set_title(f"Identyfikacja koła {args.wheel}, skok {du:g} PWM "
                     f"(szare kropki: surowe vL, kwant 0.381 m/s)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(args.plot, dpi=150)
        print(f"[OK] wykres -> {args.plot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
