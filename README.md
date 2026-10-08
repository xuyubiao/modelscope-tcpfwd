# edgefn-proxy

一个简单的 Python 反向代理：把收到的所有请求原样转发到 `https://api.edgefn.net`，
并把上游的响应（含状态码、响应头、流式 body）透传回客户端。适合部署到
魔搭 ModelScope 创空间（Studio）对外提供 API 入口。

## 文件

- `app.py` — 代理主程序（Flask + requests，流式转发，支持 SSE）
- `requirements.txt` — 依赖

## 本地运行

```bash
pip install -r requirements.txt
python app.py
# 监听 0.0.0.0:7860，例如：curl http://127.0.0.1:7860/<你的API路径>
```

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `UPSTREAM_URL` | `https://api.edgefn.net` | 上游地址 |
| `PORT` | `7860` | 监听端口 |
| `PROXY_CONNECT_TIMEOUT` | `10` | 上游连接超时（秒） |
| `PROXY_READ_TIMEOUT` | `300` | 上游读取超时（秒） |
| `CORS_ENABLED` | `1` | 是否自动加 CORS 头（`0` 关闭） |

`GET /health` 为本地健康检查接口（不转发），返回代理进程状态。

## 部署到 ModelScope 创空间

1. 在 [modelscope.cn/studios](https://modelscope.cn/studios) 创建创空间，关联本仓库；
2. 入口文件选择 `app.py`（或按页面提示配置启动命令 `python app.py`）；
3. 确认应用监听端口为 `7860`（`PORT` 环境变量）；
4. 启动后，通过创空间分配的公网域名访问，请求会被转发到 `https://api.edgefn.net`。
