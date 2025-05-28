import certifi
import orjson
import urllib3

_CONTENT_TYPES = {
    bytes: "application/octet-stream",
    str: "text/plain",
}


def _request(method, url, data):
    from .utils import get_environment

    env = get_environment()

    if data is None:
        data = data or {}
    content_type = _CONTENT_TYPES.get(type(data), "application/json")

    if content_type == "application/json":
        data = orjson.dumps(data, option=orjson.OPT_SERIALIZE_NUMPY)

    if isinstance(data, str):
        data = data.encode("utf-8")

    url = env.backend_api_url + url
    headers = {
        "Content-type": content_type,
        "Authorization": env.backend_api_token,
        "X-Client-Id": env.backend_api_client_id,
    }
    http = urllib3.PoolManager(
        cert_reqs="CERT_REQUIRED", ca_certs=certifi.where()
    )
    response = http.request(method, url, headers=headers, body=data)
    content_type = response.headers.get("content-type", "")
    data = response.data
    if "application/json" in content_type:
        data = orjson.loads(response.data)
    if "text/" in content_type:
        data = response.data.decode("utf-8")
    if response.status >= 400:
        raise RuntimeError(
            f"Request failed: {response.status}, {url}, {data}", url, data
        )
    return data


def encode_url_params(**kwargs):
    return "&".join(f"{k}={v}" for k, v in kwargs.items())


def get(url, data=None):
    return _request("GET", url, data)


def post(url, data):
    return _request("POST", url, data)


def put(url, data):
    return _request("PUT", url, data)


def delete(url, data=None):
    return _request("DELETE", url, data)
