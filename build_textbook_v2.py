import json
import os
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION ---
JSON_GAME_FOLDER = 'C:/Users/sidha/nfl_json_output'
STATS_CSV_FILE = 'rbsdm_style_stats_1999_2025.csv'
OUTPUT_TEXTBOOK_FILE = 'gemma_textbook_v2_advanced.jsonl'

# --- 2. LOAD THE KNOWLEDGE BASE ---
print(f"Loading advanced stats from {STATS_CSV_FILE}...")
try:
    # Load the CSV into a pandas DataFrame
    stats_df = pd.read_csv(STATS_CSV_FILE)
    # Create a unique ID for fast lookup: "1999_1_GB" (Season_Week_Team)
    stats_df['lookup_id'] = stats_df['season'].astype(str) + "_" + \
                            stats_df['week'].astype(str) + "_" + \
                            stats_df['team']
    # Convert to a dictionary for instant access
    STATS_DB = stats_df.set_index('lookup_id').to_dict('index')
    print(" Advanced stats loaded successfully!")
except Exception as e:
    print(f"CRITICAL ERROR: Could not load stats CSV. {e}")
    exit()

# --- 3. HELPER FUNCTIONS (The robust parsers you already have) ---

def parse_format_old(game_data, filename):
    try:
        game_id = list(game_data.keys())[0]
        game_content = game_data[game_id]
        home_team = game_content['home']['abbr']
        away_team = game_content['away']['abbr']
        home_score = game_content['home']['score']['T']
        away_score = game_content['away']['score']['T']
        weather = game_content.get('weather', 'N/A')
        return {'home': home_team, 'away': away_team, 'home_score': home_score, 'away_score': away_score, 'weather': weather}
    except: return None

def parse_format_new(game_data, filename):
    try:
        det = game_data['data']['viewer']['gameDetail']
        home_team = det['homeTeam']['abbreviation']
        away_team = det['visitorTeam']['abbreviation']
        home_score = det['homePointsTotal']
        away_score = det['visitorPointsTotal']
        weather = "N/A"
        if 'weather' in det and det['weather']: weather = det['weather'].get('shortDescription', 'N/A')
        return {'home': home_team, 'away': away_team, 'home_score': home_score, 'away_score': away_score, 'weather': weather}
    except: return None

def get_team_advanced_stats(team, season, week):
    """
    Looks up the team's stats from the PREVIOUS week.
    If it's Week 5, we want their stats from Week 4 (or average of W1-4).
    
    For simplicity and speed in V2, we will take the 'rolling average' 
    of the team's stats from the current season up to this point.
    """
    # If Week 1, use previous season's average (if available) or skips
    target_season = season
    target_weeks = [w for w in range(1, week)] # Weeks 1 to (Current-1)
    
    if week <= 1:
        target_season = season - 1
        target_weeks = [w for w in range(1, 18)] # Full previous season

    # Gather stats for all prior weeks
    epas = []
    success_rates = []
    dropback_epas = []
    rush_epas = []

    for w in target_weeks:
        lookup_id = f"{target_season}_{w}_{team}"
        if lookup_id in STATS_DB:
            data = STATS_DB[lookup_id]
            epas.append(data['epa_per_play'])
            success_rates.append(data['success_rate'])
            dropback_epas.append(data['dropback_epa'])
            rush_epas.append(data['rush_epa'])
            
    if not epas:
        return None # No data found (e.g. Week 1 of 1999)

    # Calculate Averages
    return {
        "epa": f"{np.mean(epas):.3f}",
        "success_rate": f"{np.mean(success_rates)*100:.1f}%",
        "dropback_epa": f"{np.mean(dropback_epas):.3f}",
        "rush_epa": f"{np.mean(rush_epas):.3f}",
        "games_played": len(epas)
    }

# --- 4. MAIN FACTORY ---

print("Starting V2 Data Factory...")
games_written = 0

with open(OUTPUT_TEXTBOOK_FILE, 'w', encoding='utf-8') as outfile:
    
    for filename in os.listdir(JSON_GAME_FOLDER):
        if not filename.endswith('.json'): continue
        
        # --- A. Parse the Game (Who played?) ---
        file_path = os.path.join(JSON_GAME_FOLDER, filename)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
            if not content: continue
            data = json.loads(content)
            
            parsed = parse_format_new(data, filename) if 'data' in data else parse_format_old(data, filename)
            if not parsed: continue
            
            parts = filename.replace('.json', '').split('_')
            season, week = int(parts[0]), int(parts[1])
            
        except: continue

        # --- B. Get Advanced Stats (The Upgrade) ---
        home_stats = get_team_advanced_stats(parsed['home'], season, week)
        away_stats = get_team_advanced_stats(parsed['away'], season, week)

        if not home_stats or not away_stats:
            continue # Skip if we don't have advanced stats yet

        # --- C. Build the V2 Prompt ---
        text_input = f"""
Predict the final score for: {parsed['home']} (Home) vs. {parsed['away']} (Away).

### Advanced Pre-Game Stats (Season Average)
* **{parsed['home']} (Home):**
    EPA/Play: {home_stats['epa']}
    Success Rate: {home_stats['success_rate']}
    Dropback EPA: {home_stats['dropback_epa']}
    Rush EPA: {home_stats['rush_epa']}

* **{parsed['away']} (Away):**
    EPA/Play: {away_stats['epa']}
    Success Rate: {away_stats['success_rate']}
    Dropback EPA: {away_stats['dropback_epa']}
    Rush EPA: {away_stats['rush_epa']}

### Game Context
* Location: {parsed['home']} (Home)
* Weather: {parsed['weather']}
"""
        
        # --- D. The Answer ---
        winner = parsed['home'] if parsed['home_score'] > parsed['away_score'] else parsed['away']
        score_str = f"{parsed['home']} {parsed['home_score']}, {parsed['away']} {parsed['away_score']}"
        output_text = f"Winner: {winner}, Final Score: {score_str}"

        # --- E. Save ---
        entry = {"text_input": text_input.strip(), "output": output_text}
        outfile.write(json.dumps(entry) + '\n')
        games_written += 1

print(f"DONE! Created V2 Textbook with {games_written} examples.")