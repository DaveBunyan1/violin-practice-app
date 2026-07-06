import os
import json
from matplotlib.container import BarContainer
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from app.core.config import settings


def load_p99_metrics(folder_path: str):
    """Parses benchmark JSON files and extracts p99 latencies per stage."""
    data_points = []

    # Mapping to look for specific target files
    files = {
        "50k Frames": f"{settings.VERSION}/{settings.VERSION}_50000_frames_{settings.BUFFER_SIZE}_buffer_size.json",
        "100k Frames": f"{settings.VERSION}/{settings.VERSION}_100000_frames_{settings.BUFFER_SIZE}_buffer_size.json",
        "1M Frames": f"{settings.VERSION}/{settings.VERSION}_1000000_frames_{settings.BUFFER_SIZE}_buffer_size.json",
    }

    for run_label, filename in files.items():
        full_path = os.path.join(folder_path, filename)
        if not os.path.exists(full_path):
            print(f"⚠️ Missing file: {full_path}. Skipping from plot.")
            continue

        with open(full_path, "r") as f:
            telemetry = json.load(f)

        stages = telemetry["pipeline_analysis_ms"]["stages"]

        # Extract p99 for the main core tracking stages
        for stage_name, metrics in stages.items():
            # Clean up names for prettier chart labels
            clean_stage_name = stage_name.split("_", 1)[-1].replace("_", " ").title()

            data_points.append(
                {
                    "Run Scale": run_label,
                    "Pipeline Stage": clean_stage_name,
                    "p99 Latency (ms)": metrics["p99"],
                }
            )

    return pd.DataFrame(data_points)


def generate_benchmark_chart():
    # 1. Load data
    results_dir = "docs/"
    df = load_p99_metrics(results_dir)

    if df.empty:
        print("❌ No telemetry data found to plot!")
        return

    # 2. Set style and canvas
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(11, 6))

    # 3. Create grouped bar chart
    ax = sns.barplot(
        data=df,
        x="Pipeline Stage",
        y="p99 Latency (ms)",
        hue="Run Scale",
        palette="viridis",
        edgecolor="0.2",
    )

    # 4. Draw the Real-Time Budget Deadline Constraint line
    plt.axhline(
        y=settings.BUFFER_SIZE / settings.SAMPLE_RATE * 1000,
        color="crimson",
        linestyle="--",
        linewidth=1.5,
        label=f"Real-time Window Limit ({round(settings.BUFFER_SIZE/settings.SAMPLE_RATE * 1000, 2)}ms)",
    )

    # Adjust y-limit dynamically so the line doesn't compress low-ms findings completely
    max_measured_p99 = df["p99 Latency (ms)"].max()
    plt.ylim(0, min(190, max_measured_p99 * 1.5))

    # 5. Styling and labels
    plt.title(
        "Pipeline Scaling Profile: Tail Latency (p99) Convergence Analysis",
        fontsize=14,
        pad=15,
        fontweight="bold",
    )
    plt.xlabel("Audio Architecture Pipeline Stage", fontsize=12, labelpad=10)
    plt.ylabel("Latency (milliseconds)", fontsize=12, labelpad=10)
    plt.legend(title="Data Volume Volume Scale", loc="upper right")

    # Annotate bars with exact numbers
    for container in ax.containers:
        if isinstance(container, BarContainer):
            ax.bar_label(container, fmt="%.2f ms", padding=3, fontsize=9)

    plt.tight_layout()

    # 6. Export directly to your project workspace
    output_image_path = os.path.join(
        results_dir,
        f"{settings.VERSION}/{settings.VERSION}_{settings.BUFFER_SIZE}_benchmark_scaling_profiles.png",
    )
    plt.savefig(output_image_path, dpi=300)
    print(f"🎉 Chart successfully compiled and saved to: {output_image_path}")


if __name__ == "__main__":
    generate_benchmark_chart()
