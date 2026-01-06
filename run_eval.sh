#!/bin/bash

# Usage: bash run_eval.sh ./pdfs ./outputs
INPUT_DIR=$1
OUTPUT_DIR=$2
API_URL="http://localhost:8000"

mkdir -p "$OUTPUT_DIR"

echo "Launching Parallel Evaluation..."

process_pdf() {
    local file=$1
    local filename=$(basename "$file")
    
    # 1. Ingest
    job_id=$(curl -s -X POST "$API_URL/ingest" -F "file=@$file" | jq -r '.job_id')
    
    if [[ "$job_id" == "null" || -z "$job_id" ]]; then
        echo "[ERROR] $filename: Ingestion failed."
        return
    fi

    # 2. Poll
    while true; do
        # Fetch the result
        full_resp=$(curl -s "$API_URL/result/$job_id")
        
        # Check status
        status=$(echo "$full_resp" | jq -r '.status')

        if [[ "$status" == "completed" ]]; then
            # Save the 'data' object (which contains our final_output)
            echo "$full_resp" | jq '.data' > "$OUTPUT_DIR/${filename%.pdf}.json"
            
            # Extract time from the 'data' field
            # In main.py, final_output is returned inside the 'data' key
            p_time=$(echo "$full_resp" | jq -r '.data.processing_time_sec')
            
            if [[ "$p_time" == "null" ]]; then
                echo "[!] $filename: Done (Time returned null)"
            else
                echo "[✓] $filename: Done in ${p_time}s"
            fi
            break
        fi
        sleep 3
    done
}

# Run all in parallel
for file in "$INPUT_DIR"/*.pdf; do
    process_pdf "$file" &
done

wait
echo "------------------------------------------------"
echo "All PDFs processed. Results in $OUTPUT_DIR"