"""
Chat Engine - Uses ModelManager for generation
Heavy imports are fully handled by ModelManager.load()
"""


class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class ChatEngine:
    SYSTEM_PROMPT = """你是一个耐心、专业的中文AI学习导师。
你的教学风格是苏格拉底式引导——不直接给答案，而是通过提问引导学生思考。
使用简体中文回答。态度鼓励。每次回复后，提出一个引导性问题帮助学生深入理解。
回复简练，不超过200字。"""

    def __init__(self, model_manager, system_prompt: str = None):
        self.mm = model_manager
        self.history: list = []
        self.system_prompt = system_prompt or self.SYSTEM_PROMPT

    def reset(self):
        self.history = []

    def chat(self, user_input: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
        """Generate a reply"""
        self.history.append(ChatMessage("user", user_input))

        # Build prompt
        prompt_parts = [f"System: {self.system_prompt}"]
        for m in self.history:
            if m.role == "user":
                prompt_parts.append(f"用户: {m.content}")
            elif m.role == "assistant":
                prompt_parts.append(f"导师: {m.content}")
        prompt_parts.append("导师: ")
        prompt = "\n".join(prompt_parts)

        reply = self.mm.generate(prompt, max_new_tokens=256)

        self.history.append(ChatMessage("assistant", reply))
        return reply

    def get_history_text(self) -> str:
        lines = []
        for m in self.history:
            label = "用户" if m.role == "user" else "导师"
            lines.append(f"**{label}**: {m.content}")
        return "\n\n".join(lines)
