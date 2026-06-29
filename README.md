# wfs

A generic **S3-compatible storage gateway** built with FastAPI and deployed on
**Cloudflare Containers**. Point it at any S3-compatible backend (Cloudflare R2,
AWS S3, MinIO, …) via environment variables.

## Architecture

```
Internet → Cloudflare edge → Worker (src/worker/index.js) → Container (Dockerfile → uvicorn → FastAPI)
```

- **`src/wfs/`** — the FastAPI application (all real logic lives here).
- **`src/worker/`** — a thin Cloudflare Worker that proxies requests to the
  container. Required by the Cloudflare Containers model; stays tiny.
- **`Dockerfile`** — builds the FastAPI image that runs in the container.
- **`wrangler.jsonc`** — wires the Worker to the container.

## Layout

```
src/wfs/
  main.py              # FastAPI app factory + /health
  config.py            # settings (env-driven)
  controllers/         # HTTP route handlers
  core/                # backend-agnostic storage logic
  models/              # response classes with custom serializers
src/worker/index.js    # Cloudflare Worker (proxy)
tests/                 # pytest suite
scripts/               # setup / dev / test / lint helpers
```

## Getting started

Requires Python 3.11+, [direnv](https://direnv.net/), [`just`](https://github.com/casey/just),
and (for deploys) Node + npm. [`uv`](https://docs.astral.sh/uv/) is used if
present, else stdlib `venv`.

```bash
direnv allow         # creates & activates .venv automatically on cd
just setup           # install Python (+ worker) dependencies
cp .env.example .env # then fill in your S3 backend credentials
```

The venv is created and activated by **direnv** (`.envrc`). After `direnv allow`,
the venv activates automatically whenever you `cd` into the project.

## Common commands

```bash
just            # list all recipes
just run        # run the API locally with hot reload (:8000)
just test       # run the test suite (e.g. `just test -k health`)
just lint       # ruff check + format check
just fmt        # auto-fix lint + format
just build      # build the container image locally
```

Deploys happen automatically via GitHub Actions on push to `main`.

## Configuration

Set via environment (see `.env.example`):

| Variable               | Description                                  |
| ---------------------- | -------------------------------------------- |
| `S3_ENDPOINT_URL`      | S3-compatible endpoint (e.g. R2 endpoint)    |
| `S3_ACCESS_KEY_ID`     | Access key                                   |
| `S3_SECRET_ACCESS_KEY` | Secret key                                   |
| `S3_REGION`            | Region (`auto` for R2)                       |
| `S3_BUCKET`            | Target bucket                                |
| `LOG_LEVEL`            | Log level (default `info`)                   |

## CI/CD

- **`.github/workflows/ci.yml`** — runs ruff + pytest on every PR and on pushes
  to `main`.
- **`.github/workflows/deploy.yml`** — on push to `main` (merged PRs), builds the
  image and deploys to Cloudflare via `wrangler`.

Add these GitHub repo secrets for deploys:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
