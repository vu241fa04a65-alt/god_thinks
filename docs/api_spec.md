# CropHealthAI API Specification

## Endpoints

### 1. Health Check
- **GET** `/api/v1/health`
- **Response**: `{"status": "healthy"}`

### 2. Disease Diagnosis
- **POST** `/api/v1/diagnose`
- **Body**: `multipart/form-data` (file: image)
- **Response**:
  ```json
  {
    "crop": "Tomato",
    "disease": "Early Blight",
    "confidence": 0.94,
    "treatment": {
      "cause": "Alternaria solani fungus",
      "prevention": "Ensure proper spacing and avoid overhead watering",
      "cure": "Apply copper-based fungicide"
    }
  }
  ```
