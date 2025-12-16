# NFL AI Prediction Engine: Project Documentation

**An open-source, iterative AI experiment to teach Large Language Models (LLMs) how to predict NFL game outcomes using historical play-by-play data.**

> **Core Tech:** Google Gemini 2.5 Flash & Flash-Lite (via Vertex AI)  
> **Data Source:** `nflfastr` (1999–2025)  
> **Models:** AI Model V1 used 2.5 Flash with data from 1999-2025 based solely on Points Per Game (PPG). **V2** and **V3** both used advanced statistics such as EPA/Play, with V3 accounting for defensive stats as well as offensive.

---

## 1. Project Overview & Hypothesis

The goal of this project was to determine if a Generative AI model could move beyond simple statistical regression and "understand" the nuances of American football matchups. We hypothesized that by fine-tuning an LLM on historical data, it could learn to weigh complex variables—like offensive efficiency, defensive resistance, and injury impacts—better than standard "Points Per Game" models.

The project evolved through three distinct phases, each adding a layer of complexity to the model's "context window."

### The Evolution of the Models

| Model Version | Architecture | Key Metrics Used | The Hypothesis | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **V1 (Baseline)** | **Gemini 2.5 Flash** | Points Per Game (PPG), Location | **"Simple is Better"**<br>Can basic scoring trends predict winners? | **Solid Baseline.** Performed on par with human analysts in Week 11 but lacked nuance for complex matchups. |
| **V2 (Efficiency)** | **Gemini 2.5 Flash-Lite** | EPA/Play, Success Rate, Dropback Efficiency | **"The Glass Cannon"**<br>Will advanced offensive stats outperform PPG? | **High Volatility.** Excellent at predicting high-scoring games but failed to account for defensive resistance. |
| **V3 (Context)** | **Gemini 2.5 Flash-Lite** | Offense + **Defense** + **Injuries** | **"The Complete Picture"**<br>Does adding defensive stats & injury reports stabilize the model? | **High Stability.** Mitigated the extreme errors of V2. While V2 won Week 13 on raw picks, V3 showed the tightest mathematical variance over time. |

---

## 2. Technical Architecture & Workflow

This project utilizes a modular Python/R pipeline to transform raw data into actionable AI predictions. The data engineering process evolved significantly with each version.

### A. Data Engineering Pipeline

#### Phase 1: The Baseline (V1)
* **Goal:** Establish a working pipeline using basic box-score data.
* **Scraping:** Built a custom R script to parse 8,000+ game files from `.rds` format to JSON.
* **Feature Engineering (`build_textbook_full.py`):**
    * Extrapolated **Points Per Game (PPG)** and **Points Allowed** for every team since 1999.
    * Calculated simple home/away splits.
* **Prompt Structure:** Inputs were limited to: *"Team A (24.5 PPG) vs Team B (21.0 PPG)."*

#### Phase 2: The Efficiency Engine (V2)
* **Goal:** Move beyond results (Points) to process (Efficiency).
* **Ingestion (`build_advanced_stats_db.py`):**
    * Connected directly to the **nflverse** repository to download play-by-play data (1999–2025).
* **Feature Engineering:**
    * Aggregated millions of raw plays into game-level advanced stats.
    * **Key Metrics:** **EPA/Play** (Expected Points Added), **Success Rate %**, and **Dropback/Rush Efficiency**.
* **Limitation:** The pipeline only calculated *Offensive* efficiency, ignoring the opponent's defensive metrics.

#### Phase 3: The Context Engine (V3)
* **Goal:** Create a full "Matchup Vector" that accounts for both sides of the ball.
* **Ingestion (`build_advanced_stats_v3.py`):**
    * Upgraded the V2 script to pull **Defensive EPA Allowed**, **Defensive Success Rate**, and **Defensive Dropback EPA**.
* **Dataset Construction (`build_textbook_v3.py`):**
    * The core logic engine. It iterates through 7,500+ historical games.
    * Looks up the *prior* rolling average stats for both teams (Offense vs. Defense).
    * Constructs a complex "Prompt/Response" pair to teach the model how specific defenses neutralize specific offenses.

### B. The AI Models (Vertex AI)
* **Training Method:** Supervised Fine-Tuning (SFT) on 7,000+ historical examples.
* **Format Adaptation (`convert_to_vertex.py`):** A custom adapter that transforms our raw JSONL datasets into the strict multi-turn chat format required by Google Vertex AI.
* **Inference Strategy:**
    * **Deterministic Output:** The models are instructed to act as statistical engines, not chatbots.
    * **Tool Use (V3 Only):** V3 is equipped with Google Search to verify *active* injury reports in real-time before making a prediction.

---

## 3. System Instructions (Prompt Engineering)

The "brain" of the project lies in how we instruct the AI to process the data. The prompt evolved significantly from V1 to V3.

#### V1 Prompt (The Basic)
> "You are a specialized NFL prediction engine. Your ONLY function is to receive a 'Pre-Game Stats' block (PPG) and output a predicted winner. Do not use outside knowledge."

#### V3 Prompt (The Advanced)
> "You are an advanced NFL analytics engine trained on 25 years of `nflfastr` data. Your PRIMARY function is to analyze the conflict between **Offensive EPA** and **Defensive EPA Allowed**.
>
> **Secondary Function:** Use Google Search to identify *active* roster changes.
> * **Smart Injury Logic:** Only adjust scores for *new* injuries to key starters (QB, WR1). Ignore long-term IR players (already in the stats).
> * **Output:** Winner: [TEAM], Final Score: [TEAM] [SCORE], [TEAM] [SCORE]"

---

## 4. Key Performance Insights

We benchmarked the models against top ESPN/NFL analysts (Maldonado, Moody, Walder, Filice) over Weeks 11, 12, and 13.

### Insight 1: Offense vs. Defense (Week 12)
When we transitioned from V1 (PPG) to V2 (Offensive EPA only), accuracy actually **dropped**.
* **The Finding:** V2 became a "Glass Cannon." It would predict massive scores for good offenses, failing to realize they were playing elite defenses.
* **The Lesson:** "Smart" stats (EPA) are useless without context. This necessitated the build of V3.

![Sensitivity Analysis V1 vs V2](sensitivity_analysis_v1_vs_v2.png)

> **Observation:** V1 (Green) consistently outperformed V2 (Red) in Week 12, proving that offensive efficiency alone cannot predict game outcomes without defensive context.

### Insight 2: The Breakout (Week 13)
In Week 13, both V2 and V3 significantly outperformed human analysts in sensitivity analysis (error tolerance).

![Sensitivity Analysis V3](sensitivity_analysis_v1_vs_v2_vs_v3.png)

* **V2 Performance:** Won the week with **11 correct picks (69%)**. It capitalized on a week dominated by high-scoring offensive showcases.
* **V3 Performance:** Achieved **10 correct picks (63%)** but had a **lower Average Error** than V2.
* **The Takeaway:** V3 is the "safer" model. It didn't spike as high as V2 on raw wins this specific week, but its understanding of defense prevented it from making massive blowout prediction errors, keeping its spread differential tighter.

### Insight 3: Model Drift
Longitudinal analysis of V1 (Weeks 11-13) showed a steady regression in accuracy.

![V1 Longitudinal Analysis](ai_v1_sensitivity_analysis.png)

* **The Finding:** Simple "Points Per Game" averages lose predictive power late in the season as injuries mount and schemes change. This validates the need for the V3 approach (Search + Specific Matchup Stats) to maintain accuracy into the playoffs.

---

## 5. Conclusion & Future Scope

**Final Verdict:**
While **V2** (Offense-Only) can occasionally outperform on high-scoring weeks, **V3** (Full Context) represents the most robust architecture for long-term success. It balances the explosiveness of offensive efficiency with the reality of defensive resistance and real-time injury news.

**Future Improvements:**
* **DVOA Integration:** Incorporating opponent-adjusted metrics for even deeper context.
* **Live Betting Lines:** Using Vegas spread movement as the "population's sentiment." It is another factor that the AI can take into account to increase accuracy.
