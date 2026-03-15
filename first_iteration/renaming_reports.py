import os

folder_path = "reports_en"

files = [f for f in os.listdir(folder_path) if f.endswith(".md")]
#files.sort()  # optional but recommended

for i, filename in enumerate(files, start=1):
    old_path = os.path.join(folder_path, filename)
    new_path = os.path.join(folder_path, f"report_{i}.md")
    os.rename(old_path, new_path)

print("Renaming completed.")