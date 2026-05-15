import json
import logging
from pathlib import Path
from typing import Any

from vault_client import VaultClient


logger = logging.getLogger(__name__)

LOCAL_STORAGE_DIR = Path(__file__).resolve().parent / "data"
LOCAL_STORAGE_FILE = LOCAL_STORAGE_DIR / "artisan_secrets.json"
VAULT_ARTISAN_PREFIX = "skillchain/artisan"

vault_client = VaultClient()


def _vault_path(artisan_id: str) -> str:
    return f"{VAULT_ARTISAN_PREFIX}/{artisan_id}"


def _read_local_store() -> dict[str, Any]:
    if not LOCAL_STORAGE_FILE.exists():
        return {}

    try:
        return json.loads(LOCAL_STORAGE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Local fallback store is unreadable; returning empty store.")
        return {}


def _write_local_store(data: dict[str, Any]) -> None:
    LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_STORAGE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def store_artisan_secret(artisan_id: str, secret_data: Any) -> dict[str, Any]:
    payload = {"artisan_id": artisan_id, "secret": secret_data}
    path = _vault_path(artisan_id)

    if vault_client.write_secret(path, payload):
        return {"stored": True, "backend": "vault", "path": f"{vault_client.mount}/{path}"}

    store = _read_local_store()
    store[artisan_id] = payload
    _write_local_store(store)
    logger.info("Stored secret in local fallback storage for artisan_id=%s", artisan_id)
    return {"stored": True, "backend": "local", "path": str(LOCAL_STORAGE_FILE)}


def load_artisan_secret(artisan_id: str) -> dict[str, Any] | None:
    path = _vault_path(artisan_id)
    data = vault_client.read_secret(path)
    if data is not None:
        return {"backend": "vault", "data": data}

    store = _read_local_store()
    local_data = store.get(artisan_id)
    if local_data is None:
        logger.info("No secret found for artisan_id=%s in Vault or local fallback.", artisan_id)
        return None

    logger.info("Loaded secret from local fallback storage for artisan_id=%s", artisan_id)
    return {"backend": "local", "data": local_data}
