import os

st = os.stat("./test_file")

for s in st:
    print (s)

print(st.st_uid, st.st_mtime)