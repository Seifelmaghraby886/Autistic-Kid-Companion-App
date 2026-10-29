"""
ARIA Emotion Model Training
MobileNetV2-based emotion classifier with data augmentation, class weights, and early stopping.
"""

import os
import json
import numpy as np
from pathlib import Path


ROOT = Path(__file__).parent.parent
COMBINED_DIR = ROOT / "combined_dataset"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "ml_training"

IMG_SIZE = (96, 96)
BATCH_SIZE = 32
EPOCHS = 40
LEARNING_RATE = 1e-4


def log(msg):
    print(f"[ARIA Train] {msg}")


def train(progress_callback=None, log_callback=None) -> dict:
    """
    Train the emotion recognition model.
    Returns training history dict.
    """
    def emit_log(msg):
        log(msg)
        if log_callback:
            log_callback(msg)

    emit_log("Starting ARIA emotion model training...")

    try:
        import tensorflow as tf
        from tensorflow import keras
        emit_log(f"TensorFlow version: {tf.__version__}")
    except ImportError:
        emit_log("❌ TensorFlow not installed. Run: pip install tensorflow")
        return {}

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load labels
    labels_path = MODELS_DIR / "labels.json"
    if labels_path.exists():
        with open(labels_path) as f:
            labels = json.load(f)
    else:
        labels = ["anger", "fear", "joy", "neutral", "sadness", "surprise"]
    num_classes = len(labels)
    emit_log(f"Classes ({num_classes}): {labels}")

    if progress_callback:
        progress_callback(5)

    # ── Data generators with augmentation
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    train_gen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        brightness_range=[0.8, 1.2],
        zoom_range=0.15,
        horizontal_flip=True,
        fill_mode="nearest",
    )

    val_gen = ImageDataGenerator(rescale=1.0 / 255)

    train_dir = COMBINED_DIR / "train"
    val_dir = COMBINED_DIR / "validation"
    test_dir = COMBINED_DIR / "test"

    if not train_dir.exists():
        emit_log("❌ combined_dataset/train not found. Run prepare_datasets first.")
        return {}

    train_data = train_gen.flow_from_directory(
        str(train_dir),
        target_size=IMG_SIZE,
        color_mode="rgb",
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=True,
    )

    val_data = val_gen.flow_from_directory(
        str(val_dir),
        target_size=IMG_SIZE,
        color_mode="rgb",
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
    )

    emit_log(f"Training images: {train_data.samples}")
    emit_log(f"Validation images: {val_data.samples}")
    emit_log(f"Class indices: {train_data.class_indices}")

    # Save updated labels based on actual folder detection
    detected_labels = list(train_data.class_indices.keys())
    with open(labels_path, "w") as f:
        json.dump(detected_labels, f, indent=2)
    num_classes = len(detected_labels)
    emit_log(f"Updated labels: {detected_labels}")

    if progress_callback:
        progress_callback(15)

    # ── Class weights for imbalance
    try:
        from sklearn.utils.class_weight import compute_class_weight
        class_labels = train_data.classes
        unique = np.unique(class_labels)
        weights = compute_class_weight("balanced", classes=unique, y=class_labels)
        class_weights = {i: w for i, w in zip(unique, weights)}
        emit_log(f"Class weights: {class_weights}")
    except Exception:
        class_weights = None
        emit_log("Class weights not computed (sklearn not available)")

    if progress_callback:
        progress_callback(20)

    # ── Build Model (MobileNetV2)
    emit_log("Building MobileNetV2 model...")
    base_model = keras.applications.MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False  # Freeze base initially

    model = keras.Sequential([
        base_model,
        keras.layers.GlobalAveragePooling2D(),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.4),
        keras.layers.Dense(256, activation="relu"),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(128, activation="relu"),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    emit_log(f"Model parameters: {model.count_params():,}")
    if progress_callback:
        progress_callback(30)

    # ── Callbacks
    model_path = str(MODELS_DIR / "emotion_model.h5")
    callbacks = [
        keras.callbacks.ModelCheckpoint(
            filepath=model_path,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=8,
            restore_best_weights=True,
            verbose=1,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=4,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    # Custom callback for progress
    class ProgressCallback(keras.callbacks.Callback):
        def __init__(self, total_epochs, progress_fn, log_fn):
            super().__init__()
            self._total = total_epochs
            self._pfn = progress_fn
            self._lfn = log_fn

        def on_epoch_end(self, epoch, logs=None):
            logs = logs or {}
            msg = (f"Epoch {epoch+1}/{self._total} — "
                   f"loss: {logs.get('loss',0):.4f}  "
                   f"acc: {logs.get('accuracy',0)*100:.1f}%  "
                   f"val_acc: {logs.get('val_accuracy',0)*100:.1f}%")
            if self._lfn:
                self._lfn(msg)
            if self._pfn:
                pct = 30 + int((epoch + 1) / self._total * 55)
                self._pfn(min(pct, 85))

    callbacks.append(ProgressCallback(EPOCHS, progress_callback, log_callback))

    # ── Phase 1: Train head only
    emit_log("\n── Phase 1: Training classification head...")
    history1 = model.fit(
        train_data,
        validation_data=val_data,
        epochs=min(EPOCHS, 20),
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=0,
    )

    # ── Phase 2: Fine-tune top layers of base model
    emit_log("\n── Phase 2: Fine-tuning top layers...")
    base_model.trainable = True
    # Freeze bottom 80% of layers
    fine_tune_at = int(len(base_model.layers) * 0.80)
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE / 10),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    history2 = model.fit(
        train_data,
        validation_data=val_data,
        epochs=min(EPOCHS, 20),
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=0,
    )

    if progress_callback:
        progress_callback(88)

    # ── Load best model
    if os.path.exists(model_path):
        model = keras.models.load_model(model_path)
        emit_log(f"✅ Best model loaded from {model_path}")

    # ── Test evaluation
    if test_dir.exists():
        emit_log("\nEvaluating on test set...")
        test_data = val_gen.flow_from_directory(
            str(test_dir),
            target_size=IMG_SIZE,
            color_mode="rgb",
            batch_size=BATCH_SIZE,
            class_mode="categorical",
            shuffle=False,
        )
        test_loss, test_acc = model.evaluate(test_data, verbose=0)
        emit_log(f"Test accuracy: {test_acc * 100:.2f}%")
        emit_log(f"Test loss: {test_loss:.4f}")
    else:
        test_acc = 0.0
        test_loss = 0.0

    # ── Export TFLite
    emit_log("Exporting TFLite model...")
    try:
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()
        tflite_path = MODELS_DIR / "emotion_model.tflite"
        with open(tflite_path, "wb") as f:
            f.write(tflite_model)
        emit_log(f"✅ TFLite model saved: {tflite_path}")
    except Exception as e:
        emit_log(f"TFLite export skipped: {e}")

    if progress_callback:
        progress_callback(95)

    # ── Combine histories
    combined_history = {}
    for key in ["accuracy", "val_accuracy", "loss", "val_loss"]:
        combined_history[key] = (
            list(history1.history.get(key, [])) +
            list(history2.history.get(key, []))
        )

    # ── Save training report
    report = {
        "test_accuracy": float(test_acc),
        "test_loss": float(test_loss),
        "total_epochs": len(combined_history.get("accuracy", [])),
        "best_val_accuracy": float(max(combined_history.get("val_accuracy", [0]))),
        "labels": detected_labels,
        "num_classes": num_classes,
        "img_size": list(IMG_SIZE),
        "model_path": str(model_path),
    }
    with open(REPORTS_DIR / "training_report.json", "w") as f:
        json.dump(report, f, indent=2)

    emit_log(f"\n🎉 Training complete!")
    emit_log(f"   Best val accuracy: {report['best_val_accuracy']*100:.1f}%")
    emit_log(f"   Model saved: {model_path}")

    if progress_callback:
        progress_callback(100)

    return combined_history


if __name__ == "__main__":
    train()
