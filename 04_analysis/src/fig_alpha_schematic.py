import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DARK="#262626"; ORANGE="#E07B39"; PURPLE="#6A4C93"; GREY="#8A8A8A"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,
                     "axes.linewidth":1.4,"axes.labelsize":12})

fig,ax=plt.subplots(figsize=(5.6,2.5))
T=np.linspace(0,1,50); V0=0.30
ax.plot(T,V0+0.84*T,color=PURPLE ,lw=2.6,ls=(0,(5,2.5)),zorder=3)
ax.plot(T,V0+0.50*T,color=DARK,  lw=2.8,zorder=4)
ax.plot(T,V0+0.18*T,color=ORANGE ,lw=2.6,ls=(0,(1.6,1.8)),zorder=3)

ax.text(1.03,V0+0.84,r"additive A  ($\alpha\uparrow$)",fontsize=10.5,color=PURPLE ,va="center")
ax.text(1.03,V0+0.50,"a-SiO$_2$",fontsize=10.5,color=DARK,va="center",fontweight="bold")
ax.text(1.03,V0+0.18,r"additive B  ($\alpha\downarrow$)",fontsize=10.5,color=ORANGE ,va="center")

x0,x1=0.60,0.86
ax.plot([x0,x1],[V0+0.50*x0]*2,color=GREY,lw=1.0,ls=":")
ax.plot([x1,x1],[V0+0.50*x0,V0+0.50*x1],color=GREY,lw=1.0,ls=":")
ax.text(0.05,1.18,r"$\alpha=\frac{1}{V}\left(\frac{\partial V}{\partial T}\right)_P$",
        fontsize=12,va="center",color=DARK)

ax.set_xlabel("Temperature"); ax.set_ylabel("Volume")
ax.set_xlim(0,1.72); ax.set_ylim(0.22,1.32)
ax.set_xticks([]); ax.set_yticks([])
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.text(0.99,0.02,"schematic",transform=ax.transAxes,ha="right",va="bottom",
        fontsize=10,color=GREY,style="italic")
fig.tight_layout(pad=0.4)
fig.savefig("../fig/fig_alpha_schematic.png",dpi=300)
print("Done!")
