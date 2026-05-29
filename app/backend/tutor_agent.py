"""
Tutor Agent - 参考 DeepTutor 的个性化导师逻辑
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class StudyProfile:
    """学习者档案 (L2 Memory)"""
    user_id: str = "default"
    name: str = ""
    interests: List[str] = field(default_factory=list)
    weak_topics: List[str] = field(default_factory=list)
    strong_topics: List[str] = field(default_factory=list)
    chat_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class MemoryEntry:
    """记忆条目 (L1/L2)"""
    timestamp: str
    topic: str
    content: str
    level: int  # 1=L1会话 2=L2档案 3=L3知识图谱


class TutorAgent:
    """
    DeepTutor 风格的导师Agent
    核心特点:
    - 苏格拉底式引导 (Socratic tutoring)
    - 三层记忆系统 (L1/L2/L3)
    - Auto Mode 自动判断学习模式
    """

    TUTOR_MODES = {
        "explain": "概念讲解 - 深入浅出解释知识点",
        "quiz": "练习题 - 出题检验理解",
        "hint": "提示引导 - 通过提问让学生自己找到答案",
        "summary": "总结复习 - 梳理知识点脉络",
        "debug": "错题分析 - 找出思维误区",
    }

    def __init__(self, chat_engine, rag_engine=None):
        self.chat = chat_engine
        self.rag = rag_engine
        self.profile = StudyProfile()
        self.l1_memory: List[MemoryEntry] = []  # 会话上下文
        self.l3_knowledge: Dict[str, List[str]] = {}  # 知识图谱

        self._profile_path = "user_profile.json"

    def set_profile(self, name: str = None, interests: List[str] = None):
        """设置学习者档案"""
        if name:
            self.profile.name = name
        if interests:
            self.profile.interests = interests
        self.profile.updated_at = datetime.now().isoformat()

    def _save_profile(self):
        """持久化档案"""
        data = {
            "user_id": self.profile.user_id,
            "name": self.profile.name,
            "interests": self.profile.interests,
            "weak_topics": self.profile.weak_topics,
            "strong_topics": self.profile.strong_topics,
            "chat_count": self.profile.chat_count,
            "created_at": self.profile.created_at,
            "updated_at": self.profile.updated_at,
        }
        with open(self._profile_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_profile(self):
        """加载档案"""
        if os.path.exists(self._profile_path):
            try:
                with open(self._profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.profile = StudyProfile(**data)
            except Exception:
                pass

    def _add_l1_memory(self, topic: str, content: str):
        """添加会话记忆"""
        self.l1_memory.append(MemoryEntry(
            timestamp=datetime.now().isoformat(),
            topic=topic,
            content=content,
            level=1,
        ))
        # L1 限制保留最近20条
        if len(self.l1_memory) > 20:
            self.l1_memory = self.l1_memory[-20:]

    def auto_mode(self, query: str) -> str:
        """Auto Mode - 根据输入自动判断学习模式"""
        query_lower = query.lower()

        # 关键词判断模式
        if any(k in query_lower for k in ["是什么", "什么是", "讲解", "解释", "概念"]):
            mode = "explain"
        elif any(k in query_lower for k in ["做题", "练习", "测试", "出题", "考考"]):
            mode = "quiz"
        elif any(k in query_lower for k in ["不会", "不懂", "错", "哪里错了"]):
            mode = "debug"
        elif any(k in query_lower for k in ["总结", "复习", "回顾"]):
            mode = "summary"
        else:
            mode = "hint"

        return mode

    def tutor_reply(self, user_input: str, mode: str = None,
                    temperature: float = 0.7) -> str:
        """导师回复"""
        # 自动判断模式
        if not mode:
            mode = self.auto_mode(user_input)

        # 更新档案
        self.profile.chat_count += 1
        self.profile.updated_at = datetime.now().isoformat()

        # 尝试RAG增强
        context = ""
        if self.rag:
            context, docs = self.rag.query_with_context(user_input)
            if context:
                context = f"\n\n【相关知识点】\n{context}\n"

        # 构建prompt
        mode_instruction = {
            "explain": "请用通俗易懂的方式讲解这个概念，如果涉及到相关知识点也一并说明。",
            "quiz": "请出一道与这个知识点相关的选择题或简答题，用于检验学习效果。",
            "hint": "请用苏格拉底式提问引导学生思考，不要直接给答案，通过提问一步步引导。",
            "summary": "请帮助学生梳理这一知识点的脉络和关键点，便于复习巩固。",
            "debug": "请分析学生在理解这个知识点时可能出现的常见错误和思维误区。",
        }

        system_msg = self.chat.system_prompt
        if mode in mode_instruction:
            system_msg = f"{system_msg}\n\n【当前模式】{mode_instruction[mode]}"

        if context:
            system_msg = f"{system_msg}\n{context}"

        old_system = self.chat.system_prompt
        self.chat.system_prompt = system_msg

        try:
            reply = self.chat.chat(user_input, temperature=temperature)
        finally:
            self.chat.system_prompt = old_system

        # 记录L1记忆
        self._add_l1_memory(
            topic=f"mode:{mode}",
            content=f"Q: {user_input}\nA: {reply}"
        )

        return reply

    def get_profile(self) -> dict:
        """获取学习档案"""
        return {
            "name": self.profile.name,
            "interests": self.profile.interests,
            "weak_topics": self.profile.weak_topics,
            "strong_topics": self.profile.strong_topics,
            "total_chats": self.profile.chat_count,
            "l1_memory_count": len(self.l1_memory),
        }

    def get_memory_summary(self) -> str:
        """获取记忆摘要"""
        lines = ["【会话记忆】最近对话摘要:"]
        for entry in self.l1_memory[-5:]:
            lines.append(f"- [{entry.topic}] {entry.content[:80]}...")
        return "\n".join(lines)