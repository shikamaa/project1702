FILE_PATH=$1

if [ -z "$FILE_PATH" ]; then
  echo "No file path provided."
  exit 1
fi

BASENAME=$(basename "$FILE_PATH" .c)
OUTPUT="/uploads/${BASENAME}_out"

echo "Compiling $FILE_PATH..."
gcc "$FILE_PATH" -o "$OUTPUT" 2>"/uploads/${BASENAME}_compile.log"

if [ $? -eq 0 ]; then
  echo "Compiled successfully."
  echo "Running program..."
  "$OUTPUT" >"/uploads/${BASENAME}_run.log" 2>&1
  echo "Done."
else
  echo "Compilation failed. See log: ${BASENAME}_compile.log"
fi