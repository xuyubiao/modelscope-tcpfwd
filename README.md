# modelscope-tcpfwd

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

经官方文档核实，普通 Python Web 服务应选择 **Docker** 类型的创空间：

1. 在 [modelscope.cn/studios](https://modelscope.cn/studios) 点击「创建创空间」，
   SDK 类型选 **Docker**（前置要求：绑定阿里云账号并完成实名认证）；
2. 代码提交：创空间**不支持直接关联 GitHub 仓库**，需把代码推送到创空间自带的
   魔搭 Git 仓库（地址形如 `https://www.modelscope.cn/{用户名}/{仓库名}.git`，
   用魔搭 access token 做密码），或在网页端拖拽上传；
3. 仓库需包含 `Dockerfile` + `app.py` + `requirements.txt`（本仓库已备好）；
4. 容器内应用**必须监听 7860 端口且绑定 0.0.0.0**（单应用只能暴露这一个端口），
   本应用默认即 `0.0.0.0:7860`；
5. 上线后每个创空间有独立公网访问链接，请求将被转发到 `https://api.edgefn.net`。

官方文档：
- [创空间创建与搭建](https://modelscope.cn/docs/studios/create)
- [Docker 创空间](https://modelscope.cn/docs/studios/docker)
- [快速创建并部署](https://modelscope.cn/docs/studios/quick-create)
