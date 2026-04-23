#!/bin/sh
FILENAME=$1

gcc $FILENAME -o /box/binary_file -lm -O2
compilation=$?

if [ $compilation -eq 0 ]; then
    for input_file in /box/*.in; do
        output_file="${input_file/.in/.out}"
        /box/binary_file < "$input_file" > "$output_file"
    done
else
    echo "ce" > /box/errors.log
fi