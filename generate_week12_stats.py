import pandas as pd

# --- CONFIGURATION ---
INPUT_FILE = "MasterData_Week12.csv"  # Make sure this matches your file name
THRESHOLD_FOR_BAR_CHART = 10          # The arbitrary line for the bar chart

try:
    df = pd.read_csv(INPUT_FILE)
    
    # 1. FIND COLUMNS (Auto-detect names if they are slightly different)
    # We look for keywords like "Average" for error and "Winner" for the yes/no
    error_col = [c for c in df.columns if "Average" in c][0]
    winner_col = [c for c in df.columns if "Winner" in c][0]
    analyst_col = [c for c in df.columns if "Analyst" in c][0]
    
    print(f"Processing data for: {df[analyst_col].unique()}")

    # 2. CLEAN DATA
    # Convert "YES" to 1 and "NO" to 0
    df['Winner_Numeric'] = df[winner_col].apply(lambda x: 1 if str(x).upper().strip() == 'YES' else 0)
    # Force error to be a number
    df['Error_Numeric'] = pd.to_numeric(df[error_col], errors='coerce')

    # --- OUTPUT 1: SENSITIVITY CHART DATA (0-25) ---
    analysts = df[analyst_col].unique()
    sensitivity_data = {'Threshold': range(26)} # 0 to 25
    
    for analyst in analysts:
        scores = []
        subset = df[df[analyst_col] == analyst]
        winner_points = subset['Winner_Numeric'].sum()
        
        for t in range(26):
            accuracy_points = subset[subset['Error_Numeric'] < t].shape[0]
            scores.append(winner_points + accuracy_points)
        
        sensitivity_data[analyst] = scores
    
    pd.DataFrame(sensitivity_data).to_csv("graph_data_sensitivity.csv", index=False)
    print("✅ Created 'graph_data_sensitivity.csv'")

    # --- OUTPUT 2: SCORE COMPOSITION (Stacked Bar) ---
    comp_data = []
    for analyst in analysts:
        subset = df[df[analyst_col] == analyst]
        winner_pts = subset['Winner_Numeric'].sum()
        acc_pts = subset[subset['Error_Numeric'] < THRESHOLD_FOR_BAR_CHART].shape[0]
        
        comp_data.append({
            'Analyst': analyst,
            'Winner Points': winner_pts,
            'Accuracy Points': acc_pts
        })
        
    pd.DataFrame(comp_data).to_csv("graph_data_composition.csv", index=False)
    print("✅ Created 'graph_data_composition.csv'")

    # --- OUTPUT 3: SIMPLE STATS (Win Rate & Avg Error) ---
    # This is for your "Average Error" and "Win %" bar charts
    stats = df.groupby(analyst_col).agg(
        Win_Rate=('Winner_Numeric', 'mean'),
        Avg_Error=('Error_Numeric', 'mean')
    ).reset_index()
    
    stats.to_csv("graph_data_simple_stats.csv", index=False)
    print("✅ Created 'graph_data_simple_stats.csv'")

except Exception as e:
    print(f"❌ Error: {e}")