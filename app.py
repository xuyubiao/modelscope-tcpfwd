#!/usr/bin/env python3
"""简单的反向代理：将所有请求转发到 https://api.edgefn.net。

用法：
    pip install -r requirements.txt
    python app.py

适用于部署到魔搭 ModelScope 创空间（Studio）：监听 0.0.0.0，端口取 PORT
环境变量（默认 7860）。
"""
import os
from urllib.parse import urlsplit

import requests
from flask import Flask, Response, request, stream_with_context

UPSTREAM = os.environ.get("UPSTREAM_URL", "https://api.edgefn.net").rstrip("/")
PORT = int(os.environ.get("PORT", "7860"))
CONNECT_TIMEOUT = float(os.environ.get("PROXY_CONNECT_TIMEOUT", "10"))
READ_TIMEOUT = float(os.environ.get("PROXY_READ_TIMEOUT", "300"))
CORS_ENABLED = os.environ.get("CORS_ENABLED", "1") == "1"

# 上游认证注入：设置 UPSTREAM_TOKEN 后，转发前用它覆盖上游请求的认证头。
# 背景：调用方的魔搭 token 只用于魔搭网关鉴权，不能透传给上游，
# 而 Authorization 头只有一个，所以上游 token 必须由代理服务端注入。
UPSTREAM_TOKEN = os.environ.get("UPSTREAM_TOKEN", "")
UPSTREAM_AUTH_HEADER = os.environ.get("UPSTREAM_AUTH_HEADER", "Authorization")
UPSTREAM_AUTH_SCHEME = os.environ.get("UPSTREAM_AUTH_SCHEME", "Bearer")

METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# RFC 7230 §6.1：逐跳（hop-by-hop）头不得转发
HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}

app = Flask(__name__)
session = requests.Session()


def _cors_headers() -> dict:
    return {
        "Access-Control-Allow-Origin": request.headers.get("Origin", "*"),
        "Access-Control-Allow-Methods": ", ".join(METHODS),
        "Access-Control-Allow-Headers": request.headers.get(
            "Access-Control-Request-Headers", "*"
        ),
        "Access-Control-Max-Age": "86400",
    }


@app.route("/health", methods=["GET"])
def health():
    """本地健康检查（不转发），方便确认代理进程本身存活。"""
    return {"status": "ok", "upstream": UPSTREAM}, 200


@app.route("/", defaults={"path": ""}, methods=METHODS)
@app.route("/<path:path>", methods=METHODS)
def proxy(path: str):
    # 浏览器跨域预处理请求直接本地应答
    if request.method == "OPTIONS" and CORS_ENABLED:
        return Response(status=204, headers=_cors_headers())

    # 目标 URL：原样保留 path + query string
    parts = urlsplit(request.url)
    target = UPSTREAM + (parts.path or "/")
    if parts.query:
        target += "?" + parts.query

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP and key.lower() != "host"
    }
    headers["X-Forwarded-For"] = request.remote_addr or ""
    headers["X-Forwarded-Proto"] = request.scheme
    headers["X-Forwarded-Host"] = request.host

    # 服务端注入上游认证（若配置了 UPSTREAM_TOKEN）：覆盖调用方带来的同名认证头
    if UPSTREAM_TOKEN:
        headers = {
            key: value
            for key, value in headers.items()
            if key.lower() != UPSTREAM_AUTH_HEADER.lower()
        }
        credential = (
            f"{UPSTREAM_AUTH_SCHEME} {UPSTREAM_TOKEN}"
            if UPSTREAM_AUTH_SCHEME
            else UPSTREAM_TOKEN
        )
        headers[UPSTREAM_AUTH_HEADER] = credential

    try:
        upstream = session.request(
            request.method,
            target,
            headers=headers,
            data=request.get_data(),
            stream=True,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        return {"error": "bad_gateway", "detail": str(exc)}, 502

    def generate():
        try:
            # decode_content=False：字节原样透传（含 gzip 等编码）
            for chunk in upstream.raw.stream(65536, decode_content=False):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    # 分块输出：长度由网关重算；Server/Date 由网关自己生成，避免重复
    excluded = HOP_BY_HOP | {"content-length", "server", "date"}
    resp_headers = [
        (key, value)
        for key, value in upstream.headers.items()
        if key.lower() not in excluded
    ]
    if CORS_ENABLED:
        resp_headers.extend(_cors_headers().items())

    return Response(
        stream_with_context(generate()),
        status=upstream.status_code,
        headers=resp_headers,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
