import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import scienceplots

# Use the science style
plt.style.use('science')
plt.rcParams['text.usetex'] = False
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
})

# Protocol definitions
PROTOCOLS = ['cubic', 'bbr', 'bbr3', 'orbtcp']
COLORS    = {
    'cubic':  '#0C5DA5',
    'bbr':    '#00B945',
    'orbtcp': '#FF9500',
    'bbr3':   '#eb0909'
}
FRIENDLY  = {
    'cubic':  'Cubic',
    'bbr':    'BBRv1',
    'orbtcp': 'LeoTCP',
    'bbr3':   'BBRv3'
}
MARKERS   = {
    'cubic':  'x',
    'bbr':    '.',
    'bbr3':   '_',
    'orbtcp': '^'
}

# Create a very thin figure for the legend strip
fig, ax = plt.subplots(figsize=(40, 1))
ax.axis('off')

# Build legend handles: thinner line + very large, thick markers (no edge)
for prot in PROTOCOLS:
    ax.add_line(mlines.Line2D(
        [], [],
        color=COLORS[prot],
        linestyle='-',
        linewidth=8,                   # thin base line
        marker=MARKERS[prot],
        markersize=130,                # very large symbol
        markerfacecolor=COLORS[prot],
        markeredgecolor=COLORS[prot],  # no separate edge color
        markeredgewidth=25,            # thick marker strokes
        label=FRIENDLY[prot]
    ))

# Create the legend centered in the strip
legend = ax.legend(
    ncol=len(PROTOCOLS),
    loc='center',
    bbox_to_anchor=(0.5, 0.5),
    columnspacing=8,
    handletextpad=0.5,
    fontsize=200,
    frameon=False,
    borderaxespad=1
)

# Save the legend-only plot (unchanged filename)
out_path = "protocol_legend_lines_with_symbols.pdf"
fig.savefig(
    out_path,
    bbox_inches='tight',
    pad_inches=0,
    transparent=True,
    dpi=1080
)

print(f"Legend saved to: {out_path}")