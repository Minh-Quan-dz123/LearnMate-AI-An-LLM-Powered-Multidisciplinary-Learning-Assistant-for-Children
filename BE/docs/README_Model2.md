# Module 2 — Backend

**Người phụ trách:** Thành viên Backend Module 2

## 1. Phạm vi

Module 2 phụ trách bài tập câu hỏi mở.

Chức năng chính:

- Sinh câu hỏi mở.
- Nhận câu trả lời của trẻ.
- Gọi LLM để đánh giá.
- Trả về điểm số và nhận xét bằng tiếng Việt.

Không cần lưu lịch sử bài làm trong Database.

## 2. Các file và hàm dự kiến

### app/routers/module2.py

**generate_questions()**

- Nhận yêu cầu sinh bài từ FE.
- Kiểm tra dữ liệu đầu vào.
- Gọi EGM sinh câu hỏi.
- Trả về JSON câu hỏi.

**evaluate_answer()**

- Nhận câu hỏi và câu trả lời của trẻ.
- Gọi EGM đánh giá.
- Trả kết quả về FE.

### app/schemas/module2.py

Các Pydantic model đề xuất:

**GenerateQuestionsRequest**

- user_id
- subject
- topic
- level
- question_count

**EvaluateAnswerRequest**

- user_id
- question
- answer
- subject
- topic
- level

**EvaluationResult**

- score
- feedback
- suggestion

### app/egm/module2_egm.py

**build_generation_prompt()**

- Tạo prompt sinh câu hỏi mở.

**build_evaluation_prompt()**

- Tạo prompt đánh giá câu trả lời.

**generate_questions()**

- Gọi LLM để sinh câu hỏi.

**evaluate_answer()**

- Gọi LLM để chấm câu trả lời.

### app/llm_client.py

**generate_text()**

- Nhận prompt và các tham số tùy chọn.
- Gửi HTTP request đến LLM Server.
- Trả về kết quả model sinh ra.

File này được cả hai module sử dụng.

## 3. API dự kiến

| Method | Endpoint              | Chức năng            |
| ------ | --------------------- | -------------------- |
| POST   | /api/module2/generate | Sinh câu hỏi mở      |
| POST   | /api/module2/evaluate | Đánh giá câu trả lời |

### Request sinh câu hỏi

    {
      "user_id": 1,
      "subject": "Đạo đức",
      "topic": "Giúp đỡ bạn bè",
      "level": "Cơ bản",
      "question_count": 2
    }

### Response sinh câu hỏi

    {
      "success": true,
      "message": "Sinh câu hỏi thành công",
      "data": {
        "questions": [
          {
            "id": 1,
            "question": "Khi thấy bạn bị ngã, em sẽ làm gì?"
          },
          {
            "id": 2,
            "question": "Em có thể giúp đỡ bạn bè bằng những việc gì?"
          }
        ]
      }
    }

### Request đánh giá

    {
      "user_id": 1,
      "subject": "Đạo đức",
      "topic": "Giúp đỡ bạn bè",
      "level": "Cơ bản",
      "question": "Khi thấy bạn bị ngã, em sẽ làm gì?",
      "answer": "Em sẽ đỡ bạn dậy và hỏi xem bạn có đau không."
    }

### Response đánh giá

    {
      "success": true,
      "message": "Đánh giá câu trả lời thành công",
      "data": {
        "score": 10,
        "feedback": "Em trả lời rất tốt! Em đã biết quan tâm và giúp đỡ bạn bè.",
        "suggestion": "Em cũng có thể nhờ thầy cô giúp nếu bạn bị thương."
      }
    }

## 4. Prompt sinh câu hỏi mẫu

Bạn là giáo viên thân thiện với trẻ em.

Hãy tạo câu hỏi mở bằng tiếng Việt theo thông tin:

- Môn học: {subject}
- Chủ đề: {topic}
- Độ khó: {level}
- Tuổi trẻ: {age}
- Số câu hỏi: {question_count}

Yêu cầu:

1. Câu hỏi ngắn gọn, rõ ràng.
2. Phù hợp với độ tuổi.
3. Cho phép trẻ trả lời bằng từ, cụm từ hoặc câu ngắn.
4. Ưu tiên câu hỏi có thể có nhiều câu trả lời hợp lý.
5. Trả về JSON theo schema đã thống nhất.

## 5. Prompt đánh giá mẫu

Bạn là giáo viên thân thiện với trẻ em.

Hãy đánh giá câu trả lời sau:

Câu hỏi: {question}

Câu trả lời của trẻ: {answer}

Môn học: {subject}

Chủ đề: {topic}

Độ khó: {level}

Yêu cầu:

1. Đánh giá theo ý nghĩa, không so khớp cứng nhắc từng từ.
2. Chấp nhận các cách diễn đạt khác nhau nếu hợp lý.
3. Cho điểm từ 0 đến 10.
4. Đưa ra nhận xét tích cực, nhẹ nhàng.
5. Nếu câu trả lời chưa đầy đủ, đưa ra gợi ý giúp trẻ cải thiện.
6. Không chê bai hoặc sử dụng lời lẽ tiêu cực.
7. Trả về JSON với các trường score, feedback, suggestion.

## 6. Luồng xử lý

### Sinh câu hỏi

1. FE gửi yêu cầu.
2. Router gọi EGM.
3. EGM tạo prompt.
4. Gọi LLM Server.
5. Kiểm tra JSON trả về.
6. Trả danh sách câu hỏi cho FE.

### Đánh giá

1. FE gửi câu hỏi và câu trả lời.
2. EGM tạo prompt đánh giá.
3. Gọi LLM Server.
4. Nhận điểm và phản hồi.
5. Chuẩn hóa JSON.
6. Trả kết quả cho FE.

## 7. Danh sách công việc

- Viết schemas/module2.py.
- Viết routers/module2.py.
- Viết prompt sinh câu hỏi.
- Viết prompt đánh giá.
- Hoàn thiện llm_client.py.
- Kiểm tra output JSON.
- Test API sinh câu hỏi.
- Test API đánh giá.
- Cập nhật tài liệu.

## 8. Ghi chú

- Không cần lưu câu trả lời vào Database.
- Không cần JWT.
- LLM là thành phần thực hiện đánh giá.
- Backend cần xử lý trường hợp model không trả về JSON hợp lệ.
- Tên key JSON bằng tiếng Anh, nội dung câu hỏi và nhận xét bằng tiếng Việt.