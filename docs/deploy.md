# Deploy

One container. Caddy fronts the FastAPI backend and the Next.js standalone
server, supervised by `supervisord`.

```
                       ┌──────────── container ────────────┐
  client ──TLS(edge)──▶ :$PORT  caddy ─┬─ /api/* ─▶ :8000  uvicorn (rules engine)
                       │                └─ /*     ─▶ :3000  next  (standalone)
                       └───────────────────────────────────┘
```

The backend is stateless (see `docs/stateless-refactor.md`); characters live in
the browser. Nothing to back up, safe to scale to zero / run many instances.

## Build & run locally

```bash
docker compose up --build      # http://localhost:8080
# or
docker build -t chummer-web .
docker run --rm -p 8080:8080 chummer-web
```

The Chummer game data is fetched at **build time** (`fetch_chummer_data.py`,
pinned to `CHUMMER_REF`) and baked into the image — no network needed at
runtime. Move the pin with `--build-arg CHUMMER_REF=<sha>`.

## Runtime env

| var | default | note |
| --- | --- | --- |
| `PORT` | `8080` | port Caddy listens on |
| `ALLOWED_ORIGINS` | `localhost:3000` list | only matters for a split deploy (frontend on another origin) |
| `RATE_LIMIT` | `120/minute` | per client IP, all routes |
| `IMPORT_RATE_LIMIT` | `20/minute` | per client IP, the two import routes |
| `MAX_REQUEST_BYTES` | `12582912` | 413 above this |
| `CHUM5_MAX_DECOMPRESSED_BYTES` | `33554432` | `.chum5lz` decompression-bomb cap |

Client IP is read from `cf-connecting-ip` / the first `x-forwarded-for` hop,
so rate limiting works behind Cloudflare or a platform load balancer.

Health check: `GET /api/health` (also the image `HEALTHCHECK`).

## Google Cloud Run

```bash
gcloud run deploy chummer-web \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 512Mi --cpu 1 \
  --min-instances 0        # 1 to kill cold starts (~catalog parse); costs a bit
```

Cloud Run sets `PORT`; the container already honours it. Scale-to-zero is fine
— the first request after idle pays the container start + the one-off
`catalog()` XML parse.

## Fly.io

`fly launch` detects the Dockerfile. A minimal `fly.toml`:

```toml
app = "chummer-web"
primary_region = "nrt"

[build]

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0        # 1 for no cold starts

[[vm]]
  size = "shared-cpu-1x"
  memory = "512mb"

[checks.health]
  type = "http"
  path = "/api/health"
  interval = "30s"
  timeout = "3s"
```

## Self-host + Cloudflare Tunnel

Run the container (`docker compose up -d`), then point a named tunnel at it:

```
# ~/.cloudflared/config.yml
tunnel: <tunnel-id>
credentials-file: /home/you/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: chummer.example.com
    service: http://localhost:8080
  - service: http_status:404
```

Put **Cloudflare Access** in front if the audience is small — it removes the
anonymous-abuse surface entirely. Run the container on an isolated network
segment / dedicated device; the tunnel needs only outbound 443.

## Notes

- Single uvicorn worker. `compute()` is CPU-bound and runs in FastAPI's
  threadpool, so a handful of concurrent edits are fine on 1 vCPU. Bump with a
  custom `--workers N` in `deploy/supervisord.conf` if needed (each worker
  keeps its own `catalog()` cache → memory ×N).
- GPL-3.0: `LICENSE` and `NOTICE.txt` are in the image at `/app/`. Keep the
  repo reachable (public, or a source tarball) so users can get the source.
