from django.conf import settings


def get_sslcommerz_client():
    """
    Create an SSLCOMMERZ client from Django settings.
    """
    try:
        from sslcommerz_lib import SSLCOMMERZ
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "sslcommerz-lib is not installed. Run: pip install sslcommerz-lib"
        ) from exc

    store_id = getattr(settings, "SSLCOMMERZ_STORE_ID", "")
    store_pass = getattr(settings, "SSLCOMMERZ_STORE_PASS", "")
    issandbox = getattr(settings, "SSLCOMMERZ_ISSANDBOX", True)

    if not store_id or not store_pass:
        raise RuntimeError(
            "Missing SSLCOMMERZ credentials. Set SSLCOMMERZ_STORE_ID and SSLCOMMERZ_STORE_PASS."
        )

    sslcz_settings = {"store_id": store_id, "store_pass": store_pass, "issandbox": issandbox}
    return SSLCOMMERZ(sslcz_settings)










