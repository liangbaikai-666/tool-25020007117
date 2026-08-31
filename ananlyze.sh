#!/bin/bash
# analyze.sh — 统计 5xx 最多的前 2 个 path 与平均 latency_ms

# 1. 参数检查: 无参数则 stderr 提示并退出
if [ $# -eq 0 ]; then
    echo "error:please give a path of .csv as augument">&2
    exit 1
fi

# 2. 文件存在性检查
csv_file="$1"
if test ! -f "$csv_file" ; then
   echo "error:file '$csv_file'not exist." >&2
   exit 1
fi

# 3) 5xx 次数最多的前 2 个 path (次数降序, 相同按 path 字典序)
echo "=== HTTP 5xx nums  1st and 2ed of paths ==="
tail -n +2 "$csv_file"          |   # 跳过表头
awk -F, '$4 >= 500 && $4 < 600 {print $3}' |   # 筛选 5xx, 输出 path
sort | uniq -c                  |   # 计数
sort -k1,1nr -k2,2              |   # 次数降序, 同则 path 升序
head -n 2

echo " "

# 4) 全部数据行的平均 latency_ms (跳过表头, 保留两位小数)
echo "=== all average latency_ms of data lines ==="
tail -n +2 "$csv_file"          |
awk -F, '{ sum += $5; count++ } END { printf "%.2f\n", sum / count }'