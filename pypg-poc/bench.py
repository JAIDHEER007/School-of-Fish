import argparse
import csv
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                          # draw straight to files, never open a window
import matplotlib.pyplot as plt
import numpy as np                             # installed together with matplotlib
from matplotlib.ticker import FuncFormatter, NullLocator

import settings
from flock import Flock

DEFAULT_SIZES = [25, 50, 100, 200, 400, 800, 1600, 3200, 6400, 12800]
DEFAULT_OUT_DIR = Path(__file__).parent / "benchmark"   # next to this script, from any cwd
CSV_NAME = "bench_results.csv"
FRAME_BUDGET_MS = 1000.0 / 60.0                # one frame at 60 FPS

# Chart colors: blue for measurements, orange for the fitted model, gray for references.
MEASURED_COLOR = "#2a78d6"
FIT_COLOR = "#eb6834"
REFERENCE_COLOR = "#52514e"


def bench(n, steps):
    """Time one run: returns ms per step for a flock of n fish."""
    flock = Flock(n, settings.SEED)
    flock.step(settings.SIM_DT)                # warm-up step (not timed)
    t0 = time.perf_counter()
    for _ in range(steps):
        flock.step(settings.SIM_DT)
    elapsed = time.perf_counter() - t0
    return elapsed / steps * 1000.0            # ms per step


def bench_avg(n, steps, runs):
    """Repeat the same experiment `runs` times and return the average ms/step."""
    times = [bench(n, steps) for _ in range(runs)]
    return sum(times) / len(times)


def run_benchmark(sizes, steps, runs, csv_path):
    """Benchmark every size, writing each row to the CSV as soon as it is done."""
    rows = []
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        # runs and steps are saved per row so the CSV documents how each number was measured.
        writer.writerow(["fishcount", "ms/step", "runs", "steps"])
        for n in sizes:
            avg = bench_avg(n, steps, runs)
            print(f"n = {n:5d}   {avg:8.2f} ms/step   (avg of {runs} runs x {steps} steps)")
            writer.writerow([n, f"{avg:.4f}", runs, steps])
            f.flush()                          # keep partial results if you Ctrl+C
            rows.append((n, avg))
    print(f"Results saved to {csv_path}")
    return rows


def load_results(csv_path):
    """Read (n, ms/step) rows back from a CSV written by run_benchmark."""
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        next(reader)                           # skip the header row
        # Only the first two columns are needed for plotting; this also reads
        # older CSVs that were written before the runs/steps columns existed.
        return [(int(row[0]), float(row[1])) for row in reader]


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def fit_quadratic(ns, ms):
    """Least-squares fit of  ms = a·n² + b·n.

    a·n² is the pairwise work (the inner loop), b·n is the per-fish work
    (steering, wander, update). There is no constant term: 0 fish = 0 work.
    """
    A = np.column_stack([ns ** 2, ns])
    (a, b), *_ = np.linalg.lstsq(A, ms, rcond=None)
    return a, b


def loglog_slope(ns, ms):
    """Slope of the best straight line through (log n, log ms).

    If ms ≈ c·n^k then log(ms) = log(c) + k·log(n), so the slope IS the exponent k.
    """
    slope, _intercept = np.polyfit(np.log10(ns), np.log10(ms), 1)
    return slope


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def style_axes(ax):
    """Light grid and no top/right frame, so the data stands out."""
    ax.grid(True, color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def plot_ms_vs_n(ns, ms, a, b, path):
    """Linear axes: the measurements trace a parabola, which is what n² looks like."""
    fig, ax = plt.subplots(figsize=(8, 5))

    curve_n = np.linspace(0, ns.max() * 1.05, 200)
    ax.plot(curve_n, a * curve_n ** 2 + b * curve_n, color=FIT_COLOR, linewidth=2,
            label=f"fit: {a * 1e6:.0f} ns·n² + {b * 1e3:.1f} µs·n")
    ax.plot(ns, ms, "o", color=MEASURED_COLOR, markersize=7,
            markeredgecolor="white", markeredgewidth=1.5, zorder=3, label="measured")

    ax.annotate(f"{ms[-1] / 1000:.1f} s per step", (ns[-1], ms[-1]),
                textcoords="offset points", xytext=(-10, 4), ha="right")

    ax.set_title("Naive boids: time per step vs. fish count")
    ax.set_xlabel("fish count n")
    ax.set_ylabel("ms per step")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    style_axes(ax)
    ax.legend(frameon=False, loc="upper left")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_complexity(ns, ms, slope, path):
    """Log-log axes: a power law n^k becomes a straight line with slope k."""
    fig, ax = plt.subplots(figsize=(8, 5))

    # Reference lines through the LARGEST measurement, where the n² term
    # dominates (at small n the per-fish b·n work still bends the curve).
    x = np.array([ns.min() * 0.8, ns.max() * 1.25])
    n_ref, ms_ref = ns[-1], ms[-1]
    ax.plot(x, ms_ref * (x / n_ref) ** 2, "--", color=REFERENCE_COLOR, linewidth=1.5,
            label="O(n²) reference, slope 2")
    ax.plot(x, ms_ref * (x / n_ref), ":", color=REFERENCE_COLOR, linewidth=1.5,
            label="O(n) reference, slope 1")

    # Above this line the simulation can no longer keep up with 60 FPS.
    ax.axhline(FRAME_BUDGET_MS, color=REFERENCE_COLOR, linewidth=1, alpha=0.5)
    ax.text(x[1], FRAME_BUDGET_MS * 1.15, "60 FPS budget (16.7 ms)",
            ha="right", va="bottom", color=REFERENCE_COLOR, fontsize=9)

    ax.plot(ns, ms, "-o", color=MEASURED_COLOR, linewidth=2, markersize=7,
            markeredgecolor="white", markeredgewidth=1.5, zorder=3,
            label=f"measured, slope {slope:.2f}")

    ax.set_xscale("log")
    ax.set_yscale("log")
    # Label the sizes we measured, skipping any that would crowd its left
    # neighbor on the log axis (e.g. 1000 right after 800).
    ticks = [ns[0]]
    for n in ns[1:]:
        if n / ticks[-1] >= 1.5:
            ticks.append(n)
    ax.set_xticks(ticks, labels=[f"{n:.0f}" for n in ticks])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:g}"))   # 1, 10, 100 instead of 10⁰, 10¹
    ax.set_title(f"Time complexity: log-log slope {slope:.2f} → O(n²)")
    ax.set_xlabel("fish count n (log scale)")
    ax.set_ylabel("ms per step (log scale)")
    style_axes(ax)
    ax.legend(frameon=False, loc="upper left")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(rows, out_dir):
    if len(rows) < 3:
        print("Need at least 3 fish counts to fit and plot; skipping graphs.")
        return
    ns = np.array([n for n, _ in rows], dtype=float)
    ms = np.array([t for _, t in rows])

    a, b = fit_quadratic(ns, ms)
    slope = loglog_slope(ns, ms)
    print(f"Fit: ms/step ≈ {a * 1e6:.1f} ns·n² + {b * 1e3:.2f} µs·n   "
          f"(log-log slope {slope:.2f})")

    plot_ms_vs_n(ns, ms, a, b, out_dir / "ms_vs_n.png")
    plot_complexity(ns, ms, slope, out_dir / "complexity_loglog.png")
    print(f"Graphs saved to {out_dir}")


def parse_args():
    p = argparse.ArgumentParser(description="Benchmark the naive flock simulation.")
    p.add_argument("--steps", type=int, default=20,
                   help="timed steps per run (default: 20)")
    p.add_argument("--runs", type=int, default=5,
                   help="number of runs to average per fish count (default: 5)")
    p.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES,
                   help="fish counts to test (default: %(default)s)")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                   help="folder for the CSV and graphs (default: benchmark/ next to bench.py)")
    p.add_argument("--plot-only", action="store_true",
                   help="skip benchmarking; redraw graphs from the existing CSV")
    args = p.parse_args()
    if args.steps < 1 or args.runs < 1:
        p.error("--steps and --runs must be at least 1")
    return args


if __name__ == "__main__":
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / CSV_NAME

    if args.plot_only:
        rows = load_results(csv_path)
    else:
        rows = run_benchmark(args.sizes, args.steps, args.runs, csv_path)

    make_plots(rows, args.out_dir)
