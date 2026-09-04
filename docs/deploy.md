# Deploy

One container. Caddy fronts the FastAPI backend and the Next.js standalone
server, supervised by `supervisord`.

```
                       ┌──────────── container ────────────┐
  client ──TLS(edge)──▶ :$PORT  caddy ─┬─ /api/* ─▶ :8000  uvicorn (rules engine)
                       │                └─ /*     ─▶ :3000  next  (standalone)
                       └───────────────────────────────────┘
```

The backend is stateless (see `docs/plans/stateless-refactor.md`); characters live in
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
| `TRUSTED_PROXY_HOPS` | `0` | entries in from the right of `x-forwarded-for` that hold the real client |
| `LOG_FORMAT` | `text` | `json` for one object per line |
| `LOG_LEVEL` | `INFO` | root level |

**Logs.** Every response carries `X-Request-ID`, and every log line carries the
same id, so a user quoting the header from their network tab is enough to find
the request. With `TRUSTED_PROXY_HOPS` above 0 an `X-Request-ID` from the edge
is adopted instead, so one id spans the whole hop chain (at 0 the header is
attacker-controlled and is ignored, same rule as the forwarded IP below). The
access line is written by the app, not uvicorn — `uvicorn.access` is quieted to
avoid a second, less useful copy.

`LOG_FORMAT=json` gives one object per line:

```json
{"ts":"…","level":"INFO","logger":"chummer_web","message":"POST /api/characters/patch -> 200 in 41.2ms",
 "request_id":"9f0c1d2e3a4b","method":"POST","path":"/api/characters/patch","status":200,
 "duration_ms":41.2,"client":"203.0.113.7"}
```

Request bodies, query strings and anything derived from a `CharacterState` are
never logged. Characters are the user's and never touch disk on the server; a
log line is disk.

**Client IP for rate limiting.** `cf-connecting-ip` is always trusted
(Cloudflare overwrites it). `x-forwarded-for` is *not* trusted by default — a
client talking straight to the app can forge it and take one request per fake
IP, straight past every limit. If a proxy you control sits in front, set
`TRUSTED_PROXY_HOPS` to the position (counting from the right) of the entry that
proxy chain records the client at:

- **Cloudflare Tunnel** — leave `0`; `cf-connecting-ip` covers it.
- **Cloud Run / Fly.io** — `2` (the platform appends `client, lb-ip`).
- **One self-managed nginx/Caddy** that appends the connecting peer — `1`.

Sanity-check after deploy: hit it from a known IP and confirm that IP (not the
LB's) shows up in a 429 / log line.

Health check: `GET /api/health` (also the image `HEALTHCHECK`).

## Google Cloud Run

```bash
gcloud run deploy chummer-web \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 512Mi --cpu 1 \
  --min-instances 0 \
  --set-env-vars TRUSTED_PROXY_HOPS=2   # rate-limit on the real client IP
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

[env]
  TRUSTED_PROXY_HOPS = "2"   # rate-limit on the real client IP, not fly's edge

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
