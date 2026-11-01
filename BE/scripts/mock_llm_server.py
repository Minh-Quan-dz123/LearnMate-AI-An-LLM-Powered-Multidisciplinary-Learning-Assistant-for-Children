
"""
LLM Server giả lập để test tích hợp.
Chỉ trả dữ liệu mẫu, không gọi model thật.
"""

import json
import re

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="LearnMate Mock LLM")


class LLMRequest(BaseModel):
    task: str
    model: str = "default"
    prompt: str
    temperature: float = 0.5
    max_output_tokens: int = 1800


def count_from_prompt(prompt: str, expression: str) -> int:
    found = re.search(
        expression,
        prompt,
        flags=re.IGNORECASE
    )

    count = int(found.group(1)) if found else 2
    return min(5, max(1, count))


@app.get("/health")
def health():
    return {
        "success": True,
        "message": "Mock LLM đang chạy",
    }


@app.post("/internal/llm/generate")
def generate(request: LLMRequest):

    task = request.task
    prompt = request.prompt

    # TASK 1: Sinh trắc nghiệm
    if task == "Sinh câu hỏi trắc nghiệm":

        count = count_from_prompt(
            prompt,
            r"Tạo\s+ĐÚNG\s+(\d+)\s+câu",
        )

        is_multiple = "Trắc nghiệm nhiều đáp án" in prompt
        questions = []

        for i in range(1, count + 1):

            if is_multiple:
                options = [
                    {"option_id": "A", "text": "Con chim"},
                    {"option_id": "B", "text": "Con cá"},
                    {"option_id": "C", "text": "Con bướm"},
                    {"option_id": "D", "text": "Con mèo"},
                ]
                correct = ["A", "C"]
                content = "Những con vật nào có thể bay?"
                explanation = "Chim và bướm có thể bay."
            else:
                options = [
                    {"option_id": "A", "text": "Con cá"},
                    {"option_id": "B", "text": "Con mèo"},
                    {"option_id": "C", "text": "Con chó"},
                ]
                correct = ["A"]
                content = "Con vật nào thường sống dưới nước?"
                explanation = "Cá thường sống dưới nước."

            questions.append({
                "question_id": f"q{i}",
                "content": f"{content} (câu {i})",
                "options": options,
                "correct_option_ids": correct,
                "explanation": explanation,
            })

        result = {"questions": questions}

    # TASK 2: Sinh câu hỏi mở
    elif task == "module2_generate_questions":

        count = count_from_prompt(
            prompt,
            r"Hãy\s+tạo\s+đúng\s+(\d+)\s+câu",
        )

        result = {
            "questions": [
                {
                    "question_id": f"q{i}",
                    "content": (
                        "Khi thấy bạn bị ngã, "
                        f"con nên làm gì? (câu {i})"
                    ),
                    "answer_hint": "Viết một hoặc hai câu ngắn.",
                    "evaluation_criteria": [
                        "Biết giúp đỡ bạn",
                        "Biết nhờ người lớn khi cần",
                    ],
                }
                for i in range(1, count + 1)
            ]
        }

    # TASK 3: Chấm câu trả lời mở
    elif task == "module2_evaluate_answer":

        result = {
            "score": 8.0,
            "is_appropriate": True,
            "feedback": (
                "Con đã cố gắng trả lời. "
                "Đây là nhận xét giả lập để thử hệ thống."
            ),
            "strengths": [
                "Con đã trả lời câu hỏi"
            ],
            "suggestions": [
                "Con có thể bổ sung chi tiết hơn nhé."
            ],
            "sample_answer": (
                "Con hỏi thăm bạn và nhờ cô giáo "
                "hỗ trợ khi cần."
            ),
        }

    else:
        return {
            "success": False,
            "message": f"Task chưa hỗ trợ: {task}",
            "data": {},
        }

    # Contract mà app/llm_client.py đang sử dụng.
    # data.content PHẢI là chuỗi JSON.
    return {
        "success": True,
        "message": "Mock LLM đã tạo nội dung mẫu",
        "data": {
            "content": json.dumps(
                result,
                ensure_ascii=False,
            )
        },
    }
