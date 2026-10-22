f=open("c:/Users/brett/AIProjects/ECAS_BETA/ecas/ui/main_window.py", encoding="utf-8")
content = f.read()
import sys
line_num = int(sys.argv[1]) if len(sys.argv) &gt; 1 else None
lines = content.split("\n")
if line_num is not None:
    print("=" * 80)
    start = max(0, line_num - 5)
    end = min(len(lines), line_num + 6)
    for i in range(start, end):
        print(f"Line {i+1}: {lines[i]}")
else:
    print(f"Total lines: {len(lines)}")
f.close()
