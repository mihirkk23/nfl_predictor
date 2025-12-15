import pandas as pd
import os

# --- CONFIGURATION ---
START_YEAR = 1999
END_YEAR = 2025
OUTPUT_FILE = 'rbsdm_stats_v3_off_def.csv'

BASE_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{}.csv"

def calculate_advanced_stats(df):
    """
    Aggregates play-by-play data into game-level stats for BOTH Offense and Defense.
    """
    # Filter for real plays
    mask = (df['play_type'].isin(['pass', 'run'])) & (df['epa'].notna())
    plays = df[mask].copy()
    
    if 'success' not in plays.columns:
        plays['success'] = (plays['epa'] > 0).astype(int)

    # --- 1. OFFENSIVE STATS (Group by 'posteam') ---
    offense = plays.groupby(['season', 'week', 'game_id', 'posteam']).agg(
        off_epa=('epa', 'mean'),
        off_success=('success', 'mean'),
        off_dropback_epa=('epa', lambda x: x[plays.loc[x.index, 'play_type'] == 'pass'].mean()),
        off_rush_epa=('epa', lambda x: x[plays.loc[x.index, 'play_type'] == 'run'].mean())
    ).reset_index().rename(columns={'posteam': 'team'})

    # --- 2. DEFENSIVE STATS (Group by 'defteam') ---
    defense = plays.groupby(['season', 'week', 'game_id', 'defteam']).agg(
        def_epa=('epa', 'mean'),
        def_success=('success', 'mean'),
        def_dropback_epa=('epa', lambda x: x[plays.loc[x.index, 'play_type'] == 'pass'].mean()),
        def_rush_epa=('epa', lambda x: x[plays.loc[x.index, 'play_type'] == 'run'].mean())
    ).reset_index().rename(columns={'defteam': 'team'})

    # --- 3. MERGE THEM ---
    # Combine so each row is: Week 1, Chiefs, Off_Stats, Def_Stats
    full_stats = pd.merge(offense, defense, on=['season', 'week', 'game_id', 'team'])
    
    return full_stats

# --- MAIN LOOP ---
all_seasons_data = []
print(f"Starting V3 download ({START_YEAR}-{END_YEAR})...")

for year in range(START_YEAR, END_YEAR + 1):
    print(f"Processing {year}...", end=" ", flush=True)
    try:
        df = pd.read_csv(BASE_URL.format(year), low_memory=False)
        season_stats = calculate_advanced_stats(df)
        all_seasons_data.append(season_stats)
        print(f"Done! ({len(season_stats)} games)")
    except Exception as e:
        print(f"Error: {e}")

print("Combining all seasons...")
full_db = pd.concat(all_seasons_data, ignore_index=True)
full_db = full_db.sort_values(by=['season', 'week', 'game_id'])

full_db.to_csv(OUTPUT_FILE, index=False)
print(f"\n--- SUCCESS ---")
print(f"Saved V3 stats to {OUTPUT_FILE}")