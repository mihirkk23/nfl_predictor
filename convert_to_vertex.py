import json

# --- CONFIGURATION ---
INPUT_FILE = 'gemma_textbook_full_1998_present.jsonl'
OUTPUT_FILE = 'vertex_gemini_training_data.jsonl'

print(f"Converting {INPUT_FILE} to Vertex AI format...")
print("This will be very fast.")

converted_count = 0
# Open the file you just made
with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
     open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
    
    for line in infile:
        try:
            # 1. Read your current line
            data = json.loads(line)
            
            # 2. Extract your data
            user_prompt = data['text_input']
            model_response = data['output']
            
            # 3. Re-package it into the new "Chat" format
            new_entry = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user_prompt}]
                    },
                    {
                        "role": "model",
                        "parts": [{"text": model_response}]
                    }
                ]
            }
            
            # 4. Write the new line to the new file
            outfile.write(json.dumps(new_entry) + '\n')
            converted_count += 1
            
        except Exception as e:
            print(f"Skipping broken line: {e}")

print(f"\n--- CONVERSION COMPLETE ---")
print(f"Successfully converted {converted_count} examples.")
print(f"You are ready to upload this file: {OUTPUT_FILE}")