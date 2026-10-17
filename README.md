# wfs

A generic **S3-compatible storage gateway** built with FastAPI and deployed on
**Cloudflare Containers**. Point it at any S3-compatible backend (Cloudflare R2,
AWS S3, MinIO, …) via environment variables.

## Architecture

```
Internet → Cloudflare edge → Worker (src/worker/index.js) → Container (Dockerfile → uvicorn → FastAPI)
```

A thin Cloudflare Worker proxies requests to a container running the FastAPI app.

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
| `PRIVATE_KEY_NAME`     | Private key object name (default `keys/pk.pem`) |
| `PUBLIC_KEY_NAME`      | Public key object name (default `keys/pub.pem`) |
| `JWT_ISSUER`           | JWT `iss` claim (default `wfs`)              |
| `JWT_TTL`              | Token lifetime in seconds (default `3600`)   |

## Auth

On boot the container looks for `PRIVATE_KEY_NAME` / `PUBLIC_KEY_NAME` in the
bucket and generates an RSA keypair into it if either is missing, so a fresh
deploy against a fresh bucket is self-bootstrapping and a redeploy against an
existing one keeps issuing tokens the old keys can still verify.

Clients hold the public key. `POST /login` takes it as the bearer credential and
returns a short-lived RS256 JWT signed with the private key; every other
endpoint takes that JWT as the bearer. An HTTP header cannot carry a PEM's
newlines, so send the key flattened — whitespace-collapsed PEM, base64-wrapped
PEM, and a bare base64 body are all accepted.

```bash
TOKEN=$(curl -sX POST localhost:8000/login \
  -H "Authorization: Bearer $(tr '\n' ' ' < pub.pem)" | jq -r .access_token)

curl -s "localhost:8000/files/get-signed-url?filename=a/b.pdf&method=put" \
  -H "Authorization: Bearer $TOKEN"
```

## API

| Endpoint                | Description                                          |
| ----------------------- | ---------------------------------------------------- |
| `GET /health`           | Liveness probe.                                      |
| `POST /login`           | Public key in, JWT out.                              |
| `GET /files/get-signed-url` | Presigned S3 URL for `filename`. `method=get\|put` (default `get`), `expires_in` seconds (default 3600, max 604800). |

The gateway never proxies file bytes: clients upload and download directly
against the presigned URL.

## Run locally

Requires Python 3.11+, [direnv](https://direnv.net/), [`just`](https://github.com/casey/just),
and Node + npm (for `wrangler`). [`uv`](https://docs.astral.sh/uv/) is used if
present, else stdlib `venv`.

```bash
direnv allow         # creates & activates .venv automatically on cd
just setup           # install dependencies
cp .env.example .env # then fill in your S3 backend credentials
just run             # serve on http://localhost:8000
```

Other recipes: `just test`, `just lint`, `just fmt`, `just build`. Run `just` to
list them all.

## Deploy to Cloudflare

This repo deploys as a [Cloudflare Container](https://developers.cloudflare.com/containers/).
Two options:

**One-off / manual:**

```bash
just deploy
```

**Connect the repo (auto-deploys on push):** in the Cloudflare dashboard, create
a Worker from your Git repo. Cloudflare builds the `Dockerfile` and deploys using
`wrangler.jsonc` on every push — no GitHub Actions or secrets needed.

Set the S3 environment variables (above) on the Worker via the dashboard or
`wrangler secret put`.
