# 🔭 Observability & Telemetry Guide

CropHealthAI incorporates comprehensive observability across errors, metrics, structured logs, and container readiness probes.

---

## 1. Sentry Error Tracking & Performance Monitoring

Sentry is integrated in both backend (Python FastAPI) and frontend (React 18).

### A. Environment Configuration
Add your Sentry DSNs to your environment files:

```bash
# Backend (.env)
SENTRY_DSN="https://examplePublicKey@o0.ingest.sentry.io/0"
SENTRY_TRACES_SAMPLE_RATE=0.2

# Frontend (.env)
VITE_SENTRY_DSN="https://examplePublicKey@o0.ingest.sentry.io/0"
VITE_SENTRY_TRACES_SAMPLE_RATE=0.2
```

### B. Backend Initialization Sample
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration()
    ],
    send_default_pii=False,
)
```

### C. Frontend Initialization Sample
```typescript
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE || 'production',
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration({
      maskAllText: false,
      blockAllMedia: false,
    }),
  ],
  tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.2'),
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

---

## 2. Prometheus Metrics

The backend exposes a standard Prometheus scrape endpoint at `/metrics` (and `/api/v1/metrics`).

### Exposed Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `crophealth_http_requests_total` | Counter | `method`, `endpoint`, `status_code` | Total HTTP requests handled |
| `crophealth_http_request_duration_seconds` | Histogram | `method`, `endpoint` | Latency distribution buckets (10ms to 10s) |
| `crophealth_http_active_requests` | Gauge | — | Current in-flight requests |
| `crophealth_disease_predictions_total` | Counter | `crop_type`, `disease` | Completed leaf diagnostic inference calls |
| `crophealth_expert_reviews_total` | Counter | `decision` | Expert agronomist reviews submitted |
| `crophealth_alert_broadcasts_total` | Counter | `severity` | Outbreak SMS broadcast events |
| `crophealth_database_healthy` | Gauge | — | 1 = database healthy, 0 = connection degraded |

### Sample Prometheus Scrape Configuration (`prometheus.yml`)

Add the following job definition to your `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'crophealth-backend'
    metrics_path: '/metrics'
    scrape_interval: 10s
    static_configs:
      - targets: ['backend:8000']
        labels:
          app: 'crophealth'
          tier: 'api'
          environment: 'production'

  # Kubernetes Service Discovery (Optional)
  - job_name: 'kubernetes-pods-crophealth'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: ['crophealth']
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
```

---

## 3. Structured JSON Logging & Rotation

Logs are emitted in standard structured JSON format on `sys.stdout` for container collectors (Fluentbit, Datadog, CloudWatch) and rotated locally:

- **JSON Schema:**
  ```json
  {
    "timestamp": "2026-09-09T14:10:00.000000Z",
    "level": "INFO",
    "logger": "CropHealthAI",
    "module": "reports",
    "func": "upload_report",
    "line": 84,
    "message": "Leaf image processed successfully",
    "crop": "Tomato",
    "disease": "Early Blight"
  }
  ```
- **Rotation Configuration:**
  - Configurable via `LOG_ROTATION_MAX_BYTES` (default: 10MB) and `LOG_ROTATION_BACKUP_COUNT` (default: 5 backups).
  - Stored under `backend/logs/crophealth.log`.

---

## 4. Health Checks & Container Probes

CropHealthAI provides separate liveness and readiness probes designed for Kubernetes and Docker Swarm:

1. **Liveness Probe (`GET /health`):**
   - Lightweight status check verifying process uptime and responsiveness.
   - HTTP 200: Application is live.

2. **Readiness Probe (`GET /ready`):**
   - Deep dependency inspection.
   - Executes `SELECT 1` on the PostgreSQL database engine.
   - Validates that `backend/storage/` is mounted and writable.
   - HTTP 200: Traffic ready.
   - HTTP 503: Service not ready (pod will not receive traffic until dependencies recover).

### Kubernetes Configuration:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 20
  periodSeconds: 15

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
```
