# Computational Phonetics of Monty Python’s "Woody and Tinny Words"

An empirical psycholinguistic investigation testing the 1972 Monty Python sketch *"Woody and Tinny Words"* against the **CMU Pronouncing Dictionary (`CMUdict`)** and the **5,553-word Glasgow Norms dataset**.

---

## 1. Background & Hypothesis

In Monty Python’s classic sketch, Graham Chapman (the father), Eric Idle (the mother), and Carol Cleveland (the daughter) categorize English words by their acoustic texture:

* **Woody words** (*gorn, sausage, vole, bound, caribou*): Deep, resonant, rounded, and warm.
* **Tinny words** (*newspaper, litterbin, antelope, simian, tit*): Sharp, metallic, clipped, and high-pitched.

During the sketch, Graham Chapman’s character becomes obsessed with deliciously "woody" words—progressing from *gorn* and *sausage* to *intercourse, perturbation, erogenous zone,* and *loose woman*—before making the connection that *"all the naughty words sound woody."* However, when he brings up *tit*, the family agrees it is *"very tinny,"* sending Eric Idle’s character into tears.

This project tests that comedic premise computationally across two levels:

1. **Curated Lexicon Test:** Scoring canonical words from the sketch alongside polite sensual euphemisms and blunt Anglo-Saxon profanity.
2. **Corpus-Wide Psycholinguistic Test:** Mapping the **Glasgow Norms (Scott et al., 2019)** across **Valence (`VAL`)**, **Arousal (`AROU`)**, **Perceived Size (`SIZE`)**, and **Gender Association (`GEND`)** to test whether "naughty" or high-arousal words actually skew woody across the English lexicon.



---

## 2. Methodology

### A. The Phonetic Woody–Tinny Index ($-100$ to $+100$)

Words are converted into **ARPAbet** phonemes via `pronouncing` (`CMUdict`). Each phoneme is assigned an articulatory/acoustic weight $W_i \in [-1.0, +1.0]$ grounded in sound symbolism (**Bouba/Kiki**) and **Ohala’s Frequency Code**:

| Acoustic Dimension | "Woody" Profile ($W_i < 0$) | "Tinny" Profile ($W_i > 0$) |
| --- | --- | --- |
| **Vowels (Second Formant $F_2$)** | **Low & Back Rounded** (`AO`, `UW`, `OW`, `UH`, `AW`, `AA`). Lengthens the vocal tract and lowers $F_2$ resonance ($850\text{–}1,150\text{ Hz}$). | **High-Front Unrounded** (`IY`, `IH`, `EY`, `EH`). Arches the tongue toward the hard palate, raising $F_2$ ($1,800\text{–}2,350\text{ Hz}$). |
| **Consonants (Voicing & Airflow)** | **Voiced Approximants, Sonorants & Stops** (`W`, `R`, `L`, `M`, `B`, `G`). Continuous vocal cord vibration and low-frequency energy. | **Voiceless Plosives & Alveolar Sibilants** (`T`, `S`, `P`, `K`, `SH`, `CH`). Abrupt airflow stops and high-frequency hiss ($4,000\text{–}8,000\text{ Hz}$). |

### B. Lexical Stress Weighting

Because primary stressed syllables dominate human acoustic perception, vowel phonemes receive a stress multiplier ($m_i$) extracted from their ARPAbet stress digits:

* **Primary Stress (`1`):** $1.4\times$
* **Secondary Stress (`2`):** $1.2\times$
* **Consonants:** $1.0\times$
* **Unstressed Vowels (`0`):** $0.75\times$

The normalized word score is computed as:

$$\text{Woody–Tinny Index} = 100 \times \frac{\sum_{i=1}^{N} m_i W_i}{\sum_{i=1}^{N} m_i}$$

### C. Glasgow Norms Integration

The unified script ingests `GlasgowNorms.xlsx` (5,553 words), cleans parenthetical homograph sense tags (e.g., `"organ (body)"` $\rightarrow$ `"organ"`), and extracts mean ratings in a single pass for:

* **Arousal (`AROU`, Column 2):** $1 = \text{Passive/Calm}$ to $9 = \text{High Arousal}$.


* **Valence (`VAL`, Column 5):** $1 = \text{Very Negative}$ to $9 = \text{Very Positive}$.


* **Perceived Size (`SIZE`, Column 23):** $1 = \text{Very Small}$ to $7 = \text{Very Large}$.


* **Gender Association (`GEND`, Column 26):** $1 = \text{Very Feminine}$ to $7 = \text{Very Masculine}$.

---

## 3. Key Empirical Findings

### Finding 1: Curated Sensual Words Are Woody, But Blunt Profanity Is Tinny

When testing specific "naughty" vocabulary, English splits along etymological and phonetic lines:

* **Sensual & Erotic Euphemisms skew Woody ($-19$ to $-65$):** Words like *loose woman* (`-59.8`), *arousal* (`-50.2`), *bosom* (`-46.7`), *erogenous* (`-45.8`), and *voluptuous* (`-45.0`) rely heavily on rounded back vowels and voiced sonorants (`/l/`, `/r/`, `/w/`, `/m/`).
* **Blunt Taboo & Slang skew Tinny ($+15$ to $+94$):** Short profanity like *tit* (`+93.8`), *shit* (`+86.5`), *piss* (`+86.5`), and *prick* (`+55.9`) pack voiceless stops (`/t/`, `/p/`, `/k/`) and sibilants (`/s/`, `/ʃ/`) around high-front vowels (`/ɪ/`), matching Lev-Ari & McKay’s (2022) finding that profanity systematically avoids approximants.
* **The Sketch's Secret Outlier:** Graham Chapman includes *recidivist* (`+28.1`) in his rapid-fire list of woody words (*bound, vole, recidivist*), even though four high-front `/ɪ/` vowels and two `/s/` sibilants make it acoustically tinny.

### Finding 2: Across the Full Lexicon, Physiological Arousal Drives "Tinny" Phonetics

Testing all 5,553 words in the Glasgow Norms reveals that **the baseline English lexicon behaves the opposite of Graham Chapman’s premise**:

* **Low-Arousal Words are Woody:** In the 2D Valence $\times$ Arousal hexbin space, the bottom edge of calm, sleepy, low-arousal words ($\text{AROU} \approx 2.0\text{–}3.5$) is predominantly brown (Woody) across both negative and positive valence.


* **High-Arousal Quadrants Shift Tinny:** Both the **Harsh / Taboo quadrant** ($\text{AROU} \ge 5.5, \text{VAL} \le 3.5, n=224$) and the **Sensual / Exciting quadrant** ($\text{AROU} \ge 5.5, \text{VAL} \ge 5.8, n=813$) have group means shifted slightly to the positive (Tinny) side of zero, compared to the **Mundane Baseline** ($\text{AROU} \le 4.2, \text{Neutral}, n=1623$) which centers at zero. Because the broad high-arousal positive quadrant includes hundreds of non-erotic excitement words (*thrill, victory, electricity, sprint*), high-frequency front vowels and sharp plosives dominate the upper corners of the affective map.


* **Statistically Significant Arousal Gradient:** Ordinary Least Squares (OLS) regression across all 10 Arousal deciles confirms a positive correlation between physiological arousal and tinny phonetics ($r = +0.043, p = 1.33 \times 10^{-3}$). Only the lowest arousal bins—Decile 1 ($\text{Mean Arousal} \approx 3.0, \text{Score} \approx -3.1$) and Decile 3 ($\text{Mean Arousal} \approx 3.8, \text{Score} \approx -1.5$)—sit below zero in the Woody zone, while Decile 10 ($\text{Mean Arousal} \approx 6.8$) climbs to $\approx +3.0$ with its $95\%$ confidence interval entirely in the Tinny zone.



### Finding 3: A Non-Linear "Tiny = Tinny" Cliff in Perceived Size

Testing **Ohala’s Frequency Code** via the Glasgow Perceived Size (`SIZE`) ratings shows a striking non-linear threshold:

* While the linear fit across all 10 size deciles is marginal ($r = -0.026, p = 5.55 \times 10^{-2}$), **Decile 1 ($\text{Mean Size} \approx 2.25$) spikes to a Mean Woody–Tinny Score of $\approx +5.7$** ($\pm 95\%$ CI roughly $+2.7$ to $+8.7$).


* Across Deciles 2 through 10 ($\text{Mean Size } 3.0\text{ to }5.8$), the trajectory flattens out near $0$. English does not linearly make every large object sound woody, but it strongly concentrates high-frequency "tinny" phonemes into words denoting miniature concepts.



---

## 4. Installation & Usage

### Prerequisites

Requires Python 3.10+ and the following scientific packages:

```bash
pip install pronouncing pandas numpy scipy matplotlib openpyxl

```

### Files in This Project

* `GlasgowNorms.xlsx`: Official Glasgow Norms spreadsheet containing 5,553 words and 9 psycholinguistic dimensions.


* `WoodyTinny.py`: Unified analysis pipeline that loads `GlasgowNorms.xlsx` once, computes ARPAbet Woody–Tinny scores, and runs both the affective quadrant tests (`run_quadrant_analysis`) and the lexicon-wide decile regressions (`run_regression_analysis`).
* `edited-image.png`: Two-panel figure showing the 2D Valence $\times$ Arousal hexbin map and affective quadrant violin plots (`--mode quadrants`).


* `Figure_1.png`: Two-panel decile regression figure testing Arousal ($p = 1.33 \times 10^{-3}$) and Perceived Size ($p = 5.55 \times 10^{-2}$) against the Woody–Tinny Index (`--mode regression`).



### Running the Unified Analysis

Place `GlasgowNorms.xlsx` in the working directory and run `WoodyTinny.py`. You can run both analyses simultaneously or select a specific mode via the `--mode` flag:

```bash
# Run both analyses and open both Figure 1 and Figure 2 simultaneously (default)
python WoodyTinny.py

# Run only the Valence x Arousal quadrant hexbin & violin analysis
python WoodyTinny.py --mode quadrants

# Run only the lexicon-wide Arousal & Size decile regression analysis
python WoodyTinny.py --mode regression

```

---

## 5. References

1. **Scott, G. G., Keitel, A., Becirspahic, M., Yao, B., & Sereno, S. C. (2019).** *The Glasgow Norms: Ratings of 5,500 words on nine scales.* Behavior Research Methods, 51(3), 1258–1270.
2. **Lev-Ari, S., & McKay, R. (2022).** *The sound of swearing: Are there universal patterns in profanity?* Psychonomic Bulletin & Review, 29, 2292–2304.
3. **Ohala, J. J. (1994).** *The frequency code underlies the sound-symbolic use of voice pitch.* In Sound Symbolism (pp. 325–347). Cambridge University Press.
