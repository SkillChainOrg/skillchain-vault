import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

from storage import load_artisan_secret, store_artisan_secret, vault_client

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = Flask(__name__)

SERVICE_NAME = os.getenv("VAULT_SERVICE_NAME", "skillchain-vault")
PORT = int(os.getenv("PORT", 8000))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": SERVICE_NAME,
        "vault_enabled": vault_client.enabled,
        "vault_connected": vault_client.vault_available(),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }), 200


@app.route("/store-test-secret", methods=["POST"])
def store_test_secret():
    payload = request.get_json(silent=True) or {}
    artisan_id = payload.get("artisan_id")
    secret = payload.get("secret")

    if not artisan_id or secret is None:
        return jsonify({
            "error": "artisan_id and secret are required",
        }), 400

    result = store_artisan_secret(artisan_id=artisan_id, secret_data=secret)
    return jsonify({
        "status": "stored",
        "artisan_id": artisan_id,
        **result,
    }), 200


@app.route("/load-test-secret/<artisan_id>", methods=["GET"])
def load_test_secret(artisan_id: str):
    result = load_artisan_secret(artisan_id)
    if result is None:
        return jsonify({
            "error": "secret not found",
            "artisan_id": artisan_id,
        }), 404

    return jsonify({
        "status": "loaded",
        "artisan_id": artisan_id,
        **result,
    }), 200


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "message": "SkillChain Vault Service",
        "status": "running"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
