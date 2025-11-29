from tenacity import retry, wait_exponential, stop_after_attempt
import requests

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
def safe_get(url, params=None, timeout=10):
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
