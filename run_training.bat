@echo off
title ARIA - Emotion Model Training
cd /d "%~dp0"
echo ============================================
echo  ARIA Emotion Model Training
echo  This will take 30-90 minutes on CPU.
echo ============================================
echo.
"C:\Users\Seif\AppData\Local\Programs\Python\Python311\python.exe" -c "
import sys
sys.path.insert(0, '.')
from ml_training.prepare_datasets import prepare_combined_dataset
from ml_training.train_emotion_model import train
from ml_training.evaluate_model import evaluate_and_plot

print('Step 1: Preparing datasets...')
prepare_combined_dataset()

print()
print('Step 2: Training model...')
train()

print()
print('Step 3: Evaluating...')
evaluate_and_plot()

print()
print('Done! Launch ARIA with run_aria.bat')
"
pause
