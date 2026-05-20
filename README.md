# skillchain-vault

Isolated key/secret management service for [SkillChain](https://frontend-rho-eight-42.vercel.app/).

This service exists for one reason: to keep sensitive storage responsibilities out of the main backend. It has no knowledge of provenance logic, x402 flows, or artwork business rules.

---

## What This Service Does

- Stores artisan-related secrets through a storage abstraction layer
- Uses HashiCorp Vault KV v2 when enabled and reachable
- Falls back to local storage when Vault is unavailable (development / demo)
- Exposes simple endpoints for storage verification and health checks

## What This Service Does Not Do

This repository deliberately does not handle:

- Provenance recording or verification
- x402 acquisition flows
- DID issuance or resolution
- Ownership mutation or blockchain settlement
- Vault Transit signing
- Artwork marketplace logic

All of that lives in the [backend](https://github.com/SkillChainOrg/backend).

---

## Architecture

```
Frontend / Backend Services
        ↓
  Vault Service API (Flask)
        ↓
  Storage Abstraction Layer
        ↓
  HashiCorp Vault KV v2     ←── when VAULT_ENABLED=true and reachable
  OR
  Local Fallback Storage    ←── when Vault is disabled or unavailable
```

The storage abstraction means the calling service doesn't need to know which backend is active. The vault service resolves that internally and responds uniformly.

---

## Getting Started

### Prerequisites

- Python 3.10+
- [HashiCorp Vault](https://developer.hashicorp.com/vault/install) (optional — local dev server works fine)

---

### 1. Clone the Repository

```bash
git clone https://github.com/SkillChainOrg/skillchain-vault.git
cd skillchain-vault
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

#### Environment Variable Reference

```env
# --- Flask ---
FLASK_ENV=development
SECRET_KEY=your-flask-secret-key
PORT=5001

# --- Vault ---
# Set to true to use HashiCorp Vault KV v2
VAULT_ENABLED=false

# Address of your local or remote Vault instance
VAULT_ADDR=http://127.0.0.1:8200

# Root or app-role token for Vault authentication
VAULT_TOKEN=your-vault-token

# KV v2 mount path (default is "secret")
VAULT_MOUNT=secret

# --- Backend Integration ---
# The backend uses this key to authenticate requests to the vault service
VAULT_ADMIN_KEY=your-admin-key
```

| Variable | Purpose |
|---|---|
| `VAULT_ENABLED` | Switches between HashiCorp Vault and local fallback storage. Set `false` for local development. |
| `VAULT_ADDR` | Address of your Vault instance. The local dev server defaults to `http://127.0.0.1:8200`. |
| `VAULT_TOKEN` | Auth token for Vault. In development, the dev server provides a root token on startup. |
| `VAULT_ADMIN_KEY` | Shared secret the backend must include when calling the vault service. Keep this out of version control. |

---

### 5. (Optional) Start a Local Vault Dev Server

If you want to test with real Vault KV v2 rather than the local fallback:

```bash
vault server -dev
```

Vault will print a root token on startup. Copy it into `VAULT_TOKEN` in your `.env`, set `VAULT_ENABLED=true`, and the service will use KV v2 automatically.

Secrets are stored under:

```
secret/skillchain/artisan/<artisan_id>
```

When the dev server is not running or `VAULT_ENABLED=false`, the service falls back to local storage silently — no configuration change required.

---

### 6. Run the Vault Service

```bash
flask run --port 5001
```

The service will be available at `http://localhost:5001`.

---

### 7. Connect to the Backend

In your backend `.env`, point `VAULT_URL` at the running vault service:

```env
VAULT_URL=http://localhost:5001
VAULT_ADMIN_KEY=your-admin-key   # must match the vault service's VAULT_ADMIN_KEY
```

The backend delegates all signing and secret storage requests to this address.

---

## API Endpoints

### `GET /health`

Returns service status and indicates which storage backend is active.

```json
{
  "status": "ok",
  "storage_backend": "vault"   // or "local"
}
```

---

### `POST /store-test-secret`

Stores a test secret for a given artisan. Used for verifying storage connectivity.

**Request**
```json
{
  "artisan_id": "artisan_abc123",
  "secret": "test-value"
}
```

**Response**
```json
{
  "stored": true,
  "artisan_id": "artisan_abc123",
  "backend": "vault"
}
```

---

### `GET /load-test-secret/<artisan_id>`

Retrieves the stored test secret for a given artisan ID.

**Response**
```json
{
  "artisan_id": "artisan_abc123",
  "secret": "test-value",
  "backend": "local"
}
```

---

## Storage Fallback Behavior

| Condition | Storage Used |
|---|---|
| `VAULT_ENABLED=true` and Vault is reachable | HashiCorp Vault KV v2 |
| `VAULT_ENABLED=true` and Vault is unreachable | Local fallback |
| `VAULT_ENABLED=false` | Local fallback |

The fallback is intentional — it keeps local development and demo flows running without requiring a Vault instance. It is not intended for production use.

---

## Related Repositories

| Repo | Purpose |
|---|---|
| [SkillChainOrg/backend](https://github.com/SkillChainOrg/backend) | Main API — provenance, x402 flows, Algorand integration |
| [SkillChainOrg/frontend](https://github.com/SkillChainOrg/frontend) | React + Vite frontend, deployed on Vercel |

---

## License

MIT
