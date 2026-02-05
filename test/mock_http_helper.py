import os
import json
from urllib.parse import urlparse, parse_qs
from requests.models import Response


def _params_to_filename(params_dict):
    return "_".join([f"{k}-{v[0]}" for k, v in sorted(params_dict.items())])


def make_base_path_from_url(url: str):
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path.strip("/") or "root"
    param_str = _params_to_filename(parse_qs(parsed.query)) or "default"
    return os.path.join("data", "test", "api", host, *path.split("/"), param_str)


def save_response(response: Response, base_path: str):
    os.makedirs(os.path.dirname(base_path), exist_ok=True)

    raw_text = response.text
    content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()

    # Check if it's really JSON (even with wrong MIME type e.g. from SwissLipids)
    is_json = False
    try:
        parsed_json = response.json()
        is_json = True
    except Exception:
        parsed_json = None

    if is_json:
        with open(base_path + ".json", "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, indent=2)
        detected_type = "application/json"
    elif content_type in ["text/html", "application/xml", "text/xml"]:
        ext = ".html" if "html" in content_type else ".xml"
        with open(base_path + ext, "w", encoding="utf-8") as f:
            f.write(raw_text)
        detected_type = content_type
    else:
        with open(base_path + ".txt", "w", encoding="utf-8") as f:
            f.write(raw_text)
        detected_type = content_type

    # Save metadata (always use the detected MIME type)
    meta = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "content_type": detected_type,
    }
    with open(base_path + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def load_response(base_path: str) -> Response:
    # Load metadata first
    with open(base_path + ".meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    content_type = meta.get("content_type", "text/plain")
    status_code = meta.get("status_code", 200)
    headers = meta.get("headers", {})

    # Determine content type
    if content_type == "application/json":
        with open(base_path + ".json", "r", encoding="utf-8") as f:
            content = json.dumps(json.load(f))  # JSON string
    elif content_type in ["text/html", "application/xml", "text/xml"]:
        ext = ".html" if "html" in content_type else ".xml"
        with open(base_path + ext, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        with open(base_path + ".txt", "r", encoding="utf-8") as f:
            content = f.read()

    # Rebuild response object
    response = Response()
    response.status_code = status_code
    response._content = content.encode("utf-8")
    response.headers = headers
    response.encoding = "utf-8"
    return response


def load_or_record_response(url, real_execute_http_query, test_development=True):
    base_path = make_base_path_from_url(url)

    if os.path.exists(base_path + ".meta.json"):
        return load_response(base_path)

    elif test_development:
        response = real_execute_http_query(url)
        save_response(response, base_path)
        return response
    else:
        raise FileNotFoundError(f"No mock file found for {url}")
