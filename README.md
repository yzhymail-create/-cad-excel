# 本地离线语义文件管理 Agent

该目录提供一个本地 CLI，用于离线语义检索指定目录内的文件内容。

## 安装依赖

```bash
pip install -r requirements.txt
```

> 说明：OCR 图片识别依赖本机安装的 `tesseract` 可执行程序（用户级安装即可）。

## 准备离线模型

推荐提前下载本地模型（如 `all-MiniLM-L6-v2`），并放在以下路径之一：

- `models/all-MiniLM-L6-v2`
- 或在命令中通过 `--model /path/to/model` 指定

系统默认启用离线模式（不会访问外网），如果模型不存在会提示手动下载。
如需完全免模型运行，可使用轻量模式：

```bash
python -m local_semantic_file_agent index --root /path --model hashing
```

## CLI 使用示例

索引指定目录：

```bash
python -m local_semantic_file_agent index --root /path/to/docs --root /path/to/more
```

语义搜索：

```bash
python -m local_semantic_file_agent search --query "工艺规范" --top-k 5
```

默认数据库路径：`~/.local_semantic_agent/index.sqlite`（可通过 `--db` 覆盖）。

## 支持的文件类型

- PDF
- Word（.docx）
- Excel（.xlsx）
- 文本（.txt / .md）
- PPTX（.ppt 需先转换）
- 图片（.png / .jpg 等，需 OCR）

## 运行约束

- 仅使用本地文件
- 不启动服务端口
- 不依赖管理员权限
- 支持增量更新（按文件时间戳与大小判断）
