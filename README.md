# NFL AI Prediction Engine (V1)

An open-source AI model that predicts NFL scores using historical data. Trained on **7,000+ games** (1999-2024) using Google's **Gemini 2.5 Flash** LLM via Vertex AI. 
All graphs and metrics were created using Microsoft Excel.

## The Results
Our model was tested against top ESPN analysts for Week 11 of the 2025 season. It was consistently on par with the human experts when evaluated on accuracy.

### 1. Sensitivity Analysis
We tested the model's accuracy across varying error thresholds.
**Neon Green Line = Our AI Model.** You can see it consistently scores close to the human analysts across almost all strictness levels.

![Sensitivity Analysis](sensitivity_analysis.png)

### 2. Where the Points Come From
We broke down the scores to see if analysts were just guessing winners or actually predicting the spread correctly.
* **Light Blue:** Points for Accuracy (Error <= 10 points).
* **Dark Blue:** Points for Correct Winner.

![Score Composition Breakdown](score_breakdown.png)

### 3. Win Score Analysis
Win Score measures the percentage of correct winner predictions. We compared the model's 'pick accuracy' directly against human analysts for the same slate of games.
**Green Bar = Our AI Model.** You can see that it is on par, if not better than, some of the analysts' predictions.

![Win Score Analysis](win_score_average.png)

### 4. Average Spread + Differential Mean
We compared the average combined error (Spread + Point Differential) across all predictions. 
* **Lower Bar = Higher Precision.**
**Insight:** While the AI Model's average error (14.5) was higher than human analysts (~11.0), this was largely driven by high volatility in two specific outlier games
where the model predicted large blowouts. This suggests that while the model is aggressive in identifying potential upsets, human analysts tend to be more conservative
with their point spreads.

![Average Error Graph](average_spread_differential_mean.png)
---

## How It Works
1.  **Data Scraping:** We built a custom R script to parse 8,000+ game files from `.rds` to JSON.
2.  **Feature Engineering:** We wrote a Python pipeline (`build_textbook_full.py`) to extrapolate the PPG and relevant statistics for every team since 1999.
3.  **Data Transformation and Formatting:** Created another Python script to correctly format everything extrapolated in `build_textbook_full.py`, titled `convert_to_vertex.py`.
4.  **Fine-Tuning:** We fine-tuned **Gemini 2.5 Flash** on Google Vertex AI to learn the relationship between *Pre-Game Stats* and *Final Scores*.

## Future Improvements
Currently implementing advanced metrics (such as DVOA, EPA/play, and injury impact scores) into the fine-tuning of the model to further enhance prediction capabilities.
