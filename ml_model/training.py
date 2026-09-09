"""
CropHealthAI: Deep Learning Training Pipeline for Crop Disease Classification.
Supports both YOLO (YOLOv5 / YOLOv8) and EfficientNet Transfer Learning architectures.
"""

import os
import argparse
import time
from typing import Optional, Dict, Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

try:
    from ultralytics import YOLO
    ULTRALYTICS_INSTALLED = True
except ImportError:
    ULTRALYTICS_INSTALLED = False

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")

def train_yolo(
    data_yaml: str,
    model_type: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch_size: int = 16,
    device: str = "0" if torch.cuda.is_available() else "cpu",
    project: str = "runs/crop_disease_train",
    name: str = "yolo_run"
) -> Dict[str, Any]:
    """
    Train a YOLO model (YOLOv5 / YOLOv8) on annotated plant leaf disease datasets.
    """
    if not ULTRALYTICS_INSTALLED:
        raise ImportError("Ultralytics is required for YOLO training. Install via `pip install ultralytics`.")

    print(f"\n=======================================================")
    print(f"Starting YOLO Training Pipeline")
    print(f"Base Architecture: {model_type} | Epochs: {epochs} | Device: {device}")
    print(f"Data config: {data_yaml}")
    print(f"=======================================================\n")

    model = YOLO(model_type)
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        project=project,
        name=name,
        save=True,
        plots=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        warmup_epochs=3
    )

    best_weights_src = os.path.join(project, name, "weights", "best.pt")
    target_weights = os.path.join(MODELS_DIR, "PlantDiseaseDetection.pt")

    if os.path.exists(best_weights_src):
        import shutil
        shutil.copyfile(best_weights_src, target_weights)
        print(f"[Training Completed] Best checkpoint deployed to: {target_weights}")

    return {"status": "success", "results": results}

def build_efficientnet(num_classes: int = 116, pretrained: bool = True) -> nn.Module:
    """
    Construct an EfficientNet-B0 transfer learning model tailored for foliar disease classification.
    """
    weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
    model = models.efficientnet_b0(weights=weights)

    # Freeze feature extraction base initially
    for param in model.features.parameters():
        param.requires_grad = False

    # Replace classifier head
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(in_features=in_features, out_features=512),
        nn.SiLU(),
        nn.Dropout(p=0.2, inplace=True),
        nn.Linear(in_features=512, out_features=num_classes)
    )
    return model

def train_efficientnet(
    dataset_dir: str = DATASETS_DIR,
    num_classes: int = 116,
    epochs: int = 25,
    batch_size: int = 32,
    lr: float = 1e-3,
    device: Optional[str] = None
) -> nn.Module:
    """
    Train an EfficientNet model on crop disease image folders with data augmentations.
    """
    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n=======================================================")
    print(f"Starting EfficientNet-B0 Transfer Learning Pipeline")
    print(f"Classes: {num_classes} | Device: {dev} | Epochs: {epochs}")
    print(f"=======================================================\n")

    train_transforms = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_path = os.path.join(dataset_dir, "train")
    val_path = os.path.join(dataset_dir, "val")

    model = build_efficientnet(num_classes=num_classes, pretrained=True).to(dev)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = torch.optim.AdamW(model.classifier.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # Check if dataset path has class folders
    if not os.path.exists(train_path) or len(os.listdir(train_path)) == 0:
        print(f"[Training Notice] No image class folders detected in {train_path}.")
        print("[Training Notice] Synthesizing 1-epoch dry run to confirm architecture initialization.")
        # Dry run with dummy tensor
        dummy_inputs = torch.randn(4, 3, 224, 224).to(dev)
        dummy_targets = torch.randint(0, num_classes, (4,)).to(dev)
        outputs = model(dummy_inputs)
        loss = criterion(outputs, dummy_targets)
        loss.backward()
        optimizer.step()
        print(f"[Dry Run] Successfully initialized. Loss: {loss.item():.4f}")
        return model

    train_dataset = datasets.ImageFolder(train_path, transform=train_transforms)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)

    val_loader = None
    if os.path.exists(val_path) and len(os.listdir(val_path)) > 0:
        val_dataset = datasets.ImageFolder(val_path, transform=val_transforms)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

    best_val_acc = 0.0
    for epoch in range(1, epochs + 1):
        start_time = time.time()
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for inputs, targets in train_loader:
            inputs, targets = inputs.to(dev), targets.to(dev)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

        scheduler.step()
        train_loss = running_loss / total
        train_acc = 100.0 * correct / total

        val_acc = 0.0
        if val_loader:
            model.eval()
            val_correct = 0
            val_total = 0
            with torch.no_grad():
                for inputs, targets in val_loader:
                    inputs, targets = inputs.to(dev), targets.to(dev)
                    outputs = model(inputs)
                    _, predicted = outputs.max(1)
                    val_total += targets.size(0)
                    val_correct += predicted.eq(targets).sum().item()
            val_acc = 100.0 * val_correct / val_total

        elapsed = time.time() - start_time
        print(f"Epoch [{epoch:02d}/{epochs:02d}] - Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}% ({elapsed:.1f}s)")

        # Save checkpoint
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            save_path = os.path.join(MODELS_DIR, "efficientnet_crophealth_best.pth")
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_acc": val_acc
            }, save_path)
            print(f"  -> Saved best checkpoint to {save_path}")

    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CropHealthAI Model Training Pipeline")
    parser.add_argument("--framework", choices=["yolo", "efficientnet"], default="efficientnet", help="Architecture framework")
    parser.add_argument("--data", default="dataset/data.yaml", help="Path to data.yaml (for YOLO) or datasets/ (for EfficientNet)")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--classes", type=int, default=116, help="Number of disease classes")
    args = parser.parse_args()

    if args.framework == "yolo":
        train_yolo(data_yaml=args.data, epochs=args.epochs, batch_size=args.batch_size)
    else:
        train_efficientnet(dataset_dir=DATASETS_DIR, num_classes=args.classes, epochs=args.epochs, batch_size=args.batch_size)

