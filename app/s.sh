#!/bin/sh
FILENAME=$1
DIR=$(dirname $FILENAME)

gcc $FILENAME -o $DIR/binary_file -lm -O2
compilation=$?

if [ $compilation -eq 0 ]; then
    for input_file in $DIR/*.in; do
        output_file="${input_file/.in/.out}"
        $DIR/binary_file < "$input_file" > "$output_file"
    done
else
    echo "ce" > $DIR/errors.log
fi