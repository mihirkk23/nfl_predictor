# --- 1. CONFIGURATION ---
# R will learn these variables first

base_data_directory <- "C:/Users/sidha/nfl-pbp-data"
json_output_directory <- "C:/Users/sidha/nfl_json_output"


# --- 2. INSTALL 'jsonlite' IF YOU DON'T HAVE IT ---
if (!require("jsonlite")) {
  install.packages("jsonlite")
  library(jsonlite)
}

# --- 3. THE CONVERSION SCRIPT ---
# Now R will know what the variables in this section mean

# This finds ALL .rds files in all subfolders
all_rds_files <- list.files(
  path = base_data_directory,
  pattern = "\\.rds$",  # This looks for files ending in .rds
  recursive = TRUE,     # This searches all subfolders
  full.names = TRUE     # This gets the full file path
)

print(paste("Found", length(all_rds_files), "RDS files. Starting conversion..."))

# Loop through every single .rds file path
for (rds_file_path in all_rds_files) {
  
  tryCatch({
    
    # --- Read the .rds file ---
    game_data <- readRDS(rds_file_path)
    
    # --- Create the new .json file name and path ---
    base_filename <- basename(rds_file_path) 
    json_filename <- sub("\\.rds$", ".json", base_filename) 
    
    # This line is where your error happened, but now it will work
    json_file_path <- file.path(json_output_directory, json_filename)
    
    # --- Write the data to a new .json file ---
    write_json(game_data, json_file_path, auto_unbox = TRUE)
    
    print(paste("SUCCESS: Converted", base_filename, "to JSON"))
    
  }, error = function(e) {
    print(paste("ERROR: Failed to convert", rds_file_path, ":", e$message))
  })
}

print("--- CONVERSION COMPLETE ---")
print(paste("All JSON files are in:", json_output_directory))