import logging
import os
from typing import Any

from dotenv import load_dotenv

try:
    import hvac
    from hvac.exceptions import InvalidPath, VaultError
except ImportError:
    hvac = None

    class VaultError(Exception):
        pass

    class InvalidPath(VaultError):
        pass


load_dotenv()

logger = logging.getLogger(__name__)


class VaultClient:
    """Lightweight KV v2 wrapper with graceful fallback behavior.

    This service intentionally limits itself to secret storage and future
    cryptographic boundary preparation. Transit signing can be added later
    behind the same abstraction without changing the caller contract.
    """

    def __init__(self) -> None:
        self.enabled = os.getenv("VAULT_ENABLED", "false").lower() == "true"
        self.addr = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.token = os.getenv("VAULT_TOKEN", "dev-only-token")
        self.mount = os.getenv("VAULT_MOUNT", "secret")
        self.timeout = int(os.getenv("VAULT_TIMEOUT_SECONDS", "3"))
        self._client = None

        if not self.enabled:
            logger.info("Vault integration disabled; using fallback storage path.")
            return

        if hvac is None:
            logger.warning("hvac is not installed; Vault integration unavailable, using fallback.")
            return

        try:
            self._client = hvac.Client(url=self.addr, token=self.token, timeout=self.timeout)
            logger.info(
                "Vault integration enabled. Configured address=%s mount=%s",
                self.addr,
                self.mount,
            )
        except Exception as exc:
            logger.warning("Vault client initialization failed; fallback will be used: %s", exc)
            self._client = None

    def vault_available(self) -> bool:
        if not self.enabled or self._client is None:
            return False

        try:
            available = bool(self._client.is_authenticated())
            if available:
                logger.info("Vault connectivity check succeeded.")
            else:
                logger.warning("Vault connectivity check failed: client is not authenticated.")
            return available
        except Exception as exc:
            logger.warning("Vault connectivity check failed; fallback will be used: %s", exc)
            return False

    def write_secret(self, path: str, data: dict[str, Any]) -> bool:
        if not self.vault_available():
            logger.info("Vault unavailable for write to %s; caller should use fallback.", path)
            return False

        try:
            self._client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=self.mount,
            )
            logger.info("Stored secret in Vault KV v2 at %s/%s", self.mount, path)
            return True
        except VaultError as exc:
            logger.warning("Vault write failed for %s; fallback will be used: %s", path, exc)
            return False
        except Exception as exc:
            logger.warning("Unexpected Vault write failure for %s: %s", path, exc)
            return False

    def read_secret(self, path: str) -> dict[str, Any] | None:
        if not self.vault_available():
            logger.info("Vault unavailable for read from %s; caller should use fallback.", path)
            return None

        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount,
            )
            data = response.get("data", {}).get("data")
            logger.info("Loaded secret from Vault KV v2 at %s/%s", self.mount, path)
            return data
        except InvalidPath:
            logger.info("Vault secret not found at %s/%s", self.mount, path)
            return None
        except VaultError as exc:
            logger.warning("Vault read failed for %s; fallback will be used: %s", path, exc)
            return None
        except Exception as exc:
            logger.warning("Unexpected Vault read failure for %s: %s", path, exc)
            return None
