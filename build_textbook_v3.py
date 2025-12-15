import json
import os
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION ---
JSON_GAME_FOLDER = 'C:/Users/sidha/nfl_json_output'
STATS_CSV_FILE = 'rbsdm_stats_v3_off_def.csv'
OUTPUT_TEXTBOOK_FILE = 'gemma_textbook_v3_full_context.jsonl'

# --- 2. LOAD THE KNOWLEDGE BASE ---
print(f"Loading V3 stats from {STATS_CSV_FILE}...")
try:
    stats_df = pd.read_csv(STATS_CSV_FILE)
    # Create lookup ID: Season_Week_Team
    stats_df['lookup_id'] = stats_df['season'].astype(str) + "_" + \
                            stats_df['week'].astype(str) + "_" + \
                            stats_df['team']
    # Load into dictionary for instant access
    STATS_DB = stats_df.set_index('lookup_id').to_dict('index')
    print("Knowledge Base loaded successfully!")
except Exception as e:
    print(f"CRITICAL ERROR: Could not load stats CSV. {e}")
    exit()

# --- 3. HELPER FUNCTIONS ---

def parse_format_old(game_data, filename):
    try:
        game_id = list(game_data.keys())[0]
        c = game_data[game_id]
        # Returns 'home_team' (Consistent naming)
        return {
            'home_team': c['home']['abbr'], 
            'away_team': c['away']['abbr'], 
            'home_score': c['home']['score']['T'], 
            'away_score': c['away']['score']['T'], 
            'weather': c.get('weather', 'N/A')
        }
    except: return None

def parse_format_new(game_data, filename):
    try:
        d = game_data['data']['viewer']['gameDetail']
        w = "N/A"
        if 'weather' in d and d['weather']: w = d['weather'].get('shortDescription', 'N/A')
        # Returns 'home_team' (Consistent naming)
        return {
            'home_team': d['homeTeam']['abbreviation'], 
            'away_team': d['visitorTeam']['abbreviation'], 
            'home_score': d['homePointsTotal'], 
            'away_score': d['visitorPointsTotal'], 
            'weather': w
        }
    except: return None

def get_team_rolling_stats(team, season, week, stats_db):
    """
    Calculates rolling average for OFFENSE and DEFENSE stats.
    """
    target_season = season
    target_weeks = [w for w in range(1, week)]
    
    if week <= 1:
        target_season = season - 1
        target_weeks = [w for w in range(1, 18)]

    metrics = {
        'off_epa': [], 'off_success': [], 'off_dropback': [], 'off_rush': [],
        'def_epa': [], 'def_success': [], 'def_dropback': [], 'def_rush': []
    }

    found_games = 0
    for w in target_weeks:
        lookup_id = f"{target_season}_{w}_{team}"
        if lookup_id in stats_db:
            data = stats_db[lookup_id]
            for key in metrics:
                # Only add if the key exists in the CSV data
                if key in data:
                    metrics[key].append(data[key])
            found_games += 1
            
    if found_games == 0: return None

    # Calculate averages safely
    return {k: np.mean(v) for k, v in metrics.items() if v}

# --- 4. MAIN FACTORY ---

def main():
    print("Starting V3 Data Factory...")
    games_written = 0

    with open(OUTPUT_TEXTBOOK_FILE, 'w', encoding='utf-8') as outfile:
        
        for filename in os.listdir(JSON_GAME_FOLDER):
            if not filename.endswith('.json'): continue
            
            file_path = os.path.join(JSON_GAME_FOLDER, filename)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
                if not content: continue
                data = json.loads(content)
                
                # Choose the correct parser
                if 'data' in data:
                    parsed = parse_format_new(data, filename)
                else:
                    parsed = parse_format_old(data, filename)
                
                if not parsed: continue
                
                parts = filename.replace('.json', '').split('_')
                season, week = int(parts[0]), int(parts[1])
            except: continue

            # --- LOOKUP STATS ---
            # Use 'home_team' here to match the parser!
            home_stats = get_team_rolling_stats(parsed['home_team'], season, week, STATS_DB)
            away_stats = get_team_rolling_stats(parsed['away_team'], season, week, STATS_DB)

            if not home_stats or not away_stats: continue

            # --- BUILD PROMPT ---
            text_input = f"""
Predict the final score for: {parsed['home_team']} (Home) vs. {parsed['away_team']} (Away).

### {parsed['home_team']} Stats (Season Avg)
* **OFFENSE:** EPA/Play: {home_stats.get('off_epa', 0):.3f}, Success Rate: {home_stats.get('off_success', 0):.1%}, Dropback EPA: {home_stats.get('off_dropback', 0):.3f}, Rush EPA: {home_stats.get('off_rush', 0):.3f}
* **DEFENSE:** EPA/Play Allowed: {home_stats.get('def_epa', 0):.3f}, Success Rate Allowed: {home_stats.get('def_success', 0):.1%}, Dropback EPA Allowed: {home_stats.get('def_dropback', 0):.3f}, Rush EPA Allowed: {home_stats.get('def_rush', 0):.3f}

### {parsed['away_team']} Stats (Season Avg)
* **OFFENSE:** EPA/Play: {away_stats.get('off_epa', 0):.3f}, Success Rate: {away_stats.get('off_success', 0):.1%}, Dropback EPA: {away_stats.get('off_dropback', 0):.3f}, Rush EPA: {away_stats.get('off_rush', 0):.3f}
* **DEFENSE:** EPA/Play Allowed: {away_stats.get('def_epa', 0):.3f}, Success Rate Allowed: {away_stats.get('def_success', 0):.1%}, Dropback EPA Allowed: {away_stats.get('def_dropback', 0):.3f}, Rush EPA Allowed: {away_stats.get('def_rush', 0):.3f}

### Game Context
* Location: {parsed['home_team']} (Home)
* Weather: {parsed['weather']}
"""
            
            # --- CLEAN OUTPUT ---
            winner = parsed['home_team'] if parsed['home_score'] > parsed['away_score'] else parsed['away_team']
            score_str = f"{parsed['home_team']} {parsed['home_score']}, {parsed['away_team']} {parsed['away_score']}"
            output_text = f"Winner: {winner}, Final Score: {score_str}"

            entry = {"text_input": text_input.strip(), "output": output_text}
            outfile.write(json.dumps(entry) + '\n')
            games_written += 1

    print(f"DONE! Created V3 Textbook with {games_written} examples.")

if __name__ == "__main__":
    main()