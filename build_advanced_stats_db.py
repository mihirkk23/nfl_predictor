import pandas as pd
import os

# --- CONFIGURATION ---
START_YEAR = 1999
END_YEAR = 2025
OUTPUT_FILE = 'rbsdm_style_stats_1999_2025.csv'

# The standard repo for pre-computed advanced stats
BASE_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{}.csv"

def calculate_advanced_stats(df):
    """
    Aggregates play-by-play data into game-level RBSDM style stats.
    """
    # Filter for relevant plays (pass or rush, not special teams/kneels)
    # rbsdm typically filters for: play_type is pass or run, and no penalties that void the play
    mask = (df['play_type'].isin(['pass', 'run'])) & (df['epa'].notna())
    plays = df[mask].copy()
    
    # Create 'success' column if it doesn't exist (nflfastr usually has it)
    # Success = EPA > 0
    if 'success' not in plays.columns:
        plays['success'] = (plays['epa'] > 0).astype(int)

    # --- GROUP BY GAME AND TEAM ---
    # We group by both 'posteam' (Offense) and 'defteam' (Defense) to get both sides
    
    # 1. OFFENSIVE STATS
    offense = plays.groupby(['season', 'week', 'game_id', 'posteam']).agg(
        n_plays=('epa', 'count'),
        epa_per_play=('epa', 'mean'),
        success_rate=('success', 'mean'),
        dropback_epa=('epa', lambda x: x[plays.loc[x.index, 'play_type'] == 'pass'].mean()),
        rush_epa=('epa', lambda x: x[plays.loc[x.index, 'play_type'] == 'run'].mean())
    ).reset_index().rename(columns={'posteam': 'team'})
    
    return offense

# --- MAIN LOOP ---
all_seasons_data = []

print(f"Starting download and processing for {START_YEAR}-{END_YEAR}...")

for year in range(START_YEAR, END_YEAR + 1):
    print(f"Processing {year}...", end=" ", flush=True)
    
    try:
        # 1. Download the data directly (pandas handles the URL)
        # low_memory=False avoids warnings on mixed types
        url = BASE_URL.format(year)
        df = pd.read_csv(url, low_memory=False)
        
        # 2. Calculate the stats
        season_stats = calculate_advanced_stats(df)
        all_seasons_data.append(season_stats)
        
        print(f"Done! ({len(season_stats)} team-games)")
        
    except Exception as e:
        print(f"Error: {e}")

# --- FINALIZE ---
print("Combining all seasons...")
full_db = pd.concat(all_seasons_data, ignore_index=True)

# Sort for cleanliness
full_db = full_db.sort_values(by=['season', 'week', 'game_id'])

# Save to CSV
full_db.to_csv(OUTPUT_FILE, index=False)

print(f"\n--- SUCCESS ---")
print(f"Saved {len(full_db)} rows of advanced stats to {OUTPUT_FILE}")
print("Columns included: Season, Week, Team, EPA/play, Success Rate, Dropback EPA, Rush EPA")