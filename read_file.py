import sys
lines = open(sys.argv[1]).readlines()
print("\n".join(lines[int(sys.argv[2]):int(sys.argv[3])]))
