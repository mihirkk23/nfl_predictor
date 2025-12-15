import json
import os
import numpy as np 

# --- 1. CONFIGURATION ---

JSON_GAME_FOLDER = 'C:/Users/INSERT_FOLDER_LOCATION_HERE'
OUTPUT_TEXTBOOK_FILE = 'gemma_textbook_full_1998_present.jsonl'


# --- 2. HELPER FUNCTIONS ---

def parse_format_old(game_data, filename):
    """Parses the 'old' format (e.g., 1999_05_NE_KC.json)"""
    try:
        game_id = list(game_data.keys())[0]
        game_content = game_data[game_id]
        
        home_team = game_content['home']['abbr']
        away_team = game_content['away']['abbr']
        home_score = game_content['home']['score']['T']
        away_score = game_content['away']['score']['T']
        
        # --- ADDED WEATHER BACK ---
        weather = game_content.get('weather', 'N/A')
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'weather': weather if weather is not None else "N/A" # Handle null weather
        }
    except Exception as e:
        print(f"  SKIPPING (Old Format Error): File {filename} had error: {e}")
        return None

def parse_format_new(game_data, filename):
    """Parses the 'new' format (e.g., 2021_02_LA_IND.json)"""
    try:
        game_detail = game_data['data']['viewer']['gameDetail']
        
        home_team = game_detail['homeTeam']['abbreviation']
        away_team = game_detail['visitorTeam']['abbreviation']
        home_score = game_detail['homePointsTotal']
        away_score = game_detail['visitorPointsTotal']
        
        # --- ADDED WEATHER BACK ---
        # Try to get weather, default to N/A if any key is missing
        weather = "N/A"
        if 'weather' in game_detail and game_detail['weather'] is not None:
            weather = game_detail['weather'].get('shortDescription', 'N/A')
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'weather': weather if weather is not None else "N/A"
        }
    except Exception as e:
        print(f"  SKIPPING (New Format Error): File {filename} had error: {e}")
        return None

def load_and_parse_all_games(folder_path):
    """
    Loads all 8,000+ JSON files, checks their format, and
    parses them to get consistent data: scores and weather.
    """
    print("Loading and parsing all 8,000+ game files into memory...")
    all_games_data = []
    
    for filename in os.listdir(folder_path):
        if not filename.endswith('.json'):
            continue
            
        file_path = os.path.join(folder_path, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
            
            if not file_content:
                print(f"  SKIPPING: File {filename} is empty.")
                continue
                
            game_data = json.loads(file_content)

            if not game_data or not isinstance(game_data, dict):
                print(f"  SKIPPING: File {filename} is not valid JSON.")
                continue

            if 'data' in game_data: # This is the "New Format"
                parsed_data = parse_format_new(game_data, filename)
            else: # This is the "Old Format"
                parsed_data = parse_format_old(game_data, filename)
            
            if not parsed_data:
                continue 
            
            parts = filename.replace('.json', '').split('_')
            season = int(parts[0])
            week = int(parts[1])

            game_obj = {
                'filename': filename,
                'season': season,
                'week': week,
                'home_team': parsed_data['home_team'],
                'away_team': parsed_data['away_team'],
                'home_score': parsed_data['home_score'],
                'away_score': parsed_data['away_score'],
                'weather': parsed_data['weather'] # Add weather to the object
            }
            all_games_data.append(game_obj)
            
        except Exception as e:
            print(f"CRITICAL SKIP: Error parsing {filename}. The specific error is: {e}")
            
    print(f"Successfully loaded and parsed {len(all_games_data)} game files.")
    return sorted(all_games_data, key=lambda g: (g['season'], g['week']))

def get_team_stats(stats_db, team, season, week):
    """
    The core "look-back" logic. Calculates *only* avg PPG.
    """
    if week <= 4:
        season_to_use = season - 1
    else:
        season_to_use = season

    team_stats = stats_db.get(season_to_use, {}).get(team, [])
    
    if not team_stats:
        return { "ppg": "N/A", "games_played": 0 }

    ppg = np.mean([s['points_scored'] for s in team_stats])
    
    return {
        "ppg": f"{ppg:.1f}",
        "games_played": len(team_stats)
    }

def update_stats_db(stats_db, game):
    """Adds the game that just "finished" to our stats database."""
    season = game['season']
    
    home_team = game['home_team']
    home_stats = { 'points_scored': game['home_score'] }
    stats_db.setdefault(season, {}).setdefault(home_team, []).append(home_stats)
    
    away_team = game['away_team']
    away_stats = { 'points_scored': game['away_score'] }
    stats_db.setdefault(season, {}).setdefault(away_team, []).append(away_stats)


# --- 3. MAIN EXECUTION ---

def main():
    stats_database = {}
    sorted_games = load_and_parse_all_games(JSON_GAME_FOLDER)
    
    print(f"Starting 'textbook' build for {len(sorted_games)} games...")
    games_written = 0
    games_skipped = 0
    
    with open(OUTPUT_TEXTBOOK_FILE, 'w', encoding='utf-8') as textbook:
        for game in sorted_games:
            
            home_stats = get_team_stats(stats_database, game['home_team'], game['season'], game['week'])
            away_stats = get_team_stats(stats_database, game['away_team'], game['season'], game['week'])

            if home_stats['games_played'] == 0 or away_stats['games_played'] == 0:
                games_skipped += 1
                update_stats_db(stats_database, game)
                continue 
            
            # --- !!! PROMPT UPDATED WITH WEATHER !!! ---
            text_input = f"""
Predict the final score for the upcoming game: {game['home_team']} (Home) vs. {game['away_team']} (Away).

### Pre-Game Stats
* **{game['home_team']} (Home):**
    Games Played: {home_stats['games_played']}
    PPG: {home_stats['ppg']}

* **{game['away_team']} (Away):**
    Games Played: {away_stats['games_played']}
    PPG: {away_stats['ppg']}

### Game Context
* Location: {game['home_team']} (Home)
* Weather: {game['weather']}
"""
            
            winner = game['home_team'] if game['home_score'] > game['away_score'] else game['away_team']
            score_string = f"{game['home_team']} {game['home_score']}, {game['away_team']} {game['away_score']}"
            
            output = { "winner": winner, "final_score": score_string }
            
            training_example = {
                "text_input": text_input.strip(),
                "output": json.dumps(output)
            }
            textbook.write(json.dumps(training_example) + '\n')
            games_written += 1
            
            update_stats_db(stats_database, game)
        
    print(f"\n--- FACTORY RUN COMPLETE ---")
    print(f"Successfully wrote {games_written} high-quality training examples.")
    print(f"Skipped {games_skipped} games (e.g., Week 1s or early season).")
    print(f"Your 'textbook' is ready: {OUTPUT_TEXTBOOK_FILE}")

if __name__ == "__main__":

    main()
