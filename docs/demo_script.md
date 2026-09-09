# CropHealthAI Demo Script

1. **Step 1**: Launch the backend API using `uvicorn backend.app.main:app --reload`.
2. **Step 2**: Open interactive OpenAPI documentation at `http://127.0.0.1:8000/docs`.
3. **Step 3**: Upload a test plant leaf image to `/api/v1/diagnose`.
4. **Step 4**: Verify real-time disease diagnosis, confidence score, and generated cure instructions.
