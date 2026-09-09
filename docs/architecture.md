# CropHealthAI System Architecture

```
[ Frontend (React) ] <---> [ REST API (FastAPI Backend) ]
                                   |
                +------------------+------------------+
                |                                     |
        [ ML Inference Engine ]            [ Generative AI Advisory ]
      (TensorFlow / Vision Model)            (Google Gemini / Groq)
```

## Layers
1. **Frontend**: React application providing image upload, diagnosis dashboards, and weather views.
2. **Backend**: FastAPI modular API layer managing auth, requests, data validation, and pipeline coordination.
3. **ML Pipeline**: Computer vision model for classification and severity detection.
4. **Advisory Service**: LLM-driven generation of personalized treatment protocols.
