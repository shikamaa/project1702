#!/bin/sh
FILENAME=$1
DIR=$(dirname "$FILENAME")
TIME_LIMIT=2

gcc "$FILENAME" -o "$DIR/binary_file" -lm -O2 2>"$DIR/compile.log"
compilation=$?

if [ $compilation -ne 0 ]; then
    echo "CE" > "$DIR/verdict.log"
    exit 1
fi

for input_file in "$DIR"/*.in; do
    test_name=$(basename "$input_file" .in)
    out_file="$DIR/${test_name}.out"
    metrics_file="$DIR/${test_name}.metrics"

    { /usr/bin/time -v \
        timeout $TIME_LIMIT \
        "$DIR/binary_file" < "$input_file" > "$out_file"; } \
        2>"$metrics_file"

    echo "EXIT:$?" >> "$metrics_file"
done