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
docker compose up -d           # http://localhost:8080 (builds from this checkout)
# or
docker build -t chummer-web .
# nothing in the image is written to at run time, so run it locked down —
# `compose.yaml` does the same, and CI smoke-tests this exact shape
docker run --rm -p 8080:8080 \
  --read-only --security-opt no-new-privileges:true --cap-drop ALL \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --tmpfs /app/frontend/.next/cache:rw,noexec,nosuid,size=16m \
  chummer-web
```

`compose.yaml` sets `pull_policy: build`, so the image is rebuilt from the
checkout on every `up`. Cached, that costs seconds, and it is what keeps the
image in step with the file starting it: the read-only / `--cap-drop ALL`
runtime needs the Dockerfile's `setcap -r` on the caddy binary, and an image
predating that fails to exec caddy (`EPERM`) under the compose file that asks
for it. Reusing whatever image the host happens to have turns that into a
container that never becomes healthy.

CI builds the same image for `linux/amd64` and `linux/arm64`, each on its own
native runner, smoke-tests both locked down, and only then joins the two
digests into one tag — so a pull gets the right architecture and never gets an
image that failed to start. It publishes to `ghcr.io/<owner>/chummer-web`, but
a GHCR package is private when first created whatever the repository's
visibility: `docker compose pull` fails with `unauthorized` until someone flips
it once in the package settings. Building is the path that always works; pull
explicitly when you have access and want to skip the build.

### Checking what you pulled

Every published tag is signed, and carries an SBOM of what is actually in its
layers. Both claims are attached to the manifest list — the digest a `docker
pull` resolves — so one check covers both architectures.

```sh
owner=<owner>   # the GitHub account or org the image was published from

# who built it: the signature names the workflow, ref and commit
cosign verify ghcr.io/$owner/chummer-web:latest \
  --certificate-identity-regexp "^https://github.com/$owner/chummer-web/" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

# what is in it
cosign download attestation ghcr.io/$owner/chummer-web:latest \
  | jq -r '.payload | @base64d | fromjson | .predicate' > sbom.spdx.json
grype sbom:sbom.spdx.json      # or any SPDX reader
```

Signing is keyless: there is no public key to distribute, and nothing to rotate.
The certificate is issued to the workflow itself, which is why the identity to
check is a URL rather than a fingerprint — `--certificate-identity-regexp`
above accepts any workflow in that repository, so narrow it to
`.../ci.yml@refs/heads/main` if you want to pin the ref as well. The same SBOM
is on the workflow run as an artifact, for comparing two releases without
cosign.

The Chummer game data is fetched at **build time** (`fetch_chummer_data.py`,
pinned to `CHUMMER_REF`) and baked into the image — no network needed at
runtime. Move the pin with `--build-arg CHUMMER_REF=<sha>`.

## Runtime env

| var | default | note |
| --- | --- | --- |
| `PORT` | `8080` | port Caddy listens on |
| `ALLOWED_ORIGINS` | `localhost:3000` list | only matters for a split deploy (frontend on another origin) |
| `RATE_LIMIT` | `120/minute` | per client IP, all routes |
| `IMPORT_RATE_LIMIT` | `20/minute` | per client IP, the XML-handling routes (imports, settings / customdata upload, .chum5 export and its check) |
| `CSP_REPORT_RATE_LIMIT` | `60/minute` | per client IP, `/api/csp-report` |
| `MAX_REQUEST_BYTES` | `12582912` | 413 above this, chunked bodies included; the bundled Caddy enforces it too |
| `CHUM5_MAX_DECOMPRESSED_BYTES` | `33554432` | `.chum5lz` decompression-bomb cap |
| `TRUSTED_PROXY_HOPS` | `0` | entries in from the right of `x-forwarded-for` that hold the real client |
| `TRUST_CLOUDFLARE_IP` | unset | `1` behind Cloudflare, which sets `cf-connecting-ip`; ignored otherwise |
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

**CSP violations.** The page's Content-Security-Policy names
`/api/csp-report`, and a violation arrives there as one `info` line:

```json
{"level":"INFO","message":"csp violation: script-src-elem blocked https://evil.test/x.js",
 "csp_report":{"document-uri":"https://…/chargen","effective-directive":"script-src-elem",
 "blocked-uri":"https://evil.test/x.js","disposition":"enforce"},"client":"203.0.113.7"}
```

`info` rather than `warning` on purpose: browser extensions and injected page
scripts produce a steady trickle on any public deployment, so the interesting
signal is a *change* in what is reported, not the presence of reports. Only the
fields above are kept, each truncated, and the endpoint answers 204 to anything
— it is the one route whose body is written by something other than our own
client. Turn it down with `CSP_REPORT_RATE_LIMIT`.

**Client IP for rate limiting.** No forwarded header is trusted by default — a
client talking straight to the app can forge one and take one request per fake
IP, straight past every limit. Say what sits in front:

- **Cloudflare (Tunnel or proxied DNS)** — `TRUST_CLOUDFLARE_IP=1`, which reads
  `cf-connecting-ip`; Cloudflare overwrites it on the way in. Without the flag
  the header is ignored, because anywhere else the caller writes it.
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
  --max-instances 1 \
  --set-env-vars TRUSTED_PROXY_HOPS=2   # rate-limit on the real client IP
```

Cloud Run sets `PORT`; the container already honours it. Scale-to-zero is fine
— the first request after idle pays the container start + the one-off
`catalog()` XML parse.

- **`--max-instances 1`** — the rate limiter counts in process memory, so a
  second instance would hand out a second full allowance. It is also the cost
  ceiling.
- **Billing is per request** (CPU and memory only while a request is being
  handled, plus start-up), so a small group's use usually stays inside the
  monthly free tier. `--min-instances 1` removes cold starts but bills the idle
  instance around the clock (roughly $10/month at this size).
- **Budget alert** — Billing › Budgets & alerts, e.g. $5 on the project.
- **Custom domain** — `gcloud beta run domain-mappings create --service
  chummer-web --domain chummer.example.com --region asia-northeast1`, then add
  the DNS record it prints. On Cloudflare DNS, keep that record **DNS only**
  (grey cloud): Google issues the certificate and needs to see its own
  endpoint.

**Do not put Cloudflare's proxy in front and set `TRUST_CLOUDFLARE_IP=1`.** The
`*.run.app` URL stays open to anyone, and a caller going there directly writes
`cf-connecting-ip` themselves — one request per fake IP, past every limit.
Closing `run.app` so that only Cloudflare can reach the service takes an
external HTTPS load balancer (`--ingress internal-and-cloud-load-balancing`),
whose fixed monthly fee outweighs the rest of this bill. If you want
Cloudflare's WAF, use the Cloudflare Containers setup instead. Here the
defence is the app's own limits on the platform-appended client IP
(`TRUSTED_PROXY_HOPS=2`), and `--max-instances 1` caps the bill.

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

## Cloudflare Containers

Everything on Cloudflare: a Worker takes the request and hands it to a container
running this same image. Needs the Workers Paid plan and a zone (your domain)
on the same account. Config lives in `deploy/cloudflare/`.

```bash
cd deploy/cloudflare
# edit wrangler.jsonc: routes[0].pattern -> your hostname
npm install
npx wrangler login
npx wrangler deploy        # builds the image locally with Docker, pushes, deploys
```

The image is built for `linux/amd64`. On an Apple Silicon Mac that runs under
emulation and the first build takes a long while; later ones reuse the cache.

What the config pins down, and why:

- **One instance** (`max_instances: 1`, and the Worker always asks for the
  instance named `main`). The rate limiter keeps its counters in process
  memory, so several containers would each hand out a full allowance. It is
  also the cost ceiling: nobody can make you run a second container.
- **`standard-1`** (1/2 vCPU, 4 GiB). `basic` fits in memory but makes the
  cold-start catalog parse slow.
- **`sleepAfter = "15m"`** — idle that long and it stops; billing is per
  running second, so a quiet instance costs little. Lengthen it to avoid cold
  starts, shorten it to pay less.
- **`TRUST_CLOUDFLARE_IP=1`** and the public rate limits (`120/minute`,
  `20/minute`) are set in `src/index.ts` (`envVars`), not `.env` — `.env` is
  only read by `docker compose`. The container is reachable only through the
  Worker, so `cf-connecting-ip` there is always Cloudflare's.
- **`workers_dev: false`, `preview_urls: false`** — the custom domain is the only
  public URL, so the WAF rules below cannot be walked around via
  `*.workers.dev`.

Logs: `npx wrangler tail`, or Workers & Pages › chummer-web › Logs in the
dashboard (the container writes JSON lines, `LOG_FORMAT=json`).

### Before going public

The app keeps no data (no accounts, characters stay in the browser), so the
realistic risk is someone burning CPU on your bill. In the dashboard, for the
zone:

1. **Security › WAF › Rate limiting rules** — one rule for
   `starts_with(http.request.uri.path, "/api/")`, e.g. 100 requests / 1 minute
   per IP → Block for 1 minute. This stops a flood at the edge, before it wakes
   the container. The app's own limits stay as the second line.
2. **Security › Bots** — turn on Bot Fight Mode.
3. **Billing › Billable usage notifications** — an alert for Workers /
   Containers usage, so a surprise shows up as an email, not an invoice.
4. **SSL/TLS** — mode *Full*, *Always Use HTTPS* on, minimum TLS 1.2.
5. **Small audience?** Put **Zero Trust › Access** on the hostname (e.g. email
   one-time PIN for your group). Anonymous visitors then never reach the
   Worker at all.
6. **Keep the image fresh.** Base images are pinned by digest; redeploy after
   taking the Dependabot / `make update` bumps, or security fixes in Python,
   Node and Caddy never reach the running container.

Sanity check afterwards: `curl -i https://<host>/api/health`, then fire
requests past the limit and confirm the 429 / log line shows your own IP.

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
