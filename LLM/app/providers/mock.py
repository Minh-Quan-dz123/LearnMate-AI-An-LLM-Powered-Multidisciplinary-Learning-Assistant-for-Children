# ============================================================
# FILE: LLM/app/providers/mock.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MockProvider mô phỏng nội dung cho 3 tác vụ của BE:
#   1. Module 1: sinh trắc nghiệm một/nhiều đáp án.
#   2. Module 2: sinh câu hỏi mở.
#   3. Module 2: đánh giá câu trả lời mở.
#
# Chỉ hoạt động khi LLM Server chọn MockProvider.
# Không gọi nhà cung cấp AI, không chấm bài theo ý nghĩa thực tế.
# Không thay đổi contract của BaseProvider hoặc ProviderResult.
# ============================================================

import asyncio
import json
import re

from .base import BaseProvider, ProviderResult


class MockProvider(BaseProvider):
    name = "mock"

    @staticmethod
    def _get_prompt(messages: list[dict]) -> str:
        """
        Lấy nội dung prompt cuối cùng từ danh sách messages.

        Hỗ trợ:
            - Prompt dạng chuỗi thông thường.
            - Prompt dạng list chứa các phần tử text.

        Ví dụ:
            messages = [
                {"role": "user", "content": "Tạo 3 câu hỏi"}
            ]

            Kết quả: "Tạo 3 câu hỏi"
        """
        raw = messages[-1].get("content", "") if messages else ""

        if isinstance(raw, list):
            return " ".join(
                str(item.get("text", ""))
                for item in raw
                if isinstance(item, dict)
                and item.get("type") == "text"
            )

        return str(raw)

    @staticmethod
    def _question_count(prompt: str) -> int:
        """
        Trích xuất số câu hỏi mà BE yêu cầu trong prompt.

        Sử dụng Regular Expression để nhận diện:
            - "Tạo đúng 3 câu hỏi"
            - "Hãy tạo đúng 5 câu"
            - "Tạo 2 câu hỏi"

        Nếu không tìm thấy số câu, mặc định sinh 1 câu.

        Giới hạn theo MVP: 1 đến 5 câu.
        """
        match = re.search(
            r"(?:hãy\s+)?tạo\s+đúng\s+(\d+)\s+câu"
            r"|\b(\d+)\s+câu\s+hỏi",
            prompt,
            flags=re.IGNORECASE,
        )

        count = (
            int(match.group(1) or match.group(2))
            if match
            else 1
        )

        return max(1, min(5, count))

    @staticmethod
    def _quiz(prompt: str) -> dict:
        """
        Giả lập sinh câu hỏi trắc nghiệm cho Module 1.

        Hỗ trợ:
            - Trắc nghiệm một đáp án.
            - Trắc nghiệm nhiều đáp án.
            - Số lượng từ 1 đến 5 câu.

        Dữ liệu đầu ra tuân theo schema mà BE kiểm tra:
            question_id
            content
            options
            correct_option_ids
            explanation

        Lưu ý:
            Các câu hỏi có nội dung cố định vì đây là Mock.
        """
        count = MockProvider._question_count(prompt)

        # BE Module 1 đưa question_type vào JSON dữ liệu bài tập.
        # Dựa vào đó để xác định loại trắc nghiệm.
        multiple = bool(
            re.search(
                r'"question_type"\s*:\s*"Trắc nghiệm nhiều đáp án"',
                prompt,
                flags=re.IGNORECASE,
            )
        )

        questions = []

        for i in range(1, count + 1):

            if multiple:
                # Trắc nghiệm nhiều đáp án đúng.
                options = [
                    {"option_id": "A", "text": "Chim sẻ"},
                    {"option_id": "B", "text": "Con bò"},
                    {"option_id": "C", "text": "Bướm"},
                    {"option_id": "D", "text": "Cá vàng"},
                ]

                correct = ["A", "C"]

                content = "Những con vật nào có thể bay?"

                explanation = (
                    "Chim sẻ và bướm đều có thể bay."
                )

            else:
                # Trắc nghiệm một đáp án đúng.
                options = [
                    {"option_id": "A", "text": "Con mèo"},
                    {"option_id": "B", "text": "Con cá"},
                    {"option_id": "C", "text": "Con gà"},
                ]

                correct = ["B"]

                content = "Con vật nào sống dưới nước?"

                explanation = (
                    "Cá sống dưới nước và hô hấp bằng mang."
                )

            # Tạo ID riêng cho mỗi câu hỏi.
            questions.append({
                "question_id": f"cau-{i:02d}",
                "content": f"{content} (câu {i})",
                "options": options,
                "correct_option_ids": correct,
                "explanation": explanation,
            })

        return {"questions": questions}

    @staticmethod
    def _open_questions(prompt: str) -> dict:
        """
        Giả lập sinh câu hỏi mở cho Module 2.

        Mỗi câu hỏi gồm:
            question_id
            content
            answer_hint
            evaluation_criteria

        Ví dụ:
            BE yêu cầu 3 câu hỏi mở.
            Mock trả về danh sách 3 câu hỏi.

        Đây là dữ liệu giả, không sinh nội dung bằng AI.
        """
        count = MockProvider._question_count(prompt)

        return {
            "questions": [
                {
                    "question_id": f"cau-{i:02d}",
                    "content": (
                        "Khi thấy một người bạn bị ngã, "
                        f"con nên làm gì? (câu {i})"
                    ),
                    "answer_hint": (
                        "Con hãy viết một hoặc hai câu ngắn."
                    ),
                    "evaluation_criteria": [
                        "Biết quan tâm và giúp đỡ bạn",
                        "Biết nhờ người lớn khi cần",
                    ],
                }
                for i in range(1, count + 1)
            ]
        }

    @staticmethod
    def _evaluation() -> dict:
        """
        Giả lập kết quả đánh giá câu trả lời mở.

        Trả về dữ liệu theo schema của Module 2:
            score
            is_appropriate
            feedback
            strengths
            suggestions
            sample_answer

        Chú ý:
            Điểm số luôn cố định là 8.0.
            Mock không thực sự đọc hiểu hay chấm câu trả lời.
        """
        return {
            "score": 8.0,
            "is_appropriate": True,
            "feedback": (
                "Đây là nhận xét giả lập "
                "để kiểm tra chức năng hiển thị."
            ),
            "strengths": [
                "Đã nhập câu trả lời"
            ],
            "suggestions": [
                "Con có thể bổ sung thêm ý nhé."
            ],
            "sample_answer": (
                "Con sẽ hỏi thăm bạn "
                "và gọi cô giáo khi cần."
            ),
        }

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> ProviderResult:
        """
        Hàm chính được LLM Service gọi khi sử dụng MockProvider.

        Luồng thực hiện:

            1. Giả lập độ trễ mạng.
            2. Lấy prompt từ messages.
            3. Nhận diện tác vụ BE đang yêu cầu.
            4. Sinh dữ liệu giả tương ứng.
            5. Chuyển dữ liệu thành JSON string.
            6. Đóng gói thành ProviderResult.

        Thứ tự nhận diện quan trọng:
            - Chấm câu trả lời mở.
            - Sinh câu hỏi mở.
            - Sinh trắc nghiệm.

        Nguyên nhân:
            Prompt chấm câu trả lời mở cũng có thể
            chứa các từ "câu hỏi", "JSON".

            Vì vậy không được kiểm tra từ "JSON"
            trước khi nhận diện tác vụ.
        """

        # 1. Giả lập độ trễ khi gọi model.
        await asyncio.sleep(0.05)

        # 2. Lấy prompt.
        prompt = self._get_prompt(messages)

        lowered = prompt.lower()

        # 3. Nhận diện tác vụ của Backend.

        # Trường hợp 1: Chấm câu trả lời mở.
        if "<cau_tra_loi_cua_tre>" in lowered:
            output = self._evaluation()

        # Trường hợp 2: Sinh câu hỏi mở.
        elif (
            re.search(r"câu\s+hỏi\s+mở", lowered)
            or (
                "answer_hint" in lowered
                and "evaluation_criteria" in lowered
            )
        ):
            output = self._open_questions(prompt)

        # Trường hợp 3: Sinh câu hỏi trắc nghiệm.
        elif (
            "trắc nghiệm" in lowered
            or "câu hỏi" in lowered
            or "cau hoi" in lowered
            or "json" in lowered
        ):
            output = self._quiz(prompt)

        else:
            # Giữ hành vi dự phòng của phiên bản cũ.
            output = self._evaluation()

        # 4. Chuyển dict Python thành JSON string.
        # ensure_ascii=False giúp giữ nguyên tiếng Việt.
        content = json.dumps(
            output,
            ensure_ascii=False,
        )

        # 5. Trả ProviderResult theo contract hiện tại.
        return ProviderResult(
            content=content,
            model=model,
            usage={
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": len(content) // 4,
                "total_tokens": (
                    len(prompt) + len(content)
                ) // 4,
            },
            finish_reason="stop",
        )