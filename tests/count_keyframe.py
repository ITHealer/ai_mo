import os
from pathlib import Path
from typing import List, Set

IMAGE_EXTENSIONS: Set[str] = {
    '.jpg', '.jpeg', '.png', '.gif', 
    '.bmp', '.tiff', '.webp', '.heic'
}

def count_images_in_folder(folder_path: str) -> int:
    path_obj = Path(folder_path)
    if not path_obj.exists():
        print(f"❌ Error: The path '{folder_path}' does not exist.")
        return 0
    
    if not path_obj.is_dir():
        print(f"❌ Error: '{folder_path}' is not a directory.")
        return 0

    image_count = 0
    print(f"📂 Scanning folder: {path_obj.resolve()}")

    try:
        for file_path in path_obj.iterdir():
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix in IMAGE_EXTENSIONS:
                    image_count += 1
    except PermissionError:
        print(f"🚫 Error: Permission denied accessing '{folder_path}'.")
        return 0

    return image_count

if __name__ == "__main__":
    target_folder = input("Please enter the folder path: ").strip()
    
    target_folder = target_folder.replace('"', '').replace("'", "")
    total_images = count_images_in_folder(target_folder)
    
    print("-" * 40)
    print(f"📸 Total images found: {total_images}")
    print("-" * 40)