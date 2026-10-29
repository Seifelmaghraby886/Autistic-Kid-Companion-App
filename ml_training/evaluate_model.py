"""ARIA Model Evaluation — confusion matrix, per-class metrics, plots."""

import json
import numpy as np
from pathlib import Path


ROOT = Path(__file__).parent.parent
MODELS_DIR = ROOT / "models"
COMBINED_DIR = ROOT / "combined_dataset"
REPORTS_DIR = ROOT / "ml_training"


def evaluate_and_plot(progress_callback=None, log_callback=None):
    def emit(msg):
        print(f"[ARIA Eval] {msg}")
        if log_callback:
            log_callback(msg)

    emit("Loading model...")
    model_path = MODELS_DIR / "emotion_model.h5"
    labels_path = MODELS_DIR / "labels.json"

    if not model_path.exists():
        emit("❌ Model not found. Train first.")
        return

    try:
        import tensorflow as tf
        model = tf.keras.models.load_model(str(model_path), compile=False)
        with open(labels_path) as f:
            labels = json.load(f)
        emit(f"Model loaded. Classes: {labels}")
    except Exception as e:
        emit(f"❌ Load error: {e}")
        return

    if progress_callback: progress_callback(20)

    # Test data
    test_dir = COMBINED_DIR / "test"
    if not test_dir.exists():
        emit("No test set found.")
        return

    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    gen = ImageDataGenerator(rescale=1.0 / 255)
    test_data = gen.flow_from_directory(
        str(test_dir), target_size=(96, 96),
        color_mode="rgb", batch_size=32,
        class_mode="categorical", shuffle=False,
    )

    emit(f"Test images: {test_data.samples}")
    if progress_callback: progress_callback(40)

    # Predict
    preds = model.predict(test_data, verbose=0)
    y_pred = np.argmax(preds, axis=1)
    y_true = test_data.classes

    if progress_callback: progress_callback(60)

    # Metrics
    try:
        from sklearn.metrics import (
            classification_report, confusion_matrix,
            accuracy_score
        )
        acc = accuracy_score(y_true, y_pred)
        report = classification_report(y_true, y_pred, target_names=labels, output_dict=True)
        cm = confusion_matrix(y_true, y_pred)
        emit(f"\nOverall Accuracy: {acc*100:.2f}%")
        emit("\nPer-class metrics:")
        for lbl in labels:
            r = report.get(lbl, {})
            emit(f"  {lbl}: P={r.get('precision',0):.2f}  R={r.get('recall',0):.2f}  F1={r.get('f1-score',0):.2f}")
    except ImportError:
        emit("sklearn not available — skipping detailed metrics")
        cm = None

    if progress_callback: progress_callback(75)

    # Plots
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Confusion Matrix
        if cm is not None:
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
            ax.figure.colorbar(im, ax=ax)
            ax.set(
                xticks=np.arange(len(labels)), yticks=np.arange(len(labels)),
                xticklabels=labels, yticklabels=labels,
                title="ARIA Emotion Model — Confusion Matrix",
                ylabel="True Emotion", xlabel="Predicted Emotion"
            )
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            thresh = cm.max() / 2
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(j, i, format(cm[i, j], 'd'),
                            ha="center", va="center",
                            color="white" if cm[i, j] > thresh else "black")
            fig.tight_layout()
            plt.savefig(str(REPORTS_DIR / "confusion_matrix.png"), dpi=120)
            plt.close()
            emit("✅ Confusion matrix saved.")
    except Exception as e:
        emit(f"Plot error: {e}")

    if progress_callback: progress_callback(100)
    emit("Evaluation complete.")
