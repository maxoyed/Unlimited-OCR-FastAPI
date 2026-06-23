# Unlimited-OCR-FastAPI

[English](README.md) | **简体中文**

一个轻量级的 **FastAPI** 服务，使用百度
[Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR) 模型把
**图片和 PDF 转换为文字**。

本服务**不**负责部署 OCR 模型本身。你需要自己用
**[sglang](https://github.com/sgl-project/sglang)**（它提供 OpenAI 兼容 API）
来部署模型，本服务只负责调用它。sglang 的地址、API Key 和模型名完全通过
**环境变量**传入。

请求格式严格遵循 Unlimited-OCR 官方的 sglang 示例 —— 包括
`skip_special_tokens=false`、`images_config.image_mode`，以及 DeepSeek-OCR 的
no-repeat-ngram `custom_logit_processor` / `custom_params`。

## 各场景固定的提示词

提示词与采样参数均为**写死的**（不可由用户自定义），与官方用法保持一致：

| 场景      | 提示词                | `image_mode`        | `ngram_size` | `window_size` |
| --------- | --------------------- | ------------------- | ------------ | ------------- |
| 单张图片  | `document parsing.`   | `gundam`（或 `base`）| 35           | 128           |
| 多张图片  | `Multi page parsing.` | `base`              | 35           | 1024          |
| PDF       | `Multi page parsing.` | `base`              | 35           | 1024          |

单张图片支持 `gundam`（默认）或 `base` 两种模式；多张图片和 PDF 始终使用
`base`。

### 关于 `custom_logit_processor`

官方客户端发送的是 `DeepseekOCRNoRepeatNGramLogitProcessor.to_str()`。由于该类在
sglang 服务端是可导入的，`to_str()` 会**按引用**序列化它 —— 序列化结果只编码了类的
导入路径，由服务端在加载时解析为真实实现。我们把这串序列化字符串直接内嵌在
[`app/logit_processor.py`](app/logit_processor.py) 中，因此本服务**无需依赖
sglang/torch**。如需重新生成，运行
[`scripts/gen_logit_processor.py`](scripts/gen_logit_processor.py)。

## 接口

| 方法   | 路径         | 说明                                          |
| ------ | ------------ | --------------------------------------------- |
| GET    | `/health`    | 存活检查 + 当前模型 / sglang 地址。            |
| POST   | `/ocr`       | 多张图片合并为一个文档；每个 PDF 各为一个文档。|
| POST   | `/ocr/image` | 单张图片 → 单页解析；多张 → 一个多页文档。     |
| POST   | `/ocr/pdf`   | 每个 PDF → 一个多页文档。                      |

Multipart 表单字段：

- `files`：一个或多个文件（多文件时重复该字段）。
- `image_mode` *（可选，仅对单张图片生效）*：`gundam`（默认）或 `base`。

交互式文档地址：`/docs`。

### 响应结构

```json
{
  "model": "Unlimited-OCR",
  "results": [
    {
      "name": "invoice.pdf",
      "scenario": "pdf",
      "image_mode": "base",
      "page_count": 2,
      "text": "…识别出的文字…",
      "error": null
    }
  ]
}
```

## 配置

所有配置均来自环境变量（参见 [`.env.example`](.env.example)）：

| 变量                   | 默认值                      | 说明                                                  |
| ---------------------- | --------------------------- | ----------------------------------------------------- |
| `SGLANG_BASE_URL`      | `http://localhost:30000`    | sglang 服务根地址（会自动追加 `/v1/chat/completions`）。|
| `SGLANG_API_KEY`       | *（空）*                    | Bearer Token；无鉴权时留空或填 `EMPTY`。              |
| `OCR_MODEL`            | `Unlimited-OCR`             | sglang 中注册的模型名。                               |
| `OCR_MAX_CONCURRENCY`  | `4`                         | 对 sglang 的最大并发 OCR 调用数。                     |
| `OCR_REQUEST_TIMEOUT`  | `1200`                      | 单次请求超时时间（秒）。                              |
| `PDF_DPI`              | `300`                       | PDF 页面栅格化的 DPI。                                |
| `MAX_FILE_SIZE_MB`     | `50`                        | 单文件大小上限（0 表示不限制）。                     |
| `MAX_FILES`            | `20`                        | 单次请求最大文件数（0 表示不限制）。                 |

## 快速开始（Docker Compose）

1. 先用 sglang 在某个可访问的地址部署模型，例如：

   ```bash
   python -m sglang.launch_server \
     --model-path baidu/Unlimited-OCR \
     --served-model-name Unlimited-OCR \
     --host 0.0.0.0 --port 30000
   ```

2. 让本服务指向它并启动：

   ```bash
   cp .env.example .env       # 修改 SGLANG_BASE_URL / SGLANG_API_KEY / OCR_MODEL
   docker compose up --build
   ```

   默认情况下它会指向 `http://host.docker.internal:30000`，以访问宿主机上运行的
   sglang 服务。

3. 服务现在运行在 `http://localhost:8000`（文档地址 `/docs`）。

## 快速开始（本地，不用 Docker）

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SGLANG_BASE_URL=http://localhost:30000
export OCR_MODEL=Unlimited-OCR
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 使用示例

单张图片（gundam）：

```bash
curl -X POST http://localhost:8000/ocr/image -F "files=@page.jpg"
```

单张图片，base 模式：

```bash
curl -X POST http://localhost:8000/ocr/image \
  -F "files=@page.jpg" -F "image_mode=base"
```

多张图片（一个多页文档）：

```bash
curl -X POST http://localhost:8000/ocr/image \
  -F "files=@page1.png" -F "files=@page2.png"
```

PDF（一个或多个）：

```bash
curl -X POST http://localhost:8000/ocr/pdf -F "files=@document.pdf"
```

## 说明

- 本服务**不进行任何模型部署**；它只负责处理上传、PDF 栅格化，并使用官方
  Unlimited-OCR 请求格式调用你的 sglang 接口。
- 请求在内部以流式方式从 sglang 读取，并聚合为接口最终返回的文字。
