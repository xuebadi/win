"""
StudyTutorAI - Gradio 6.x Compatible UI
Model loaded lazily only when user sends a message.
"""
import gradio as gr
from pathlib import Path
import json


# ==================== Config ====================
MODEL_DIR = Path("models")
CONFIG_FILE = Path("config/settings.json")
PROFILE_FILE = Path("study_profile.json")

# State: None = not loaded, False = load failed, object = loaded
_chat_engine = None
_load_error = None


def _try_load_model():
    """Try loading model. Returns (success, error_msg)"""
    global _chat_engine, _load_error
    
    if _chat_engine is not None:
        return True, None
    
    if _load_error is not None:
        return False, _load_error

    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from app.backend import ModelManager, ChatEngine

        mm = ModelManager(str(MODEL_DIR))
        status = mm.get_status()

        if not status.get("model_exists"):
            # Try HuggingFace cache
            _load_error = ("Model not found in models/ folder.\n\n"
                "Options:\n"
                "1. Download Qwen3.5-2B-GGUF to models/ folder\n"
                "2. Or run with HuggingFace cache: set TRANSFORMERS_OFFLINE=0\n\n"
                "Note: Loading the model requires ~3GB RAM.")
            return False, _load_error

        _chat_engine = ChatEngine(mm)
        return True, None
    except ImportError as e:
        _load_error = f"Missing dependency: {e}. Install with: pip install torch transformers"
        return False, _load_error
    except Exception as e:
        _load_error = str(e)
        return False, _load_error


def _get_profile() -> dict:
    """Load study profile"""
    if PROFILE_FILE.exists():
        try:
            return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {"total_sessions": 0, "questions_asked": 0, "topics": []}


def _save_profile(profile: dict):
    """Save study profile"""
    PROFILE_FILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


# ==================== Chat Functions ====================

def chat_fn(message, history, mode, temperature):
    """Main chat function"""
    if not message.strip():
        return history, ""

    # Try loading model
    ok, err = _try_load_model()

    if ok and _chat_engine is not None:
        try:
            reply = _chat_engine.chat(message, temperature=temperature)
            history = history + [{"role": "user", "content": message}]
            history = history + [{"role": "assistant", "content": reply}]

            # Update profile
            profile = _get_profile()
            profile["questions_asked"] = profile.get("questions_asked", 0) + 1
            _save_profile(profile)

            return history, ""
        except Exception as e:
            history = history + [{"role": "user", "content": message}]
            history = history + [{"role": "assistant", "content": f"[Error] {e}"}]
            return history, ""
    else:
        # No model available - show helpful message
        tip = _get_tutor_tip(message, mode)
        history = history + [{"role": "user", "content": message}]
        history = history + [{"role": "assistant", "content": f"[Model not loaded] {err}\n\n---\n\n{tip}"}]
        return history, ""


def _get_tutor_tip(question: str, mode: str) -> str:
    """Generate a helpful tip when model is unavailable"""
    tips = {
        "Auto": f"Good question about '{question[:30]}...'! Once the model is loaded, I'll guide you through it step by step.",
        "Concept": f"Let me think about how to explain this concept. Download the model to get personalized explanations!",
        "Practice": f"Great topic for practice! With the model loaded, I can generate exercises for you.",
        "Hint": f"Here's a hint: try breaking down '{question[:20]}...' into smaller parts. Load the model for more guidance!",
        "Review": f"Let's review this together! The model will help summarize key points once loaded.",
        "Error Analysis": f"Common mistakes on this topic include... Load the model for detailed error analysis!",
    }
    return tips.get(mode, tips["Auto"])


def upload_pdfs(files):
    """Upload PDF files to knowledge base"""
    if not files:
        return "No files selected"

    saved = []
    kb_dir = Path("knowledge_base")
    kb_dir.mkdir(exist_ok=True)

    for f in files:
        try:
            name = Path(f.name).name
            if name.lower().endswith(".pdf"):
                import shutil
                dest = kb_dir / name
                shutil.copy2(f.name, dest)
                saved.append(name)
        except Exception as e:
            saved.append(f"[Error: {name}]")

    if saved:
        return f"Uploaded: {', '.join(saved)}"
    return "No PDF files found"


def get_stats():
    """Get study statistics"""
    profile = _get_profile()
    return (
        f"**Questions asked**: {profile.get('questions_asked', 0)}\n\n"
        f"**Sessions**: {profile.get('total_sessions', 0)}\n\n"
        f"**Topics**: {len(profile.get('topics', []))}"
    )


# ==================== Build UI ====================

def build_app():
    """Build Gradio app"""

    with gr.Blocks(title="StudyTutorAI") as demo:
        gr.Markdown("""# StudyTutorAI
Your personal AI tutor - Local, Private, Offline-ready

> Model loads on first message (saves memory). Download Qwen3.5-2B to `models/` folder to enable AI tutoring.
""")

        with gr.Tabs():
            # Tab 1: Chat
            with gr.TabItem("Chat"):
                chatbot = gr.Chatbot(height=400)

                with gr.Row():
                    mode = gr.Dropdown(
                        choices=["Auto", "Concept", "Practice", "Hint", "Review", "Error Analysis"],
                        value="Auto",
                        label="Mode",
                        scale=2,
                    )
                    temp = gr.Slider(
                        minimum=0.1, maximum=1.5, value=0.7, step=0.1,
                        label="Temperature",
                        scale=1,
                    )

                msg = gr.Textbox(
                    placeholder="Type your question here...",
                    label="Question",
                    lines=2,
                )

                with gr.Row():
                    send_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear")

            # Tab 2: Knowledge Base
            with gr.TabItem("Knowledge Base"):
                gr.Markdown("### Upload PDF files to build your knowledge base")
                pdf_upload = gr.File(
                    file_count="multiple",
                    file_types=[".pdf"],
                    label="PDF Files",
                )
                upload_btn = gr.Button("Upload")
                upload_result = gr.Textbox(label="Result", interactive=False)

            # Tab 3: Stats
            with gr.TabItem("Stats"):
                stats_display = gr.Markdown(value=get_stats())
                refresh_btn = gr.Button("Refresh")

        # Event handlers
        send_btn.click(
            chat_fn,
            [msg, chatbot, mode, temp],
            [chatbot, msg],
        )
        msg.submit(
            chat_fn,
            [msg, chatbot, mode, temp],
            [chatbot, msg],
        )
        clear_btn.click(
            lambda: ([], ""),
            outputs=[chatbot, msg],
        )
        upload_btn.click(
            upload_pdfs,
            [pdf_upload],
            [upload_result],
        )
        refresh_btn.click(
            get_stats,
            outputs=[stats_display],
        )

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860)