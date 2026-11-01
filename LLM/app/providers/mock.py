# ============================================================
# FILE: app/providers/mock.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Provider giả lập, KHÔNG gọi model thật.
# Dùng để:
# - BE (Người 2, Người 3) phát triển và test contract khi chưa có API key.
# - Test tự động của LLM Server không tốn chi phí.
#
# LUÔN có thể bật bằng MOCK_MODE=true trong .env.
# ============================================================

import asyncio
import json

from .base import BaseProvider, ProviderResult


class MockProvider(BaseProvider):
    name = "mock"

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> ProviderResult:
        # Mô phỏng độ trễ network nhỏ.
        await asyncio.sleep(0.05)

        # Xử lý content dạng list (vision: [{type:text},{type:image_url}]).
        raw = messages[-1]["content"] if messages else ""
        if isinstance(raw, list):
            parts = []
            for item in raw:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            last_message = " ".join(parts)
        else:
            last_message = str(raw)

        lowered = last_message.lower()

        # Nếu prompt nhắc tới JSON câu hỏi -> trả JSON mẫu hợp lệ
        # để EGM của BE có thể parse/validate.
        if "json" in lowered or "cau hoi" in lowered or "câu hỏi" in lowered:
            content = json.dumps(
                {
                    "questions": [
                        {
                            "question_id": "cau-01",
                            "content": "Con vật nào dưới đây sống dưới nước?",
                            "options": [
                                {"option_id": "A", "text": "Con mèo"},
                                {"option_id": "B", "text": "Con cá"},
                                {"option_id": "C", "text": "Con gà"},
                            ],
                            "correct_option_ids": ["B"],
                            "explanation": "Cá sống dưới nước và dùng mang để hô hấp.",
                        }
                    ]
                },
                ensure_ascii=False,
            )
        else:
            content = json.dumps(
                {
                    "score": 10,
                    "is_appropriate": True,
                    "feedback": "Con đã trả lời rất tốt và đúng ý! Rất đáng khen.",
                    "strengths": ["Trả lời đúng trọng tâm câu hỏi"],
                    "suggestions": ["Con có thể kể thêm một ví dụ nữa nhé."],
                    "sample_answer": "Đây là câu trả lời mẫu của người lớn.",
                },
                ensure_ascii=False,
            )

        return ProviderResult(
            content=content,
            # Trả về đúng model đã ánh xạ để không phá vỡ contract
            # (data.model phải là ID model thật, không kèm tiền tố mock).
            model=model,
            usage={
                "prompt_tokens": len(last_message) // 4,
                "completion_tokens": len(content) // 4,
                "total_tokens": (len(last_message) + len(content)) // 4,
            },
            finish_reason="stop",
        )
