# syntax=docker/dockerfile:1
#
# One container: Caddy fronts a FastAPI (uvicorn) backend and the Next.js
# standalone server, supervised by supervisord.
#
#   /api/*  -> 127.0.0.1:8000  (uvicorn)
#   /*      -> 127.0.0.1:3000  (next)
#   :$PORT  -> caddy           (default 8080; the platform terminates TLS)
#
# Build:  docker build -t chummer-web .
# Run:    docker run --rm -p 8080:8080 chummer-web
# Pin a different Chummer data commit:  --build-arg CHUMMER_REF=<sha>

# ─── 1. frontend: Next standalone bundle ─────────────────────────────────────
FROM node:20-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN mkdir -p public && npm run build
# -> .next/standalone (server.js + traced node_modules), .next/static, public

# ─── 2. python deps into a venv ─────────────────────────────────────────────
FROM python:3.12-bookworm AS pydeps
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt supervisor

# ─── 3. bake the pinned Chummer game data ───────────────────────────────────
FROM python:3.12-slim-bookworm AS chummer
WORKDIR /app/backend
ARG CHUMMER_REF=""
COPY backend/scripts/fetch_chummer_data.py scripts/fetch_chummer_data.py
RUN CHUMMER_REF="$CHUMMER_REF" python scripts/fetch_chummer_data.py
# -> /app/backend/vendor/chummer/{data,lang}  (see NOTICE.txt)

# ─── 4. runtime ────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/venv/bin:/usr/local/bin:$PATH \
    NODE_ENV=production \
    PORT=8080 \
    HOME=/home/app \
    XDG_DATA_HOME=/tmp \
    XDG_CONFIG_HOME=/tmp
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates tini libstdc++6; \
    rm -rf /var/lib/apt/lists/*; \
    useradd --system --create-home --uid 10001 app

# binaries: python venv (+ supervisor + uvicorn), node, caddy
COPY --from=pydeps /opt/venv                        /opt/venv
COPY --from=node:20-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=caddy:2 /usr/bin/caddy                  /usr/bin/caddy

WORKDIR /app
COPY --chown=app:app backend/app                    backend/app
COPY --chown=app:app backend/scripts               backend/scripts
COPY --chown=app:app --from=chummer  /app/backend/vendor            backend/vendor
COPY --chown=app:app --from=frontend /app/frontend/.next/standalone frontend
COPY --chown=app:app --from=frontend /app/frontend/.next/static     frontend/.next/static
COPY --chown=app:app --from=frontend /app/frontend/public           frontend/public
COPY deploy/Caddyfile        /etc/caddy/Caddyfile
COPY deploy/supervisord.conf /etc/supervisord.conf
COPY LICENSE NOTICE.txt      /app/

USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=25s CMD \
  node --no-warnings -e "fetch('http://127.0.0.1:'+(process.env.PORT||8080)+'/api/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

ENTRYPOINT ["tini", "--"]
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
