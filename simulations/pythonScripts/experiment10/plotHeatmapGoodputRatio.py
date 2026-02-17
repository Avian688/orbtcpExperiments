import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize

# ─── Matplotlib Styling ───────────────────────────────────────────────────────
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif']  = ["Times New Roman", "Times", "DejaVu Serif"]
plt.rcParams['font.weight'] = 'normal'
plt.rcParams['font.size']   = 40
plt.rcParams['text.usetex'] = True

# ─── Experiment Setup ─────────────────────────────────────────────────────────
# Analyze Pair1 and Pair3, but label Pair3 as “Pair2” in the outputs
pairs2      = ['Pair1', 'Pair3']
pair_labels = {'Pair1': 'Pair1', 'Pair3': 'Pair2'}

protocols   = ['cubic', 'bbr', 'bbr3', 'orbtcp']  # LeoTCP last
RUNS        = [1, 2, 3, 4, 5]

FRIENDLY    = {'cubic':'Cubic', 'bbr':'BBRv1', 'bbr3':'BBRv3', 'orbtcp':'LeoTCP'}

# ─── Data Extraction ──────────────────────────────────────────────────────────
def fairness_ratio(proto, pair):
    base = os.path.join("../../../paperExperiments/experiment10/csvs",
                        proto.title(), pair)
    vals = []
    for run in RUNS:
        p0 = os.path.join(base, f"run{run}", "leoconstellation.server[0].app[0]", "goodput.csv")
        p1 = os.path.join(base, f"run{run}", "leoconstellation.server[1].app[0]", "goodput.csv")
        if not (os.path.exists(p0) and os.path.exists(p1)):
            continue
        df0, df1 = pd.read_csv(p0), pd.read_csv(p1)
        if "goodput" not in df0 or "goodput" not in df1:
            continue
        g0, g1 = df0['goodput'].mean(), df1['goodput'].mean()
        if g0 > 0 and g1 > 0:
            vals.append(min(g0, g1) / max(g0, g1))
    return (float(np.mean(vals)), float(np.std(vals))) if vals else (0.0, 0.0)

def avg_goodput(proto, pair):
    base = os.path.join("../../../paperExperiments/experiment10/csvs",
                        proto.title(), pair)
    vals = []
    for run in RUNS:
        for srv in [0, 1]:
            fpath = os.path.join(base,
                                 f"run{run}",
                                 f"leoconstellation.server[{srv}].app[0]",
                                 "goodput.csv")
            if os.path.exists(fpath):
                df = pd.read_csv(fpath)
                if 'goodput' in df:
                    vals.append(df['goodput'].mean())
    return float(np.mean(vals)) if vals else 0.0

# ─── Build mean/std DataFrames ────────────────────────────────────────────────
cmap = LinearSegmentedColormap.from_list('r_y_g', ['red', 'yellow', 'green'], N=256)
norm = Normalize(vmin=0.5, vmax=1.0)

df_mean = pd.DataFrame(index=pairs2, columns=protocols, dtype=float)
df_std  = pd.DataFrame(index=pairs2, columns=protocols, dtype=float)
for p in pairs2:
    for q in protocols:
        mu, sigma = fairness_ratio(q, p)
        df_mean.at[p, q] = mu
        df_std.at[p, q]  = sigma

# ─── Heatmap Plotting ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(df_mean.values, origin='upper', aspect='auto',
               cmap=cmap, norm=norm)

ax.set_xticks(range(len(protocols)))
ax.set_xticklabels([FRIENDLY[q] for q in protocols], fontsize=24)
ax.set_yticks(range(len(pairs2)))
ax.set_yticklabels([pair_labels[p] for p in pairs2], fontsize=24)

for i, p in enumerate(pairs2):
    for j, q in enumerate(protocols):
        mu, sigma = df_mean.iat[i, j], df_std.iat[i, j]
        ax.text(j, i, f"{mu:.2f}±{sigma:.2f}",
                ha='center', va='center', fontsize=20)

cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Mean Goodput Ratio', rotation=90, fontsize=34, labelpad=20)
cbar.set_ticks([0.5, 0.75, 1.0])
cbar.ax.tick_params(labelsize=24)

plt.subplots_adjust(left=0.10, right=0.84, top=0.98, bottom=0.15)
fig.savefig('heatmap_goodput_fairness_exp10.pdf', dpi=1080, bbox_inches='tight')
plt.close(fig)

# ─── LaTeX Table Generation to TXT ─────────────────────────────────────────────
def cellshade(val, alpha=0.8):
    r, g, b, _ = cmap(norm(val))
    rl = r + (1 - r) * alpha
    gl = g + (1 - g) * alpha
    bl = b + (1 - b) * alpha
    return f"{rl:.2f},{gl:.2f},{bl:.2f}"

# Prepare ratio rows
ratio_rows = []
for p in pairs2:
    row = []
    for q in protocols:
        mu, sigma = fairness_ratio(q, p)
        shade = cellshade(mu)
        row.append(f"\\cellcolor[rgb]{{{shade}}}{mu:.2f}\\pm{sigma:.2f}")
    ratio_rows.append(row)

# Prepare average goodputs rows (in Mbps)
gp_rows = []
for p in pairs2:
    row = []
    for q in protocols:
        val = avg_goodput(q, p) / 1e6
        row.append(f"{val:.2f}")
    gp_rows.append(row)

# Build LaTeX lines, using pair_labels for the leftmost column
ncols     = len(protocols)
ncolspan  = ncols + 1
lines = [
    "% Requires: \\usepackage[table]{xcolor}",
    "\\begin{tabular}{l" + "c"*ncols + "}",
    "\\toprule",
    "& " + " & ".join(FRIENDLY[q] for q in protocols) + " \\\\",
    "\\midrule"
]

# Pair ratio rows
for idx, p in enumerate(pairs2):
    label = pair_labels[p]
    cells = " & ".join(ratio_rows[idx])
    lines.append(f"{label} & {cells} \\\\")

lines += [
    "\\midrule",
    f"\\multicolumn{{{ncolspan}}}{{c}}{{\\textbf{{Average Goodputs (Mbps)}}}} \\\\",
    "\\midrule"
]

# Avg goodputs rows
for idx, p in enumerate(pairs2):
    label = pair_labels[p]
    cells = " & ".join(gp_rows[idx])
    lines.append(f"{label} & {cells} \\\\")

lines += [
    "\\bottomrule",
    "\\end{tabular}"
]

# Write to TXT
out = "fairness_table_pairs1_2.txt"
with open(out, 'w') as f:
    f.write("\n".join(lines))
print(f"LaTeX table written to {out}")