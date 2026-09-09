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

## 🚀 Deployment Guides

### 1. Simple VPS Deployment (DigitalOcean / AWS EC2 / Linode / Hetzner)
Deploying CropHealthAI to any Linux VPS using `docker-compose` takes under 2 minutes:

1. **SSH into your VPS:**
   ```bash
   ssh root@your-server-ip
   ```
2. **Install Docker & Docker Compose:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
3. **Clone the repository & launch:**
   ```bash
   git clone https://github.com/vu241fa04a65-alt/god_thinks.git /opt/crophealth
   cd /opt/crophealth
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   docker compose -f docker-compose.yml up -d --build
   ```
4. **Verify running containers:**
   ```bash
   docker compose ps
   ```
   Open `http://your-server-ip:3000` to access the web application and `http://your-server-ip:8000/docs` for API documentation.

---

### 2. Deploy to Docker Hub + Heroku (Container Registry)

You can containerize and push directly to Docker Hub and deploy the backend to Heroku Container Registry:

#### Step A: Push to Docker Hub
```bash
# Log in to Docker Hub
docker login

# Build, tag and push images using the deployment script:
./scripts/deploy.sh --registry your-dockerhub-username --tag v1.0.0 --skip-tests
```

#### Step B: One-Click Deploy to Heroku
```bash
# 1. Login to Heroku Container Registry
heroku login
heroku container:login

# 2. Create Heroku Apps & Managed Postgres
heroku create crophealth-backend-api
heroku addons:create heroku-postgresql:essential-0 -a crophealth-backend-api

# 3. Tag and push container to Heroku
docker tag your-dockerhub-username/crophealth-backend:v1.0.0 registry.heroku.com/crophealth-backend-api/web
docker push registry.heroku.com/crophealth-backend-api/web

# 4. Release and configure environment variables
heroku container:release web -a crophealth-backend-api
heroku config:set SECRET_KEY="your-32-character-secret-key" -a crophealth-backend-api
heroku config:set ENVIRONMENT="production" -a crophealth-backend-api

# 5. Open deployed backend
heroku open -a crophealth-backend-api
```

---

### 3. Kubernetes Deployment (k8s)

Deploy the multi-replica scalable stack to any Kubernetes cluster (EKS, AKS, GKE, or Minikube):

```bash
# 1. Review or customize secrets
cp k8s/secrets.template.yaml k8s/secrets.yaml
# (Edit k8s/secrets.yaml with production database and API credentials)

# 2. Deploy all manifests using Kustomize:
kubectl apply -k k8s/

# 3. Monitor rollout:
kubectl rollout status deployment/crophealth-backend -n crophealth
kubectl rollout status deployment/crophealth-frontend -n crophealth

# 4. Check services & ingress:
kubectl get svc,ingress -n crophealth
```

---

### 4. Managed Cloud Infrastructure via Terraform

Provision AWS RDS PostgreSQL and S3 Object Storage with automated backups and encryption:

```bash
# Dry-run infrastructure simulation:
./scripts/terraform_stub.sh plan

# Provision real cloud resources:
./scripts/terraform_stub.sh apply
```

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


