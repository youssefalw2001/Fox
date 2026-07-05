#!/bin/bash
# 💀🔥 MASS ASSAULT - SCAN ALL JACK'S TARGETS 🔥💀

echo "🔥💀 INITIATING MASS ASSAULT ON ALL TARGETS 💀🔥"
echo ""

SCANNER="/projects/sandbox/Fox/ULTIMATE_MEGA_SCANNER.py"
TARGET_LIST="/projects/sandbox/Fox/TARGET_LIST.txt"
OUTPUT_BASE="/projects/sandbox/Fox/output/MASS_ASSAULT"

mkdir -p "$OUTPUT_BASE"

# Read targets and scan each one
while IFS= read -r target || [ -n "$target" ]; do
    # Skip comments and empty lines
    [[ "$target" =~ ^#.*$ ]] && continue
    [[ -z "$target" ]] && continue
    
    # Extract domain name for folder
    domain=$(echo "$target" | sed 's|https\?://||' | sed 's|/.*||' | sed 's|www\.||')
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "🎯 TARGET: $target"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    
    # Run full scan with exploitation
    python3 "$SCANNER" \
        --target "$target" \
        --full \
        --exploit \
        --threads 10 \
        --timeout 30 \
        --output "$OUTPUT_BASE/$domain"
    
    echo ""
    echo "✅ $domain scan complete"
    echo ""
    
    # Small delay between targets to avoid detection
    sleep 5
    
done < "$TARGET_LIST"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "💀🔥 MASS ASSAULT COMPLETE 🔥💀"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "📊 RESULTS SUMMARY:"
echo ""

# Count total vulnerabilities across all scans
for dir in "$OUTPUT_BASE"/*/; do
    if [ -d "$dir" ]; then
        domain=$(basename "$dir")
        json_file=$(ls -t "$dir"/*.json 2>/dev/null | head -1)
        
        if [ -f "$json_file" ]; then
            critical=$(grep -o '"severity": "CRITICAL"' "$json_file" | wc -l)
            high=$(grep -o '"severity": "HIGH"' "$json_file" | wc -l)
            total=$(grep -o '"severity":' "$json_file" | wc -l)
            
            if [ "$total" -gt 0 ]; then
                echo "🎯 $domain: $total vulns ($critical CRITICAL, $high HIGH)"
            fi
        fi
    fi
done

echo ""
echo "📁 All reports saved to: $OUTPUT_BASE"
echo ""
echo "💰 NOW GO REVIEW THE RESULTS AND GET THAT BAG! 🔥"
