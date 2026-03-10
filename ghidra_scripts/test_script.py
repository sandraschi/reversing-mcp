print("Can you hear me now?")
import os

cwd = os.getcwd()
print(f"PropCWD: {cwd}")
with open("HELLO_GHIDRA.txt", "w") as f:
    f.write(f"Hello from Ghidra! CWD is {cwd}")
