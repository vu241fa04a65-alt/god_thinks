# 🌿 god_thinks – Intelligent Plant Projects & Disease Diagnosis

**god_thinks** is a modern, AI-powered platform designed for plant health monitoring, real-time disease diagnosis, and smart agricultural advisory.

---

## 🚀 Overview

The **god_thinks** project focuses on empowering growers, researchers, and farmers with intelligent computer vision and generative AI tools to diagnose plant health issues, estimate crop water requirements, and provide actionable treatment recommendations.

### Key Highlights
- 🔍 **AI Plant Diagnosis**: Real-time visual disease identification for over 38+ plant species and pathogen conditions.
- 💊 **Actionable Treatment Plans**: Instant extraction of biological cause, preventive agricultural practices, and organic/chemical remedies.
- 💧 **Resource Efficiency**: Smart water footprint estimation based on environmental and soil variables.
- 📊 **Interactive Web Interface**: Clean, accessible, and responsive dashboard for field monitoring and analytics.

---

## 🛠️ Architecture & Tech Stack

- **Frontend**: HTML5, TailwindCSS, JavaScript, Chart.js
- **Backend / API**: FastAPI, Uvicorn, Python 3.10+
- **Machine Learning & Vision**: TensorFlow, Keras, Scikit-learn, Google Gemini Vision
- **Data & Vector Storage**: ChromaDB, Sentence-Transformers

---

## 📂 Project Structure

```text
god_thinks/
├── README.md               # Project documentation & overview
├── app.py                  # Web application server
├── models/                 # Model architectures & inference pipelines
├── static/                 # Styles, client scripts, and UI assets
├── templates/              # Dashboard and UI templates
└── requirements.txt        # Python package dependencies
```

---

## 🐳 Running with Docker & Docker Compose

For an all-in-one local setup with PostgreSQL, Redis, FastAPI Backend, React Frontend, and pgAdmin:

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.

### Quick Start
Run the convenience startup script:
```bash
# On Linux / macOS:
chmod +x scripts/dev_start.sh
./scripts/dev_start.sh

# On Windows (PowerShell):
.\scripts\dev_start.ps1
```

Or run directly with Docker Compose:
```bash
docker compose up --build
```

### Services & Port Mappings
| Service | URL / Port | Credentials / Purpose |
|---|---|---|
| **Frontend UI** | [http://localhost:3000](http://localhost:3000) | React Single Page Application served via Nginx |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI application & Uvicorn server |
| **Interactive API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI / OpenAPI documentation |
| **PostgreSQL** | `localhost:5432` | DB: `crophealth_db` (User: `postgres` / Pass: `postgres`) |
| **Redis** | `localhost:6379` | In-memory caching & background queues |
| **pgAdmin 4** | [http://localhost:5050](http://localhost:5050) | Email: `admin@crophealth.ai` / Password: `admin` |

---

## ⚡ Local Development (Without Docker)

### 1. Backend Setup
```bash
cd backend
cp .env.example .env
python -m venv venv
# Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).

