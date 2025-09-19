import os
from pathlib import Path

# Force a non-interactive backend early to avoid any potential GUI blocking
os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
import matplotlib.pyplot as plt


def main():
    # Resolve project root from this script's location
    repo_root = Path(__file__).resolve().parents[2]
    fig_dir = repo_root / "src" / "latex" / "generated_data"
    fig_dir.mkdir(parents=True, exist_ok=True)
    out_png = fig_dir / "simple_plot.png"

    x = np.linspace(0, 2 * np.pi, 200)
    y = np.sin(x)

    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=150)
    ax.plot(x, y, label="sin(x)")
    ax.set_title("Simple Sine Wave")
    ax.set_xlabel("x")
    ax.set_ylabel("sin(x)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
    print(f"Saved figure to {out_png}")


if __name__ == "__main__":
    main()
