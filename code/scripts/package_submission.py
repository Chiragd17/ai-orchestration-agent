import os
import zipfile
from pathlib import Path

def package():
    project_root = Path(__file__).resolve().parent.parent.parent
    zip_path = project_root / "code.zip"
    
    # Files/Dirs to include in the zip
    # Required: "Full runnable solution, prompts/configuration, README, and the required evaluation/ folder"
    targets = [
        "code", 
        "evaluation",
        "README.md"
    ]
    
    # Exclude logic
    excludes = ["__pycache__", ".env", "venv", ".git", "log.txt"]
    
    print(f"Creating {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for t in targets:
            target_path = project_root / t
            if target_path.is_file():
                zf.write(target_path, t)
            elif target_path.is_dir():
                for root, dirs, files in os.walk(target_path):
                    # Filter excluded dirs
                    dirs[:] = [d for d in dirs if d not in excludes]
                    
                    for f in files:
                        if f in excludes or f.endswith(".pyc"):
                            continue
                        file_path = Path(root) / f
                        arcname = file_path.relative_to(project_root)
                        zf.write(file_path, arcname)
                        
    print(f"Successfully packaged {zip_path}")
    print(f"Remember to submit: code.zip, dataset/output.csv, and your chat_transcript!")

if __name__ == "__main__":
    package()
