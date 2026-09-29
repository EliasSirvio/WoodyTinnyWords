import os
import re
import urllib.request
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import pronouncing

# ---------------------------------------------------------------------------
# 1. PHONETIC WOODY-TINNY WEIGHTS (-1.0 = Pure Woody, +1.0 = Pure Tinny)
# ---------------------------------------------------------------------------
PHONEME_WEIGHTS = {
    # Woody Vowels (Low F2, Back, Rounded)
    "AO": -1.00, "UW": -0.95, "OW": -0.90, "UH": -0.85, "AW": -0.85,
    "AA": -0.70, "OY": -0.65, "ER": -0.55, "AH": -0.30,
    # Neutral to Tinny Vowels (High F2, Front, Unrounded)
    "AY":  0.10, "AE":  0.25, "EH":  0.40, "EY":  0.65, "IH":  0.85, "IY":  1.00,
    # Woody Consonants (Voiced Approximants, Nasals, Voiced Labial/Velar Stops)
    "W":  -0.95, "R":  -0.85, "G":  -0.85, "L":  -0.80, "B":  -0.80,
    "M":  -0.75, "V":  -0.60, "NG": -0.60, "D":  -0.45, "N":  -0.40,
    "JH": -0.40, "DH": -0.35, "ZH": -0.30, "Y":  -0.20,
    # Tinny Consonants (Voiceless Plosives & High-Frequency Sibilants)
    "HH":  0.20, "Z":   0.45, "TH":  0.50, "F":   0.55, "CH":  0.70,
    "SH":  0.75, "K":   0.80, "P":   0.85, "S":   0.90, "T":   1.00,
}


def score_word_arpabet(word_str: str) -> float | None:
    """
    Cleans Glasgow Norms homograph tags (e.g. 'organ (body)' -> 'organ')
    and computes the stress-weighted Woody-Tinny Index (-100 to +100).
    """
    # Strip parenthetical sense disambiguation used in Glasgow Norms
    clean_word = re.sub(r"\s*\(.*?\)", "", str(word_str)).strip().lower()
    if not clean_word or not clean_word.isalpha():
        return None

    phones_list = pronouncing.phones_for_word(clean_word)
    if not phones_list:
        return None

    tokens = phones_list[0].split()
    weighted_scores = []
    weights_used = []

    for token in tokens:
        base = re.sub(r"\d", "", token)
        stress_match = re.search(r"\d", token)
        if base not in PHONEME_WEIGHTS:
            continue

        # Primary stressed vowels carry 1.4x perceptual weight
        if stress_match:
            stress = int(stress_match.group())
            mult = 1.4 if stress == 1 else (1.2 if stress == 2 else 0.75)
        else:
            mult = 1.0

        weighted_scores.append(PHONEME_WEIGHTS[base] * mult)
        weights_used.append(mult)

    if not weights_used:
        return None

    return float(np.clip((np.sum(weighted_scores) / np.sum(weights_used)) * 100, -100, 100))


# ---------------------------------------------------------------------------
# 2. LOAD OR DOWNLOAD GLASGOW NORMS (Scott et al., 2019 - 5,553 Words)
# ---------------------------------------------------------------------------

def load_glasgow_norms(filepath: str = "GlasgowNorms.xlsx") -> pd.DataFrame:
    """
    Extracts word (col 0), arousal (col 2), valence (col 5),
    size (col 23), and gender (col 26) from GlasgowNorms.xlsx.
    """
    df_raw = pd.read_excel(filepath, header=None, skiprows=2)

    df = pd.DataFrame({
        "word": df_raw.iloc[:, 0].astype(str).str.strip(),
        "arousal": pd.to_numeric(df_raw.iloc[:, 2], errors="coerce"),
        "valence": pd.to_numeric(df_raw.iloc[:, 5], errors="coerce"),
        "size": pd.to_numeric(df_raw.iloc[:, 23], errors="coerce"),
        "gender": pd.to_numeric(df_raw.iloc[:, 26], errors="coerce"),
    })

    df = df.dropna(subset=["word", "arousal", "valence"]).copy()
    return df[df["word"] != ""].copy()


def run_regression_analysis(df: pd.DataFrame):
    """
    Runs linear regressions and non-parametric Spearman correlations testing
    Arousal, Valence, Perceived Size, and Gender against the Woody-Tinny Index.
    """
    df = df.dropna(subset=["woody_tinny"]).copy()
    print(f"\n=== LEXICON-WIDE REGRESSION RESULTS (n = {len(df):,} words) ===")
    print(f"{'DIMENSION':<18} | {'PEARSON r':>10} | {'p-VALUE':>12} | {'SPEARMAN rho':>12} | {'SLOPE (pts/unit)':>16}")
    print("-" * 80)

    for col, label in [
        ("arousal", "Arousal (AROU)"),
        ("valence", "Valence (VAL)"),
        ("size",    "Size (SIZE)"),
        ("gender",  "Gender (GEND)"),
    ]:
        sub = df.dropna(subset=[col, "woody_tinny"])
        res = stats.linregress(sub[col], sub["woody_tinny"])
        rho, _ = stats.spearmanr(sub[col], sub["woody_tinny"])
        print(f"{label:<18} | {res.rvalue:>+10.4f} | {res.pvalue:>12.4e} | {rho:>+12.4f} | {res.slope:>+16.2f}")

    # Print the extremes driving the Arousal gradient
    print("\n--- Why Low Arousal (AROU <= 3.2) is Woody ---")
    low_arou = df[df["arousal"] <= 3.2]
    print(f"Count: {len(low_arou)} | Mean Woody-Tinny: {low_arou['woody_tinny'].mean():+.2f}")
    print(low_arou.nsmallest(10, "woody_tinny")[["word", "arousal", "valence", "woody_tinny"]].to_string(index=False))

    print("\n--- Why High Arousal (AROU >= 7.0) is Tinny ---")
    high_arou = df[df["arousal"] >= 7.0]
    print(f"Count: {len(high_arou)} | Mean Woody-Tinny: {high_arou['woody_tinny'].mean():+.2f}")
    print(high_arou.nlargest(10, "woody_tinny")[["word", "arousal", "valence", "woody_tinny"]].to_string(index=False))

    # -----------------------------------------------------------------------
    # PLOT: AROUSAL DECILES & LINEAR REGRESSION TRENDLINE
    # -----------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("Direct Test: Does Physiological Arousal Drive 'Woody vs. Tinny' Phonetics?", fontsize=14, fontweight="bold")

    # Panel 1: Binned Arousal Deciles with 95% Confidence Intervals
    df["arousal_bin"] = pd.qcut(df["arousal"], q=10)
    binned = df.groupby("arousal_bin", observed=False).agg(
        mean_arou=("arousal", "mean"),
        mean_wt=("woody_tinny", "mean"),
        sem_wt=("woody_tinny", "sem"),
        count=("woody_tinny", "count"),
    ).reset_index()

    # Plot individual decile means + 95% CI error bars
    colors = ["#8B4513" if v < 0 else "#00838F" for v in binned["mean_wt"]]
    ax1.errorbar(
        binned["mean_arou"],
        binned["mean_wt"],
        yerr=1.96 * binned["sem_wt"],
        fmt="none",
        ecolor="black",
        elinewidth=1.2,
        capsize=4,
        zorder=2,
    )
    ax1.scatter(
        binned["mean_arou"],
        binned["mean_wt"],
        c=colors,
        s=110,
        edgecolors="black",
        zorder=3,
        label="Decile Mean (±95% CI)",
    )

    # Overlay global OLS regression line
    reg = stats.linregress(df["arousal"], df["woody_tinny"])
    x_vals = np.linspace(df["arousal"].min(), df["arousal"].max(), 100)
    ax1.plot(
        x_vals,
        reg.intercept + reg.slope * x_vals,
        color="#D32F2F",
        linewidth=2,
        linestyle="--",
        label=f"OLS Fit (r = {reg.rvalue:+.3f}, p = {reg.pvalue:.2e})",
    )

    ax1.axhline(0, color="gray", linestyle=":", linewidth=1)
    ax1.set_xlabel("Glasgow Arousal Decile Mean (1 = Calm/Sleepy, 9 = Intense/Aroused)", fontweight="bold")
    ax1.set_ylabel("Mean Woody–Tinny Score (<0 Woody, >0 Tinny)", fontweight="bold")
    ax1.set_title("1. Woody–Tinny Trajectory Across 10 Arousal Deciles", fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(True, linestyle=":", alpha=0.5)

    # Panel 2: Compare Binned Slopes of Arousal vs. Perceived Size
    df_size = df.dropna(subset=["size"]).copy()
    df_size["size_bin"] = pd.qcut(df_size["size"], q=10)
    binned_size = df_size.groupby("size_bin", observed=False).agg(
        mean_size=("size", "mean"),
        mean_wt=("woody_tinny", "mean"),
        sem_wt=("woody_tinny", "sem"),
    ).reset_index()

    reg_size = stats.linregress(df_size["size"], df_size["woody_tinny"])
    x_size = np.linspace(df_size["size"].min(), df_size["size"].max(), 100)

    ax2.errorbar(
        binned_size["mean_size"],
        binned_size["mean_wt"],
        yerr=1.96 * binned_size["sem_wt"],
        fmt="o",
        color="#5D4037",
        ecolor="black",
        elinewidth=1.2,
        capsize=4,
        markersize=8,
        label="Size Decile Mean (±95% CI)",
    )
    ax2.plot(
        x_size,
        reg_size.intercept + reg_size.slope * x_size,
        color="#1976D2",
        linewidth=2,
        linestyle="--",
        label=f"OLS Fit (r = {reg_size.rvalue:+.3f}, p = {reg_size.pvalue:.2e})",
    )
    ax2.axhline(0, color="gray", linestyle=":", linewidth=1)
    ax2.set_xlabel("Glasgow Perceived Size (1 = Very Small, 7 = Very Large)", fontweight="bold")
    ax2.set_ylabel("Mean Woody–Tinny Score (<0 Woody, >0 Tinny)", fontweight="bold")
    ax2.set_title("2. Ohala's Frequency Code: Perceived Size vs. Woody–Tinny", fontweight="bold")
    ax2.legend(loc="upper right")
    ax2.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # 1. Load the dataset from the local Excel file
    print("Loading Glasgow Norms...")
    df = load_glasgow_norms("GlasgowNorms.xlsx")
    print(f"Loaded {len(df):,} words.")

    # 2. Score each word on the Woody-Tinny spectrum using CMUdict
    print("Computing Woody-Tinny phonetic scores...")
    df["woody_tinny"] = df["word"].apply(score_word_arpabet)

    # 3. Drop words that couldn't be transcribed (e.g. unknown slang/proper nouns)
    df = df.dropna(subset=["woody_tinny"]).copy()
    print(f"Successfully scored {len(df):,} words.\n")

    # 4. Run regressions, print statistical summaries, and generate the plots
    run_regression_analysis(df)
