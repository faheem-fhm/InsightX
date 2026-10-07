import os
import shutil
import zipfile
import subprocess

src = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX"
dst_dir = r"C:\Users\HP\Downloads\InsightX"
zip_path = r"C:\Users\HP\Downloads\InsightX.zip"

print("Exporting fully debugged InsightX project into Downloads...")

def should_exclude(path):
    parts = path.split(os.sep)
    for p in parts:
        if p in ["node_modules", "__pycache__", ".pytest_cache", ".git"]:
            return True
        if p.endswith(".pyc"):
            return True
    return False

# 1. Write ZIP archive
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in ["node_modules", "__pycache__", ".pytest_cache", ".git"]]
        for file in files:
            full_path = os.path.join(root, file)
            if not should_exclude(full_path):
                rel_path = os.path.relpath(full_path, src)
                zipf.write(full_path, os.path.join("InsightX", rel_path))

print(f"-> Created ZIP Archive: {zip_path} ({os.path.getsize(zip_path) / 1024:.1f} KB)")

# 2. Synchronize directory with robocopy
cmd = f'robocopy "{src}" "{dst_dir}" /E /XD node_modules __pycache__ .pytest_cache .git'
subprocess.run(cmd, shell=True)
print(f"-> Synchronized Directory: {dst_dir}")
