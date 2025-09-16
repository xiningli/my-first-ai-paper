import os
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def main():
    # Resolve project root from this script's location
    repo_root = Path(__file__).resolve().parents[2]
    fig_dir = repo_root / "src" / "latex" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    out_png = fig_dir / "simple_plot.png"

    x = np.linspace(0, 2 * np.pi, 200)
    y = np.sin(x)

    plt.figure(figsize=(6, 3.5), dpi=150)
    plt.plot(x, y, label="sin(x)")
    plt.title("Simple Sine Wave")
    plt.xlabel("x")
    plt.ylabel("sin(x)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png)
    print(f"Saved figure to {out_png}")


if __name__ == "__main__":
    main()
