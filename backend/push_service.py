import os
import json
import logging
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)


def get_vapid_keys() -> tuple[str, str]:
    """Returns (private_key, public_key) from env vars."""
    private_key = os.getenv("VAPID_PRIVATE_KEY", "")
    public_key = os.getenv("VAPID_PUBLIC_KEY", "")
    return private_key, public_key


def send_push_notification(subscription_info: dict, title: str, body: str, url: str = "/") -> bool:
    private_key, _ = get_vapid_keys()
    vapid_email = os.getenv("VAPID_EMAIL", "mailto:admin@sysdesigndaily.app")

    if not private_key:
        logger.warning("VAPID keys not configured, skipping push notification")
        return False

    data = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "icon": "/icon-192.png",
        "badge": "/badge-96.png",
    })

    try:
        webpush(
            subscription_info={
                "endpoint": subscription_info["endpoint"],
                "keys": {
                    "p256dh": subscription_info["p256dh"],
                    "auth": subscription_info["auth"],
                },
            },
            data=data,
            vapid_private_key=private_key,
            vapid_claims={"sub": vapid_email},
        )
        return True
    except WebPushException as e:
        if e.response and e.response.status_code in (404, 410):
            # Subscription expired or invalid — caller should delete it
            raise
        logger.error(f"Push notification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected push error: {e}")
        return False


def generate_vapid_keys() -> tuple[str, str]:
    """Generate a new VAPID key pair. Run once and store in env vars."""
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.backends import default_backend
    import base64

    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    private_numbers = private_key.private_numbers()
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()

    private_bytes = private_numbers.private_value.to_bytes(32, "big")
    private_b64 = base64.urlsafe_b64encode(private_bytes).rstrip(b"=").decode()

    public_x = public_numbers.x.to_bytes(32, "big")
    public_y = public_numbers.y.to_bytes(32, "big")
    public_bytes = b"\x04" + public_x + public_y
    public_b64 = base64.urlsafe_b64encode(public_bytes).rstrip(b"=").decode()

    return private_b64, public_b64
