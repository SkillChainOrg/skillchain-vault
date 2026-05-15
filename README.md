# SkillChain Vault Service

This repository is the isolated vault-service for SkillChain. It is intentionally
limited to secret storage and future cryptographic boundary preparation.

## What it does

- Stores artisan secrets through a storage abstraction
- Uses real HashiCorp Vault KV v2 when enabled and reachable
- Falls back to lightweight local storage when Vault is disabled or unavailable
- Exposes demo-only HTTP endpoints for health and storage verification

## What it does not do

- Provenance or artwork business logic
- Commerce or x402 flows
- Ownership mutation
- DID issuance
- Vault Transit signing

## Local development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` into `.env` and adjust values if needed.

3. Optional: start a local Vault dev server:

```bash
vault server -dev -dev-root-token-id=dev-only-token
```

4. Start the Flask service:

```bash
python app.py
```

## Demo endpoints

- `GET /health`
- `POST /store-test-secret`
- `GET /load-test-secret/<artisan_id>`

When Vault is enabled and reachable, secrets are stored under the KV v2 path:

`secret/skillchain/artisan/<artisan_id>`
