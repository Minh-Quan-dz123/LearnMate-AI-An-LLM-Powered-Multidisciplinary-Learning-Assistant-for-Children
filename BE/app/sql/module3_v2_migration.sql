
-- ========================================================
-- MODULE 3 V2 — GIAI ĐOẠN 2 + 3
-- ========================================================

ALTER TABLE public.detective_cases
  ADD COLUMN IF NOT EXISTS
    media_manifest JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS
    last_outcome TEXT;

ALTER TABLE public.detective_cases
  DROP CONSTRAINT IF EXISTS
    detective_cases_last_outcome_check;

ALTER TABLE public.detective_cases
  ADD CONSTRAINT detective_cases_last_outcome_check
  CHECK (
    last_outcome IS NULL
    OR last_outcome IN ('solved', 'unsolved')
  );

-- Vụ án cũ đã hoàn thành được tính là solved.
UPDATE public.detective_cases
SET last_outcome = 'solved'
WHERE last_completed_at IS NOT NULL
  AND last_outcome IS NULL;

-- Chống hai request kết luận cập nhật cùng một lượt.
CREATE OR REPLACE FUNCTION
public.detective_solve_compare_set(
  p_case_id UUID,
  p_child_id BIGINT,
  p_expected JSONB,
  p_new JSONB,
  p_finished BOOLEAN,
  p_outcome TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
  updated_count INTEGER;
BEGIN
  IF p_outcome IS NOT NULL
     AND p_outcome NOT IN ('solved', 'unsolved') THEN
    RAISE EXCEPTION 'Invalid outcome';
  END IF;

  UPDATE public.detective_cases
  SET
    play_state = p_new,

    last_completed_at = CASE
      WHEN p_finished THEN now()
      ELSE last_completed_at
    END,

    last_outcome = CASE
      WHEN p_finished THEN p_outcome
      ELSE last_outcome
    END

  WHERE id = p_case_id
    AND child_id = p_child_id
    AND play_state = p_expected;

  GET DIAGNOSTICS updated_count = ROW_COUNT;

  RETURN updated_count = 1;
END;
$$;

REVOKE ALL ON FUNCTION
public.detective_solve_compare_set(
  UUID, BIGINT, JSONB, JSONB, BOOLEAN, TEXT
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION
public.detective_solve_compare_set(
  UUID, BIGINT, JSONB, JSONB, BOOLEAN, TEXT
) TO service_role;
