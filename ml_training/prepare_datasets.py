"""
ARIA Dataset Preparation
Extracts, validates, merges, and splits 3 emotion datasets.
"""

import os
import shutil
import zipfile
import random
import json
from pathlib import Path
from collections import defaultdict
from PIL import Image

# ── Paths
ROOT = Path(__file__).parent.parent
DATASETS_DIR = ROOT / "datasets"
COMBINED_DIR = ROOT / "combined_dataset"
MODELS_DIR = ROOT / "models"

# ── Emotion classes
EMOTIONS = ["anger", "fear", "joy", "neutral", "sadness", "surprise"]
NATURAL_ALIASES = {"Natural", "natural", "neutral", "NEUTRAL", "Neutral"}
NAME_MAP = {
    "Natural": "neutral", "natural": "neutral", "neutral": "neutral",
    "anger": "anger", "Anger": "anger",
    "fear": "fear", "Fear": "fear",
    "joy": "joy", "Joy": "joy", "happy": "joy", "Happy": "joy",
    "sadness": "sadness", "Sadness": "sadness", "sad": "sadness",
    "surprise": "surprise", "Surprise": "surprise", "surprised": "surprise",
}

SPLIT_RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}


def log(msg):
    print(f"[ARIA Dataset] {msg}")


def extract_zip(zip_path: Path, extract_to: Path):
    log(f"Extracting {zip_path.name}...")
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_to)
    log(f"  → Extracted to {extract_to}")


def find_image_folders(base_dir: Path) -> dict:
    """Find all emotion class folders recursively."""
    found = {}
    for path in base_dir.rglob("*"):
        if path.is_dir():
            folder_name = path.name
            mapped = NAME_MAP.get(folder_name)
            if mapped:
                if mapped not in found:
                    found[mapped] = []
                found[mapped].append(path)
    return found


def collect_valid_images(folder: Path) -> list:
    """Return list of valid image paths from a folder."""
    valid = []
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    for img_path in folder.iterdir():
        if img_path.suffix.lower() in extensions:
            try:
                with Image.open(img_path) as img:
                    img.verify()
                valid.append(img_path)
            except Exception:
                pass
    return valid


def prepare_combined_dataset(progress_callback=None) -> dict:
    """
    Main function: extract zips, collect images, split into train/val/test.
    Returns dataset statistics dict.
    """
    # Clean previous
    if COMBINED_DIR.exists():
        shutil.rmtree(COMBINED_DIR)

    # Create split folders
    for split in ["train", "validation", "test"]:
        for emotion in EMOTIONS:
            (COMBINED_DIR / split / emotion).mkdir(parents=True, exist_ok=True)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Find all zip files
    zip_files = list(DATASETS_DIR.glob("*.zip"))
    if not zip_files:
        log("No zip files found in datasets/")
        return {}

    log(f"Found {len(zip_files)} dataset zip(s)")

    # Extract temp dirs
    temp_dirs = []
    for i, zip_file in enumerate(zip_files):
        temp_dir = ROOT / "datasets" / f"_extracted_{i}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        try:
            extract_zip(zip_file, temp_dir)
            temp_dirs.append(temp_dir)
        except Exception as e:
            log(f"  ✗ Failed to extract {zip_file.name}: {e}")

        if progress_callback:
            progress_callback(int((i + 1) / len(zip_files) * 20))

    # Collect all images per emotion
    all_images = defaultdict(list)
    for temp_dir in temp_dirs:
        emotion_folders = find_image_folders(temp_dir)
        for emotion, folders in emotion_folders.items():
            for folder in folders:
                imgs = collect_valid_images(folder)
                all_images[emotion].extend(imgs)
                log(f"  + {emotion}: {len(imgs)} images from {folder.name}")

    if progress_callback:
        progress_callback(35)

    # Check we have something
    total_found = sum(len(v) for v in all_images.values())
    log(f"\nTotal valid images found: {total_found}")
    for em, imgs in all_images.items():
        log(f"  {em}: {len(imgs)} images")

    # Split and copy
    stats = {}
    copied_total = 0
    emotion_list = list(all_images.keys())

    for ei, emotion in enumerate(EMOTIONS):
        imgs = all_images.get(emotion, [])
        if not imgs:
            log(f"  ⚠ No images for class: {emotion}")
            stats[emotion] = {"train": 0, "validation": 0, "test": 0, "total": 0}
            continue

        random.shuffle(imgs)

        n = len(imgs)
        n_train = int(n * SPLIT_RATIOS["train"])
        n_val = int(n * SPLIT_RATIOS["validation"])

        splits = {
            "train":      imgs[:n_train],
            "validation": imgs[n_train:n_train + n_val],
            "test":       imgs[n_train + n_val:],
        }

        counts = {}
        for split_name, split_imgs in splits.items():
            dest_dir = COMBINED_DIR / split_name / emotion
            count = 0
            for j, src in enumerate(split_imgs):
                dst = dest_dir / f"{emotion}_{split_name}_{j:05d}{src.suffix.lower()}"
                try:
                    # Resize and save as clean JPEG
                    with Image.open(src) as img:
                        img = img.convert("RGB")
                        img = img.resize((224, 224), Image.LANCZOS)
                        img.save(dst, "JPEG", quality=90)
                    count += 1
                    copied_total += 1
                except Exception as e:
                    pass

            counts[split_name] = count

        counts["total"] = sum(counts.values())
        stats[emotion] = counts
        log(f"  ✓ {emotion}: train={counts['train']}, val={counts['validation']}, test={counts['test']}")

        if progress_callback:
            progress_callback(35 + int((ei + 1) / len(EMOTIONS) * 50))

    # Cleanup temp
    for temp_dir in temp_dirs:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

    # Save labels.json
    labels = sorted(all_images.keys())
    labels_data = {i: em for i, em in enumerate(labels)}
    with open(MODELS_DIR / "labels.json", "w") as f:
        json.dump(labels, f, indent=2)

    log(f"\n✅ Dataset ready! Total images copied: {copied_total}")
    log(f"   Labels saved to models/labels.json: {labels}")

    if progress_callback:
        progress_callback(100)

    return stats


if __name__ == "__main__":
    stats = prepare_combined_dataset()
    print("\nDataset Statistics:")
    for em, counts in stats.items():
        print(f"  {em}: {counts}")
