import argparse
import re
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
# 2. UNIFIED GLASGOW NORMS LOADER (Extracts All Needed Columns Once)
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


# ---------------------------------------------------------------------------
# 3. ANALYSIS PART 1: AFFECTIVE QUADRANTS & HEXBIN MAP (Figure 1)
# ---------------------------------------------------------------------------
def run_quadrant_analysis(df: pd.DataFrame):
    """
    Tests High-Arousal Positive vs. High-Arousal Negative quadrants and
    plots the 2D Valence x Arousal Hexbin + Violin distribution figure.
    """
    cond_sensual = (df["arousal"] >= 5.5) & (df["valence"] >= 5.8)
    cond_taboo   = (df["arousal"] >= 5.5) & (df["valence"] <= 3.5)
    cond_mundane = (df["arousal"] <= 4.2) & (df["valence"].between(4.0, 6.0))

    sensual_scores = df.loc[cond_sensual, "woody_tinny"]
    taboo_scores   = df.loc[cond_taboo,   "woody_tinny"]

    t_stat, p_val_t = stats.ttest_ind(sensual_scores, taboo_scores, equal_var=False)
    u_stat, p_val_u = stats.mannwhitneyu(sensual_scores, taboo_scores, alternative="two-sided")
    r_val, p_corr   = stats.pearsonr(
        df.loc[df["arousal"] >= 5.5, "valence"],
        df.loc[df["arousal"] >= 5.5, "woody_tinny"],
    )

    print("=== 1. GLASGOW NORMS QUADRANT HYPOTHESIS TEST ===")
    print(f"High-Arousal Positive (n={len(sensual_scores)}): Mean Score = {sensual_scores.mean():+.2f} (SD={sensual_scores.std():.2f})")
    print(f"High-Arousal Negative (n={len(taboo_scores)}):   Mean Score = {taboo_scores.mean():+.2f} (SD={taboo_scores.std():.2f})")
    print(f"Welch's t-test:       t = {t_stat:.3f}, p = {p_val_t:.4e}")
    print(f"Mann-Whitney U test:  U = {u_stat:.1f}, p = {p_val_u:.4e}")
    print(f"Correlation (Valence vs. Woody-Tinny among High-Arousal words): r = {r_val:+.3f} (p = {p_corr:.4e})\n")

    print("--- Top 8 Most 'Woody' High-Arousal Positive Words ---")
    print(df.loc[cond_sensual].nsmallest(8, "woody_tinny")[["word", "valence", "arousal", "woody_tinny"]].to_string(index=False))

    print("\n--- Top 8 Most 'Tinny' High-Arousal Negative Words ---")
    print(df.loc[cond_taboo].nlargest(8, "woody_tinny")[["word", "valence", "arousal", "woody_tinny"]].to_string(index=False))

    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.8), gridspec_kw={"width_ratios": [1.25, 1.0]})
    fig1.canvas.manager.set_window_title("Figure 1: Valence x Arousal Quadrants")
    fig1.suptitle("Glasgow Norms (5,553 Words): Valence × Arousal vs. Woody–Tinny Phonetics", fontsize=14, fontweight="bold")

    hb = ax1.hexbin(
        df["valence"],
        df["arousal"],
        C=df["woody_tinny"],
        reduce_C_function=np.mean,
        gridsize=22,
        cmap="BrBG",
        vmin=-30,
        vmax=30,
        edgecolors="white",
        linewidths=0.3,
    )
    cb = fig1.colorbar(hb, ax=ax1)
    cb.set_label("Mean Woody–Tinny Score (Brown = Woody, Teal = Tinny)", fontweight="bold")

    ax1.axhline(5.5, color="black", linestyle="--", linewidth=1, alpha=0.7)
    ax1.axvline(3.5, color="black", linestyle=":", linewidth=1, alpha=0.7)
    ax1.axvline(5.8, color="black", linestyle=":", linewidth=1, alpha=0.7)
    ax1.set_xlabel("Glasgow Valence (1 = Very Negative, 9 = Very Positive)", fontweight="bold")
    ax1.set_ylabel("Glasgow Arousal (1 = Passive/Calm, 9 = High Arousal)", fontweight="bold")
    ax1.set_title("1. Mean Phonetic Score Across Affective Space", fontweight="bold")

    groups = [
        sensual_scores.values,
        df.loc[cond_mundane, "woody_tinny"].values,
        taboo_scores.values,
    ]
    labels = [
        f"Sensual / Exciting\n(AROU≥5.5, VAL≥5.8)\nn={len(sensual_scores)}",
        f"Mundane Baseline\n(AROU≤4.2, Neutral)\nn={cond_mundane.sum()}",
        f"Harsh / Taboo\n(AROU≥5.5, VAL≤3.5)\nn={len(taboo_scores)}",
    ]

    parts = ax2.violinplot(groups, vert=False, showmeans=True, showextrema=False)
    for pc, color in zip(parts["bodies"], ["#8B4513", "#9E9E9E", "#00838F"]):
        pc.set_facecolor(color)
        pc.set_edgecolor("black")
        pc.set_alpha(0.75)

    ax2.axvline(0, color="black", linestyle="--", linewidth=1.2)
    ax2.set_yticks([1, 2, 3])
    ax2.set_yticklabels(labels, fontweight="bold")
    ax2.set_xlabel("Woody–Tinny Index (-100 = Woody, +100 = Tinny)", fontweight="bold")
    ax2.set_title("2. Phonetic Shift Across Glasgow Quadrants", fontweight="bold")
    ax2.grid(axis="x", linestyle=":", alpha=0.6)

    fig1.tight_layout()


# ---------------------------------------------------------------------------
# 4. ANALYSIS PART 2: LEXICON-WIDE DECILE REGRESSIONS (Figure 2)
# ---------------------------------------------------------------------------
def run_regression_analysis(df: pd.DataFrame):
    """
    Runs linear regressions and non-parametric Spearman correlations testing
    Arousal, Valence, Perceived Size, and Gender against the Woody-Tinny Index.
    """
    print(f"\n=== 2. LEXICON-WIDE REGRESSION RESULTS (n = {len(df):,} words) ===")
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

    print("\n--- Why Low Arousal (AROU <= 3.2) is Woody ---")
    low_arou = df[df["arousal"] <= 3.2]
    print(f"Count: {len(low_arou)} | Mean Woody-Tinny: {low_arou['woody_tinny'].mean():+.2f}")
    print(low_arou.nsmallest(10, "woody_tinny")[["word", "arousal", "valence", "woody_tinny"]].to_string(index=False))

    print("\n--- Why High Arousal (AROU >= 7.0) is Tinny ---")
    high_arou = df[df["arousal"] >= 7.0]
    print(f"Count: {len(high_arou)} | Mean Woody-Tinny: {high_arou['woody_tinny'].mean():+.2f}")
    print(high_arou.nlargest(10, "woody_tinny")[["word", "arousal", "valence", "woody_tinny"]].to_string(index=False))

    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig2.canvas.manager.set_window_title("Figure 2: Arousal & Size Regressions")
    fig2.suptitle("Direct Test: Does Physiological Arousal Drive 'Woody vs. Tinny' Phonetics?", fontsize=14, fontweight="bold")

    # Panel 1: Binned Arousal Deciles
    df_arou = df.copy()
    df_arou["arousal_bin"] = pd.qcut(df_arou["arousal"], q=10)
    binned = df_arou.groupby("arousal_bin", observed=False).agg(
        mean_arou=("arousal", "mean"),
        mean_wt=("woody_tinny", "mean"),
        sem_wt=("woody_tinny", "sem"),
    ).reset_index()

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

    reg = stats.linregress(df_arou["arousal"], df_arou["woody_tinny"])
    x_vals = np.linspace(df_arou["arousal"].min(), df_arou["arousal"].max(), 100)
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

    # Panel 2: Binned Perceived Size Deciles
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

    fig2.tight_layout()


# ---------------------------------------------------------------------------
# 5. MAIN ENTRY POINT
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Analyze Glasgow Norms Woody-Tinny Phonetics.")
    parser.add_argument(
        "--mode",
        choices=["all", "quadrants", "regression"],
        default="all",
        help="Which analysis and figures to generate (default: all)",
    )
    args = parser.parse_args()

    print("Loading Glasgow Norms...")
    df = load_glasgow_norms("GlasgowNorms.xlsx")
    print(f"Loaded {len(df):,} words from the Glasgow Norms.")

    print("Computing Woody-Tinny phonetic scores via CMUdict...")
    df["woody_tinny"] = df["word"].apply(score_word_arpabet)
    df = df.dropna(subset=["woody_tinny"]).copy()
    print(f"Successfully scored {len(df):,} words with CMUdict pronunciations.\n")

    if args.mode in ("all", "quadrants"):
        run_quadrant_analysis(df)

    if args.mode in ("all", "regression"):
        run_regression_analysis(df)

    plt.show()


if __name__ == "__main__":
    main()