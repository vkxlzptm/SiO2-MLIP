#!/usr/bin/env python3
"""
S4 — quench 프로파일에서 Tg 두 가지를 뽑는다.

  (1) caloric Tg : epa(T)의 액체 가지 / 유리 가지 선형 fit 교점
  (2) kinetic arrest : 구간당 ΔMSD가 잡음 수준 아래로 떨어지는 온도

7net 본런과 BKS 통제런 3종을 같은 방식으로 처리해 한 표로 낸다.
프로파일 형식: T_set(K)  epa(eV/atom)  Press(bar)  MSD(A^2)   (MSD는 누적값)
프로파일 파일은 profiles/ 하위에 있다 (정리 후 구조).

실행: python3 analyze_tg.py   (s4_mq7net/ 최상위에서)
"""
import glob, os
import numpy as np

LIQ_SPAN  = 1000.0   # 최고온에서 아래로 이 폭만큼을 '액체 가지'로 fit
GLA_SPAN  = 1200.0   # 최저온에서 위로 이 폭만큼을 '유리 가지'로 fit
DMSD_NOISE = 0.30    # Å^2 / 구간. 이 아래면 확산 정지로 본다
PROFILE_DIR = "profiles" if os.path.isdir("profiles") else "."


def load(path):
    d = np.loadtxt(path)
    d = d[np.argsort(-d[:, 0])]          # 고온 -> 저온
    return d[:, 0], d[:, 1], d[:, 2], d[:, 3]


def fit_branch(T, y, lo, hi):
    m = (T >= lo) & (T <= hi)
    if m.sum() < 3:
        return None, None, 0
    s, a = np.polyfit(T[m], y[m], 1)     # y = s*T + a
    return s, a, m.sum()


def caloric_tg(T, epa):
    Tmax, Tmin = T.max(), T.min()
    sL, aL, nL = fit_branch(T, epa, Tmax - LIQ_SPAN, Tmax)
    sG, aG, nG = fit_branch(T, epa, Tmin, Tmin + GLA_SPAN)
    if sL is None or sG is None or abs(sL - sG) < 1e-9:
        return None, None, None, None, None
    tg = (aG - aL) / (sL - sG)
    return tg, sL, sG, nL, nG


def kinetic_arrest(T, msd):
    d = np.abs(np.diff(msd))
    Tmid = T[1:]
    arrest = None
    for i in range(len(d)):
        if np.all(d[i:] < DMSD_NOISE):   # 이 지점 이후 계속 잡음 수준
            arrest = Tmid[i]
            break
    return arrest, Tmid, d


def report(tag, path):
    T, epa, P, msd = load(path)
    tg, sL, sG, nL, nG = caloric_tg(T, epa)
    arr, Tmid, d = kinetic_arrest(T, msd)
    print(f"\n=== {tag}  ({os.path.basename(path)}, {len(T)} 구간) ===")
    if tg:
        print(f"  caloric Tg      : {tg:7.0f} K")
        print(f"    액체 가지 기울기 : {sL*1e4:6.3f} x1e-4 eV/atom/K  (n={nL})")
        print(f"    유리 가지 기울기 : {sG*1e4:6.3f} x1e-4 eV/atom/K  (n={nG})")
        print(f"    기울기 비        : {sL/sG:5.2f}")
    else:
        print("  caloric Tg      : fit 실패 (구간 수 부족)")
    print(f"  kinetic arrest  : {arr:7.0f} K" if arr else "  kinetic arrest  : 미검출")
    print(f"  epa @ {T.min():.0f} K   : {epa[-1]:9.5f} eV/atom")
    print(f"  P   @ {T.min():.0f} K   : {P[-1]:9.1f} bar  ({P[-1]/1e4:.2f} GPa)")
    print(f"  MSD 총량         : {msd[-1]:7.1f} A^2")
    return dict(tag=tag, T=T, epa=epa, P=P, msd=msd, tg=tg, arr=arr,
                sL=sL, sG=sG, Tmid=Tmid, d=d)


def main():
    files = [("7net  2e13", os.path.join(PROFILE_DIR, "mq7net_profile.dat"))]
    for f in sorted(glob.glob(os.path.join(PROFILE_DIR, "mqbks_*_profile.dat"))):
        rate = os.path.basename(f).split("_")[1]
        files.append((f"BKS   {rate}", f))

    res = [report(t, p) for t, p in files if os.path.exists(p)]

    print("\n" + "=" * 62)
    print(f"{'run':<12}{'Tg(K)':>9}{'arrest(K)':>11}{'sL/sG':>8}{'P300(GPa)':>11}")
    print("-" * 62)
    for r in res:
        tg = f"{r['tg']:.0f}" if r['tg'] else "-"
        ar = f"{r['arr']:.0f}" if r['arr'] else "-"
        sr = f"{r['sL']/r['sG']:.2f}" if r['tg'] else "-"
        print(f"{r['tag']:<12}{tg:>9}{ar:>11}{sr:>8}{r['P'][-1]/1e4:>11.2f}")
    print("=" * 62)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
        col = {"7net  2e13": "#D7292A"}
        for r in res:
            c = col.get(r['tag'], None)
            ls = "-" if r['tag'].startswith("7net") else "--"
            ax[0].plot(r['T'], r['epa'], ls, lw=1.6, color=c, label=r['tag'])
            ax[1].semilogy(r['Tmid'], np.maximum(r['d'], 1e-3), ls, lw=1.4,
                           color=c, label=r['tag'])
            if r['tg']:
                ax[0].axvline(r['tg'], color=c or 'gray', ls=':', lw=1, alpha=.6)
        ax[1].axhline(DMSD_NOISE, color='k', ls=':', lw=1)
        ax[0].set_xlabel("T (K)"); ax[0].set_ylabel("epa (eV/atom)")
        ax[1].set_xlabel("T (K)"); ax[1].set_ylabel(r"$\Delta$MSD per 100 K ($\AA^2$)")
        for a in ax:
            a.invert_xaxis(); a.legend(fontsize=8); a.grid(alpha=.3)
        fig.tight_layout()
        fig.savefig("tg_fit.png", dpi=160)
        print("\n-> tg_fit.png 저장")
    except Exception as e:
        print(f"\n(플롯 생략: {e})")


if __name__ == "__main__":
    main()
