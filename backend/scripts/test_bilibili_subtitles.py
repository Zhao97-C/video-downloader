"""Integration test: Bilibili parse + subtitles API."""
import json
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8000"
URL = "https://www.bilibili.com/video/BV1JaL86oEWs/"


def main() -> int:
    client = httpx.Client(timeout=120.0)
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpass123"

    print("=== 1. Health ===")
    r = client.get(f"{BASE}/api/health")
    print(r.status_code, r.json())

    print("\n=== 2. Parse Bilibili ===")
    r = client.post(f"{BASE}/api/parse", json={"url": URL, "mode": "auto"})
    print("status:", r.status_code)
    if r.status_code != 200:
        print(r.text)
        return 1
    parse_data = r.json()
    print("title:", parse_data.get("title", "")[:60])
    print("platform:", parse_data.get("platform"))
    print("has_subtitles:", parse_data.get("has_subtitles"))
    print("subtitle_languages:", parse_data.get("subtitle_languages"))
    task_id = parse_data["task_id"]
    print("task_id:", task_id)

    print("\n=== 3. Register + Login ===")
    r = client.post(f"{BASE}/api/auth/register", json={"email": email, "password": password})
    print("register:", r.status_code, r.json() if r.status_code == 200 else r.text)
    token = r.json().get("access_token") if r.status_code == 200 else None
    if not token:
        r = client.post(f"{BASE}/api/auth/login", json={"email": email, "password": password})
        token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    print("\n=== 4. Subtitles (login required) ===")
    r = client.post(f"{BASE}/api/ai/subtitles", json={"task_id": task_id}, headers=headers)
    print("status:", r.status_code)
    if r.status_code != 200:
        print(r.text)
        return 1
    subs = r.json()
    print("source:", subs.get("source"))
    print("language:", subs.get("language"))
    print("extraction_method:", subs.get("extraction_method"))
    print("char_count:", subs.get("char_count"))
    print("segments:", len(subs.get("segments", [])))
    preview = (subs.get("plain_text") or "")[:400]
    print("plain_text preview:")
    print(preview.encode("utf-8", errors="replace").decode("utf-8"))

    print("\n=== 5. Subtitles cache (second call) ===")
    r2 = client.post(f"{BASE}/api/ai/subtitles", json={"task_id": task_id}, headers=headers)
    print("status:", r2.status_code, "method:", r2.json().get("extraction_method"))

    print("\n=== OK ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
