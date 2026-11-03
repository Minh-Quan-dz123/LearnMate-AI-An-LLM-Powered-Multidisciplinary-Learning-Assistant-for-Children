# Script này sẽ:
# 1. Đọc GEMINI_API_KEY từ file .env ở thư mục gốc project_LLM.
# 2. Gọi trực tiếp Gemini để sinh vụ án Bí ẩn chậu cây.
# 3. Dùng Pydantic kiểm tra JSON, số lượng vật thể, ID manh mối, giả thuyết, thử nghiệm và bằng chứng cần thiết.
# 4. Nếu hợp lệ, lưu kịch bản vào LLM/scripts/output/detective_case.json.
# 5. Nếu không hợp lệ, in ra lỗi cụ thể để mình đánh giá khả năng của model.


"""Thử Gemini sinh một vụ án Module 3; KHÔNG chạy qua LLM Server."""

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, model_validator

# LLM/scripts/ -> LLM/ -> project_LLM/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

MODEL = os.getenv("MODEL_DETECTIVE", "gemini-3.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Các vị trí tương tác mà FE có thể hỗ trợ.
SCENE_SLOTS = {
    "classroom": {"desk_left", "desk_right", "window", "shelf"},
    "garden": {"center", "soil", "fence", "corner"},
    "lab": {"table_left", "table_right", "cabinet", "window"},
}

# Danh sách sprite dự kiến của trò chơi.
ASSETS = {
    "wilted_plant", "dry_soil", "watering_can", "notebook",
    "water_tank", "lamp", "thermometer", "toy_robot", "magnifier",
}


# ============================================================
# 1. SCHEMA JSON CỦA VỤ ÁN
# ============================================================

class GameObject(BaseModel):
    object_id: str
    label: str
    asset_id: str
    slot_id: str
    clue_id: str


class Clue(BaseModel):
    id: str
    title: str
    description: str


class Hypothesis(BaseModel):
    id: str
    label: str


class Experiment(BaseModel):
    id: str
    label: str
    result: str
    unlocks_clue_id: str


class Solution(BaseModel):
    hypothesis_id: str
    required_evidence_ids: list[str]
    explanation: str


class DetectiveCase(BaseModel):
    topic_id: str
    title: str
    introduction: str
    scene_id: str
    background_prompt: str
    objects: list[GameObject]
    clues: list[Clue]
    hypotheses: list[Hypothesis]
    experiments: list[Experiment]
    solution: Solution
    feedback_if_wrong: str
    feedback_if_correct: str

    @model_validator(mode="after")
    def check_game_logic(self):
        """
        Kiểm tra:
        - Số vật thể, manh mối và giả thuyết.
        - Không trùng ID hoặc vị trí.
        - Các liên kết object -> clue có hợp lệ không.
        - Các manh mối bắt buộc có thể thu thập được không.
        """
        if self.topic_id != "plants":
            raise ValueError("Bản test đầu tiên chỉ chấp nhận topic_id='plants'.")

        if self.scene_id not in SCENE_SLOTS:
            raise ValueError("scene_id chưa được FE hỗ trợ.")

        if not 3 <= len(self.objects) <= 5:
            raise ValueError("Cần 3-5 vật thể tương tác.")

        if not 3 <= len(self.clues) <= 6:
            raise ValueError("Cần 3-6 manh mối.")

        if len(self.hypotheses) != 3 or not self.experiments:
            raise ValueError("Cần đúng 3 giả thuyết và ít nhất 1 thử nghiệm.")

        def unique(values, name):
            if len(values) != len(set(values)):
                raise ValueError(f"Trùng {name}.")

        unique([x.object_id for x in self.objects], "object_id")
        unique([x.slot_id for x in self.objects], "slot_id")
        unique([x.id for x in self.clues], "clue ID")
        unique([x.id for x in self.hypotheses], "hypothesis ID")
        unique([x.id for x in self.experiments], "experiment ID")

        clue_ids = {x.id for x in self.clues}
        hypothesis_ids = {x.id for x in self.hypotheses}
        available_clues = set()

        # Một vật thể chỉ được sử dụng asset và slot đã hỗ trợ.
        # clue_id phải tồn tại trong danh sách clues.
        for obj in self.objects:
            if obj.asset_id not in ASSETS:
                raise ValueError(f"Asset chưa hỗ trợ: {obj.asset_id}")

            if obj.slot_id not in SCENE_SLOTS[self.scene_id]:
                raise ValueError(f"Slot không thuộc hiện trường: {obj.slot_id}")

            if obj.clue_id not in clue_ids:
                raise ValueError(
                    f"Object tham chiếu clue không tồn tại: {obj.clue_id}"
                )

            available_clues.add(obj.clue_id)

        # Thử nghiệm có thể mở khóa thêm manh mối.
        for experiment in self.experiments:
            if experiment.unlocks_clue_id not in clue_ids:
                raise ValueError("Thử nghiệm mở khóa manh mối không tồn tại.")

            available_clues.add(experiment.unlocks_clue_id)

        required = self.solution.required_evidence_ids

        if len(required) < 2 or len(required) != len(set(required)):
            raise ValueError("Lời giải cần ít nhất 2 bằng chứng khác nhau.")

        if self.solution.hypothesis_id not in hypothesis_ids:
            raise ValueError("Giả thuyết đúng không có trong danh sách.")

        if not set(required) <= available_clues:
            raise ValueError("Có bằng chứng bắt buộc không thể thu thập.")

        if not clue_ids <= available_clues:
            raise ValueError("Có manh mối không thể khám phá.")

        return self


# ============================================================
# 2. PROMPT SINH VỤ ÁN
# ============================================================

def build_prompt() -> str:
    """
    Prompt thử nghiệm:
    - Một chủ đề khoa học.
    - Giới hạn scene, slot và asset.
    - Yêu cầu bằng chứng và lời giải nhất quán.
    """
    return """Bạn là nhà thiết kế trò chơi 'Thám tử khoa học' cho trẻ 8 tuổi.

Sinh MỘT vụ án ngắn bằng tiếng Việt, chủ đề
'Thực vật kỳ thú' (topic_id='plants').

Vụ án dựa trên kiến thức đáng tin cậy:
- Thiếu nước có thể làm cây héo.
- Đất khô và nhật ký tưới cây có thể là các bằng chứng.

GAME ENGINE CHỈ HỖ TRỢ:

1. scene_id: classroom, garden hoặc lab.

2. slot theo scene:
   classroom: desk_left, desk_right, window, shelf
   garden: center, soil, fence, corner
   lab: table_left, table_right, cabinet, window

3. asset_id:
   wilted_plant, dry_soil, watering_can, notebook,
   water_tank, lamp, thermometer, toy_robot, magnifier.

4. Quy tắc trò chơi:
- Có 3-4 objects.
- Có 3-6 clues.
- Có đúng 3 hypotheses, trong đó 1 giả thuyết đúng.
- Có ít nhất 1 experiment đơn giản, an toàn,
  với kết quả cố định.
- Mỗi object có clue_id trỏ tới một clue.
- Mỗi experiment có unlocks_clue_id.
- Các object phải dùng slot khác nhau thuộc scene đã chọn.
- Mọi clue phải tìm được qua object hoặc experiment.
- solution phải chọn 1 hypothesis và ít nhất 2
  required_evidence_ids khác nhau, có thể thu thập được.
- Không tiết lộ lời giải trong introduction.
- Không làm trẻ sợ hãi.
- background_prompt bằng tiếng Anh, chỉ mô tả phông nền,
  không yêu cầu vẽ các vật thể tương tác chủ chốt.

Trả về duy nhất một JSON object gồm:

topic_id, title, introduction, scene_id,
background_prompt, objects[], clues[], hypotheses[],
experiments[], solution, feedback_if_wrong,
feedback_if_correct.

Mỗi object:
object_id, label, asset_id, slot_id, clue_id.

Mỗi clue:
id, title, description.

Mỗi hypothesis:
id, label.

Mỗi experiment:
id, label, result, unlocks_clue_id.

solution:
hypothesis_id, required_evidence_ids[], explanation.

Các ID dùng ASCII không dấu.
Nội dung cho trẻ bằng tiếng Việt.
"""


# ============================================================
# 3. GỌI GEMINI VÀ KIỂM TRA KẾT QUẢ
# ============================================================

def main() -> int:
    if not GEMINI_API_KEY:
        print("THIẾU GEMINI_API_KEY trong project_LLM/.env")
        return 1

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": build_prompt()}],
            }
        ],
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 4000,
            "responseMimeType": "application/json",
        },
    }

    print(f"[1] Gọi model: {MODEL}")

    try:
        response = httpx.post(
            url,
            headers={"x-goog-api-key": GEMINI_API_KEY},
            json=payload,
            timeout=90,
        )


        # Kiểm tra lỗi API trước khi xử lý kết quả.
        if response.status_code != 200:
            print(f"[HTTP ERROR] Status code: {response.status_code}")

            try:
                error = response.json().get("error", {})
                print("Error status:", error.get("status"))
                print("Error message:", error.get("message"))
            except ValueError:
                print("Response:", response.text[:500])

            return 1

        raw = response.json()


        content = raw["candidates"][0]["content"]["parts"][0]["text"]

        # Chuyển chuỗi JSON thành dict và validate bằng Pydantic.
        case = DetectiveCase.model_validate(json.loads(content))

    except (
        httpx.HTTPError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        ValidationError,
    ) as exc:
        print(f"[FAIL] Không thể tạo/kiểm tra vụ án: {exc}")
        return 1

    # Chỉ lưu khi dữ liệu vượt qua kiểm tra.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "detective_case.json"

    output_file.write_text(
        json.dumps(case.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[PASS] JSON hợp lệ, liên kết ID và luật khám phá đạt kiểm tra.")
    print(f"Vụ án: {case.title} | Scene: {case.scene_id}")
    print(f"Objects={len(case.objects)} | Clues={len(case.clues)}")
    print(f"Hypothesis đúng: {case.solution.hypothesis_id}")
    print(f"Đã lưu: {output_file}")
    print("CẦN ĐỌC TAY: tính đúng khoa học, độ tuổi, manh mối có hợp lý không.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
