import os

# Searches folders for "Transients" type scans.

# fpath = "./resources/ivium/NaHalfcell-2_2-precrash/"
# fpath = "./resources/ivium/NaHalfcell-2_2-postcrash/"
# fpath = "./resources/ivium/NaHalfcell-2_5/"
fpath = "./resources/ivium/NaHalfcell-2_5-1Himaging/"

flist = os.listdir(fpath)

with open(fpath+"queuefile.in", "w") as qfile:
    for file in flist:
        if "TR" in file:
            print(file)
            qfile.write(file+"\n")

print("\nDone!")