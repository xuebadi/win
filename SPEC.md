# 学霸帝AI - 项目规划与架构文档

## 产品定位

- **产品名**: 学霸帝AI - 你的专属AI导师，让学习真正「活」起来
- **英文名**: StudyTutorAI
- **定位**: 本地部署的个性化AI学习导师，参考 DeepTutor 架构理念
- **核心价值**: 完全本地运行，保护隐私，无网络依赖

## 核心模型

### 主模型 (LLM)
- **模型**: Qwen3.5-2B-GGUF (Q4_K_M 量化版)
- **来源**: https://modelscope.cn/models/unsloth/Qwen3.5-2B-GGUF
- **文件**: Qwen3.5-2B-Q4_K_M.gguf
- **内存需求**: ~1.5GB（Q4量化，CPU可跑）

### 多模态视觉投影器
- **文件**: mmproj-BF16.gguf
- **来源**: 同上 ModelScope 地址
- **用途**: 视觉问答（拍照搜题、图表理解）

## 技术架构

```
study_tutor_ai/
├── app/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── model_loader.py      # 模型加载管理
│   │   ├── chat_engine.py       # 对话引擎
│   │   ├── rag_engine.py        # RAG知识库引擎
│   │   └── tutor_agent.py       # Tutor Agent (参考DeepTutor)
│   └── frontend/
│       ├── __init__.py
│       └── app.py               # Gradio 主界面
├── models/                      # 模型文件目录(手动下载)
│   └── README.md
├── config/
│   └── settings.json            # 配置(模型路径、主题等)
├── requirements.txt
├── run.py                       # 启动入口
└── build_exe.py                 # PyInstaller打包脚本
```

## 功能模块

### 1. 对话问答 (DeepTutor Auto Mode)
- 课程内容讲解、答疑
- 追问式引导（苏格拉底式提问）
- 多轮对话上下文管理

### 2. 拍照搜题 (多模态)
- 支持上传题目图片
- 视觉投影器识别题目内容
- 逐步解答与知识点关联

### 3. 知识库 (DeepTutor RAG)
- 本地知识库管理（教材PDF/TXT）
- 知识点检索与关联
- 个性化学习路径推荐

### 4. 记忆系统 (DeepTutor Three-layer Memory)
- L1: 即时会话上下文
- L2: 用户学习档案
- L3: 长期知识图谱

## 部署模式

### 开发模式 (run.py)
```bash
pip install -r requirements.txt
python run.py
# 启动 Gradio 服务 -> http://localhost:7860
```

### 生产EXE模式 (build_exe.py)
```bash
python build_exe.py
# 打包为 StudyTutorAI.exe
# 用户双击exe -> 自动解压临时目录 -> 启动本地服务
```

## 模型下载说明

模型文件较大，需手动下载：
1. 访问 https://modelscope.cn/models/unsloth/Qwen3.5-2B-GGUF
2. 下载 `Qwen3.5-2B-Q4_K_M.gguf` → 放入 `models/` 目录
3. 下载 `mmproj-BF16.gguf` → 放入 `models/` 目录

## 技术栈

- **LLM推理**: llama-cpp-python (CUDA加速 if GPU available)
- **多模态**: qwen-vl-utils + 自定义视觉投影器
- **前端**: Gradio (快速原型) / CustomTkinter (exe打包)
- **RAG**: 本地向量库（FAISS / ChromaDB）
- **Agent**: 自主Agent架构（参考DeepTutor）
- **打包**: PyInstaller + Nuitka 双保险