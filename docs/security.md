# 🛡️ Application Security Guide

CropHealthAI employs a defense-in-depth security model across the presentation layer, REST API gateways, file processing pipelines, authentication sessions, and cloud infrastructure.

---

## 1. Security Architecture Summary

```
                       [ HTTPS Client / Browser ]
                                   │
                                   ▼
                [ Ingress / TLS Termination + HSTS ]
                                   │
                     (Strict-Transport-Security)
                                   ▼
                     [ SecurityHeadersMiddleware ]
        (X-Content-Type-Options, X-Frame-Options, CSP, Referrer)
                                   │
                                   ▼
                    [ GlobalRateLimitMiddleware ]
                    (120 req/min, 20 upload/min)
                                   │
                                   ▼
                       [ CORS Whitelist Filter ]
                 (Enforced specific allowed origins)
                                   │
                                   ▼
                    [ AuthAudit & Login Limiter ]
                   (Brute-force lockout & tracking)
                                   │
                                   ▼
              [ Input Sanitizer & File Malware Scanner ]
              (XSS sanitization, PE/ELF/Script rejection)
                                   │
                                   ▼
               [ Application Logic & Database Engine ]
```

---

## 2. HTTPS Enforcement & Security Headers

### A. Automatic HTTPS & HSTS
In production (`ENVIRONMENT=production` or `ENFORCE_HTTPS=true`):
- All insecure HTTP traffic is automatically redirected to HTTPS via HTTP 301 Permanent Redirect.
- The `Strict-Transport-Security` (HSTS) header is attached with a 1-year duration and preload directive:
  ```http
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  ```

### B. Defensive Headers Matrix
Every HTTP response carries the following hardening headers:

| Header | Value | Purpose |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Forces all future browser connections over TLS/HTTPS |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing attacks |
| `X-Frame-Options` | `DENY` | Prevents Clickjacking by disallowing framing |
| `X-XSS-Protection` | `1; mode=block` | Enables legacy browser XSS filters |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Protects sensitive path information in referrers |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(self)` | Restricts hardware APIs to authorized origins |

---

## 3. Authentication & Secure Cookies

### A. Refresh Token Cookies
Refresh tokens are stored in hardened browser cookies rather than localStorage:
- **`HttpOnly=true`**: Inaccessible to JavaScript, neutralizing token theft via XSS.
- **`Secure=true`**: Transmitted strictly over HTTPS in production.
- **`SameSite=Lax`**: Prevents Cross-Site Request Forgery (CSRF) on cross-origin requests.
- **`Path=/`**: Scoped to the application.
- **Rotation**: Refresh tokens are single-use; a new refresh token is issued and rotated on every `/auth/refresh` call.

### B. Brute-Force & Credential Stuffing Defense
- **`InMemoryLoginRateLimiter`**: Restricts failed login attempts to **5 attempts per 5-minute window** per client IP.
- **Lockout**: Exceeded attempts trigger an immediate `HTTP 429 Too Many Requests` with a cooldown period.
- **Rate Limit Headers**: Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

---

## 4. Input Validation & Sanitization

All user-supplied text (crop variety names, farm location coordinates, observations, notes) is passed through `sanitize_text()` before processing or database persistence:
- **XSS Stripping**: Removes `<script>`, `<iframe>`, and dangerous event handlers (`onload=`, `onerror=`, `onclick=`).
- **Control Character Filtering**: Removes null bytes (`\x00`) and non-printable control characters.
- **Unicode Normalization**: Applies NFKC normalization to prevent homograph / visual spoofing attacks.
- **HTML Entity Encoding**: Escapes residual sensitive symbols (`&`, `<`, `>`, `"`, `'`).

---

## 5. File Upload Hardening & Malware Scanning

Uploaded leaf photos and field imagery are processed through a multi-tier security pipeline in `validate_image()`:

### A. Size Limits
- Enforced maximum upload size via `MAX_IMAGE_SIZE_MB` (default: **10MB**).
- Empty (0-byte) files are immediately rejected.

### B. Malware & Disguised Executable Detection
Heuristic magic-byte signature analysis rejects dangerous binary formats disguised as images:
- **Windows Executables (PE / EXE / DLL)**: Magic header `b"MZ"`.
- **Linux Executables (ELF)**: Magic header `b"\x7fELF"`.
- **Java Class Files**: Magic header `b"\xca\xfe\xba\xbe"`.
- **Shell Scripts**: Shebang prefix `b"#!"`.
- **Compiled Python**: Magic header `b"\x55\x0d\x0d\x0a"`.
- **Disguised PDFs**: Header `b"%PDF"`.

### C. Polyglot & Web Shell Payload Inspection
Inspects raw image streams for embedded server-side execution tags:
- `<?php`, `<?=`, `<script`, `javascript:`, `eval(`, `base64_decode(`, `system(`, `passthru(`, `shell_exec(`.

### D. Decompression Bomb Protection
- Maximum image resolution is capped at **8000 x 8000 pixels** (64 Megapixels).
- Prevents memory-exhaustion Denial-of-Service attacks triggered by malicious compressed image payloads.

### E. Filename Sanitization & Directory Traversal
- `sanitize_filename()` strips path traversal sequences (`../`, `..\\`), null bytes, and non-alphanumeric characters.
- Files are saved with cryptographically random UUID stems (`img_{timestamp}_{uuid}.jpg`).

---

## 6. Secrets Management

- **No Committed Secrets**: Secrets, database passwords, and API keys are strictly forbidden from source control.
- **Environment Driven**: Loaded via `.env` in local development and injected via Kubernetes Secrets or Cloud Secret Managers in production.
- **Mandatory Production Secrets**:
  - `SECRET_KEY`: Minimum 32-character random string (generate with `openssl rand -hex 32`).
  - `DATABASE_URL`: Encrypted connection string.
  - `TWILIO_AUTH_TOKEN`, `GEMINI_API_KEY`, `OPENWEATHER_API_KEY`.

---

## 7. CORS Whitelist & Rate Limiting

### A. CORS Whitelist
Instead of a wildcard (`*`), CORS origins are strictly validated against `CORS_ORIGINS`:
```bash
# Production Example
CORS_ORIGINS="https://app.crophealth.ai,https://admin.crophealth.ai"
```

### B. Global API Rate Limiter
`GlobalRateLimitMiddleware` enforces client-level traffic control:
- **General Endpoints**: Configurable via `RATE_LIMIT_PER_MINUTE` (default: **120 requests/minute**).
- **Heavy Endpoints (`/reports/upload`)**: Strict ceiling of **20 requests/minute** to protect ML workers.
- **Exemptions**: Kubernetes liveness (`/health`), readiness (`/ready`), and Prometheus (`/metrics`) probes are exempted to prevent monitoring blackouts.

---

## 8. Configuration Reference

| Environment Variable | Default | Recommended Production Value | Description |
|---|---|---|---|
| `ENVIRONMENT` | `development` | `production` | Enables production security policies |
| `ENFORCE_HTTPS` | `false` | `true` | Forces HTTPS redirection and HSTS |
| `SECRET_KEY` | *(sample key)* | *(random 64-char hex)* | JWT signing secret |
| `CORS_ORIGINS` | `http://localhost:3000,...` | `https://yourdomain.com` | Comma-separated allowed CORS origins |
| `RATE_LIMIT_PER_MINUTE` | `120` | `120` | Max API requests allowed per client IP |
| `MAX_IMAGE_SIZE_MB` | `10` | `10` | Maximum allowed image upload payload |
| `SENTRY_DSN` | `""` | `https://...` | Error tracking and security alerts |
