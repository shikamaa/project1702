#!/bin/sh
FILENAME=$1
TIME_LIMIT=$2
DIR=$(dirname "$FILENAME")

if ! gcc "$FILENAME" -o "$DIR/binary_file" -lm -O2 2>"$DIR/compile.log"; then
    exit 1
fi

for input_file in "$DIR"/*.in; do
    test_name=$(basename "$input_file" .in)
    out_file="$DIR/${test_name}.out"
    mem_file="$DIR/${test_name}.mem"

    /usr/bin/time -f "%M" -o "$mem_file" \
        timeout "$TIME_LIMIT" \
        "$DIR/binary_file" < "$input_file" > "$out_file" 2>/dev/null
    
    exit_code=$?
    max_mem=$(grep -m1 '^[0-9]*$' "$mem_file" 2>/dev/null || echo "0")
    
    echo "${test_name},${exit_code},${max_mem}" >> "$DIR/results.csv"
done