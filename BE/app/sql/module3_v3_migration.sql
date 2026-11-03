
-- ============================================================
-- LEARNMATE AI — MODULE 3 V3.0
--
-- Migration bổ sung:
-- 1. RPC mở gợi ý nguyên tử.
-- 2. RPC chơi lại vụ án V3.
--
-- Yêu cầu:
-- - Đã có bảng public.detective_cases.
-- - Đã chạy migration V2.
-- - BE dùng Supabase service_role key.
--
-- Không DROP bảng hoặc xóa dữ liệu V2.
-- ============================================================


-- ============================================================
-- 1. RPC: MỞ GỢI Ý TIẾP THEO
-- ============================================================

CREATE OR REPLACE FUNCTION
public.detective_reveal_next_hint(
    p_case_id UUID,
    p_child_id BIGINT,
    p_request_id TEXT
)
RETURNS JSONB

LANGUAGE plpgsql

SECURITY INVOKER

SET search_path = public

AS $$
DECLARE
    v_case JSONB;
    v_state JSONB;

    v_ids JSONB;
    v_requests JSONB;

    v_hints JSONB;
    v_hint_id TEXT;

    v_repeat BOOLEAN := FALSE;

BEGIN

    -- --------------------------------------------------------
    -- 1.1. Kiểm tra request ID
    -- --------------------------------------------------------

    IF
        p_request_id IS NULL
        OR length(p_request_id) < 8
        OR length(p_request_id) > 100
    THEN

        RETURN jsonb_build_object(
            'error',
            'INVALID_REQUEST_ID'
        );

    END IF;


    -- --------------------------------------------------------
    -- 1.2. Khóa hàng bằng SELECT FOR UPDATE
    --
    -- Hai request cùng lúc phải thực hiện tuần tự.
    -- --------------------------------------------------------

    SELECT
        case_data,
        play_state

    INTO
        v_case,
        v_state

    FROM public.detective_cases

    WHERE
        id = p_case_id
        AND child_id = p_child_id

    FOR UPDATE;


    IF NOT FOUND THEN

        RETURN jsonb_build_object(
            'error',
            'CASE_NOT_FOUND'
        );

    END IF;


    -- --------------------------------------------------------
    -- 1.3. Chỉ cho phép V3
    -- --------------------------------------------------------

    IF COALESCE(
        (v_case->>'schema_version')::INT,
        2
    ) <> 3 THEN

        RETURN jsonb_build_object(
            'error',
            'CASE_VERSION_UNSUPPORTED'
        );

    END IF;


    -- --------------------------------------------------------
    -- 1.4. Đọc trạng thái
    -- --------------------------------------------------------

    v_state := COALESCE(
        v_state,
        '{}'::JSONB
    );

    v_ids := COALESCE(
        v_state->'revealed_hint_ids',
        '[]'::JSONB
    );

    v_requests := COALESCE(
        v_state->'hint_request_results',
        '{}'::JSONB
    );

    v_hints := v_case->'hints';


    -- --------------------------------------------------------
    -- 1.5. Kiểm tra request trùng
    --
    -- Nếu cùng request_id đã mở một hint:
    -- trả lại hint đó, không tăng lượt.
    -- --------------------------------------------------------

    IF v_requests ? p_request_id THEN

        v_hint_id :=
            v_requests->>p_request_id;

        v_repeat := TRUE;

    ELSE

        -- ----------------------------------------------------
        -- 1.6. Kiểm tra vụ án đã kết thúc
        -- ----------------------------------------------------

        IF COALESCE(
            (v_state->>'completed')::BOOLEAN,
            FALSE
        ) THEN

            RETURN jsonb_build_object(
                'error',
                'CASE_ALREADY_COMPLETED'
            );

        END IF;


        -- ----------------------------------------------------
        -- 1.7. Kiểm tra đã hết gợi ý
        -- ----------------------------------------------------

        IF jsonb_array_length(v_ids)
            >= jsonb_array_length(v_hints)
        THEN

            RETURN jsonb_build_object(
                'error',
                'HINTS_EXHAUSTED'
            );

        END IF;


        -- ----------------------------------------------------
        -- 1.8. Lấy hint tiếp theo
        --
        -- V3 lưu hints theo order liên tục 1..N.
        --
        -- jsonb array sử dụng index từ 0.
        -- ----------------------------------------------------

        v_hint_id := (
            v_hints->jsonb_array_length(v_ids)
        )->>'id';


        -- ----------------------------------------------------
        -- 1.9. Đánh dấu hint đã mở
        -- ----------------------------------------------------

        v_ids := v_ids || to_jsonb(
            v_hint_id
        );

        v_requests :=
            v_requests ||
            jsonb_build_object(
                p_request_id,
                v_hint_id
            );


        -- ----------------------------------------------------
        -- 1.10. Cập nhật state
        -- ----------------------------------------------------

        v_state := jsonb_set(
            v_state,
            '{revealed_hint_ids}',
            v_ids,
            TRUE
        );

        v_state := jsonb_set(
            v_state,
            '{hint_request_results}',
            v_requests,
            TRUE
        );


        -- ----------------------------------------------------
        -- 1.11. Commit state trong transaction hiện tại
        -- ----------------------------------------------------

        UPDATE public.detective_cases

        SET play_state = v_state

        WHERE
            id = p_case_id
            AND child_id = p_child_id;

    END IF;


    -- --------------------------------------------------------
    -- 1.12. Trả kết quả
    -- --------------------------------------------------------

    RETURN jsonb_build_object(
        'hint_id',
            v_hint_id,

        'revealed_hint_ids',
            v_ids,

        'already_revealed_for_request',
            v_repeat
    );

END;
$$;


-- ============================================================
-- 2. RPC: CHƠI LẠI VỤ ÁN V3
-- ============================================================

CREATE OR REPLACE FUNCTION
public.detective_replay_v3(
    p_case_id UUID,
    p_child_id BIGINT,
    p_initial JSONB
)

RETURNS BOOLEAN

LANGUAGE plpgsql

SECURITY INVOKER

SET search_path = public

AS $$

DECLARE
    v_count INT;

BEGIN

    -- --------------------------------------------------------
    -- Chỉ reset:
    -- - Vụ án thuộc child_id.
    -- - Schema version = 3.
    -- - Đã hoàn thành.
    --
    -- Giữ nguyên:
    -- - case_data.
    -- - image_path.
    -- - media_manifest.
    -- --------------------------------------------------------

    UPDATE public.detective_cases

    SET
        play_state = p_initial,

        last_completed_at = NULL,

        last_outcome = NULL

    WHERE
        id = p_case_id

        AND child_id = p_child_id

        AND (
            case_data->>'schema_version'
        )::INT = 3

        AND COALESCE(
            (play_state->>'completed')::BOOLEAN,
            FALSE
        ) = TRUE;


    GET DIAGNOSTICS
        v_count = ROW_COUNT;

    RETURN v_count = 1;

END;
$$;


-- ============================================================
-- 3. GIỚI HẠN QUYỀN THỰC THI
--
-- Backend phải dùng service_role.
-- Không cấp quyền công khai cho anon/authenticated.
-- ============================================================

REVOKE ALL ON FUNCTION
public.detective_reveal_next_hint(
    UUID,
    BIGINT,
    TEXT
)
FROM PUBLIC;


REVOKE ALL ON FUNCTION
public.detective_replay_v3(
    UUID,
    BIGINT,
    JSONB
)
FROM PUBLIC;


GRANT EXECUTE ON FUNCTION
public.detective_reveal_next_hint(
    UUID,
    BIGINT,
    TEXT
)
TO service_role;


GRANT EXECUTE ON FUNCTION
public.detective_replay_v3(
    UUID,
    BIGINT,
    JSONB
)
TO service_role;
