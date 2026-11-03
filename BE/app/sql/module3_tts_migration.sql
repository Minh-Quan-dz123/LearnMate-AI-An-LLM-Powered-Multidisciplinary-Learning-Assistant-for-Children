
-- ========================================================
-- MODULE 3 V2 — GEMINI TTS CACHE
-- ========================================================

CREATE OR REPLACE FUNCTION
public.detective_cache_audio_path(
  p_case_id UUID,
  p_child_id BIGINT,
  p_cache_key TEXT,
  p_storage_path TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
DECLARE
  final_path TEXT;
BEGIN
  IF length(p_cache_key) > 180
     OR length(p_storage_path) > 500
     OR p_cache_key = ''
     OR p_storage_path = '' THEN
    RAISE EXCEPTION 'Invalid cache path';
  END IF;

  UPDATE public.detective_cases
  SET media_manifest = jsonb_set(
    COALESCE(media_manifest, '{}'::jsonb),
    '{audio}',
    COALESCE(
      media_manifest->'audio',
      '{}'::jsonb
    ) || jsonb_build_object(
      p_cache_key,
      p_storage_path
    ),
    true
  )

  WHERE id = p_case_id
    AND child_id = p_child_id

  RETURNING
    media_manifest->'audio'->>p_cache_key
  INTO final_path;

  RETURN final_path;
END;
$$;

REVOKE ALL ON FUNCTION
public.detective_cache_audio_path(
  UUID, BIGINT, TEXT, TEXT
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION
public.detective_cache_audio_path(
  UUID, BIGINT, TEXT, TEXT
) TO service_role;
