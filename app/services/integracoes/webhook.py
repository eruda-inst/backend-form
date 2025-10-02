from typing import Any, Dict
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

def testar(cfg: Dict[str, Any]) -> bool:
    """Dispara HEAD e, em fallback, GET para validar endpoint Webhook."""
    url = cfg.get("url")
    if not url:
        return False
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=4) as resp:
            status = getattr(resp, "status", 200)
            return 200 <= status < 400
    except (HTTPError, URLError):
        try:
            req = Request(url, method="GET")
            with urlopen(req, timeout=4) as resp:
                status = getattr(resp, "status", 200)
                return 200 <= status < 400
        except Exception:
            return False
    except Exception:
        return False