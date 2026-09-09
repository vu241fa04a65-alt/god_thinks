# CropHealthAI Machine Learning Pipeline

- `app/models`: Stores trained weights (`PlantDiseaseDetection.pt` covering 116 crop disease classes)
- `inference.py`: Loads trained models, runs predictions, and generates Grad-CAM saliency heatmap overlays.
- `training.py`: Full training pipeline for YOLO and EfficientNet-B0 with data augmentations.
- `datasets/`: Dataset structure and sample leaf images.
