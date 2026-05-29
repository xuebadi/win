"""
StudyTutorAI - Minimal Test UI
"""
import gradio as gr


def chat_reply(message: str, history: list) -> tuple:
    """Simple echo reply"""
    if not message.strip():
        return history, ""

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": f"You said: {message}"})
    return history, ""


def build_app():
    """Build minimal Gradio app"""
    with gr.Blocks(title="StudyTutorAI") as demo:
        gr.Markdown("# StudyTutorAI (Test Mode)")

        chatbot = gr.Chatbot(label="AI Tutor", height=400)
        msg_input = gr.Textbox(placeholder="Type something...", label="Input", lines=2)
        send_btn = gr.Button("Send", variant="primary")
        clear_btn = gr.Button("Clear")

        send_btn.click(chat_reply, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input])
        msg_input.submit(chat_reply, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input])
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg_input])

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860)