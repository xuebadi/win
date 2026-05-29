# 学霸帝AI (StudyTutorAI)

本地运行的中文AI学习导师，基于 Qwen2.5-0.5B-Instruct 模型，苏格拉底式引导教学。

## 特性

- 🎓 **苏格拉底式引导** — 不直接给答案，通过提问引导思考
- 🔒 **完全本地运行** — 隐私安全，无需联网
- 💡 **轻量设计** — 6GB RAM 即可运行
- 🌐 **Web 界面** — 浏览器访问，支持对话学习/知识库/学习档案

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载模型

```bash
python download_models.py
```

或手动下载 [Qwen2.5-0.5B-Instruct](https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct) 到 `models/` 目录。

### 3. 启动

```bash
python run.py
```

浏览器自动打开 http://localhost:7860

## 打包为 EXE

```bash
pip install pyinstaller
python build_exe.py
```

## 项目结构

```
├── run.py              # 主入口（轻量HTTP服务器+前端）
├── app/
│   ├── backend/
│   │   ├── model_loader.py  # 模型加载与推理
│   │   ├── chat_engine.py   # 对话引擎（苏格拉底式）
│   │   ├── rag_engine.py    # RAG知识库
│   │   └── tutor_agent.py   # DeepTutor风格Agent
│   └── frontend/
│       └── app.py           # UI界面
├── config/settings.json
├── models/                  # 模型文件（需下载）
└── knowledge_base/          # PDF知识库
```

## 系统要求

- Python 3.10+
- 6GB+ RAM（0.5B模型约占用1GB内存）
- Windows / macOS / Linux

## License

MIT
