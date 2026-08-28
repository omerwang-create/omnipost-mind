"""Minds Builder Hub client. Base: https://api.build.hellominds.ai"""
import base64, json, os, time, requests
from dotenv import load_dotenv

BASE = "https://api.build.hellominds.ai"
load_dotenv()

# 复用连接池，避免高频轮询时频繁新建 TLS 连接被服务器断开
_SESSION = requests.Session()


def _req(method, path, **kw):
    headers = {"X-Api-Key": os.environ["MINDS_API_KEY"]}
    last = None
    for attempt in range(4):
        try:
            r = _SESSION.request(method, BASE + path, headers=headers, **kw)
        except requests.exceptions.SSLError as e:
            # 服务器断开了空闲的 keep-alive 连接，关闭连接池强制重建 TLS
            last = e
            _SESSION.close()
            time.sleep(1.0 * (attempt + 1))
            continue
        except requests.exceptions.RequestException as e:
            last = e
            time.sleep(1.0 * (attempt + 1))
            continue
        if r.status_code < 500:
            r.raise_for_status()
            return r.json()
        last = r
        time.sleep(1.5 * (attempt + 1))
    if isinstance(last, requests.Response):
        last.raise_for_status()
    raise last


def _human_id():
    p = os.environ["MINDS_API_KEY"].split(".")[1]
    p += "=" * (-len(p) % 4)
    return json.loads(base64.urlsafe_b64decode(p))["humanId"]


def list_minds():
    return _req("GET", f"/v1/humans/{_human_id()}/minds")


def ensure_conversation(alias, mind_id):
    try:
        return _req("POST", "/v1/messaging/conversation",
                    json={"alias": alias, "mindId": mind_id})
    except requests.HTTPError as e:
        if e.response.status_code != 400 or "already exists" not in e.response.text:
            raise
        return _req("GET", f"/v1/messaging/conversations/{alias}")


def send_message(alias, text):
    return _req("POST", "/v1/messaging/message",
                json={"alias": alias, "messageText": text})


def get_history(alias, limit=20):
    return _req("GET", f"/v1/messaging/histories/{alias}", params={"limit": limit})


if __name__ == "__main__":
    minds = list_minds()
    assert minds, "no minds on account"
    print([m["name"] for m in minds])
