#!/bin/sh
FILENAME=$1
TIME_LIMIT=$2
MEM_KB=$3
DIR=$(dirname "$FILENAME")

# Компиляция со своим таймаутом. Ulimit'ы ниже на gcc НЕ действуют —
# они выставляются после, поэтому лимит памяти задачи компилятор не душит.
if ! timeout 10 gcc "$FILENAME" -o "$DIR/binary_file" -lm -O2 2>"$DIR/compile.log"; then
    exit 1
fi

# Лимиты для запуска решений.
# -f: максимальный размер создаваемого файла, в блоках по 512 байт.
#     10240 блоков = 5 МиБ. Процесс, превысивший лимит, получает SIGXFSZ (exit 153).
ulimit -f 10240
# -v: потолок виртуальной памяти процесса, в КБ. Дублирует контейнерный лимит,
#     но срабатывает per-process и детерминированно.
if [ -n "$MEM_KB" ] && [ "$MEM_KB" -gt 0 ] 2>/dev/null; then
    ulimit -v "$MEM_KB"
fi

for input_file in "$DIR"/*.in; do
    # если тестов нет, глоб не раскрывается и в цикл попадает literal "*.in"
    [ -e "$input_file" ] || continue

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

exit 0