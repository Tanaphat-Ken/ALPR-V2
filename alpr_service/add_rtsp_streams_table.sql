-- Migration: เพิ่มตาราง rtsp_streams สำหรับเก็บ camera config ของ user
-- รัน: psql -U postgres -d alpr_db -f add_rtsp_streams_table.sql

CREATE TABLE IF NOT EXISTS public.rtsp_streams (
    stream_id  SERIAL PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    -- รองรับทั้ง rtsp:// และ path ไฟล์วิดีโอ (สำหรับ dev/demo)
    rtsp_url   VARCHAR(1024) NOT NULL,
    location   VARCHAR(255),
    enabled    BOOLEAN NOT NULL DEFAULT FALSE,
    fps        INTEGER NOT NULL DEFAULT 10,
    frame_skip INTEGER NOT NULL DEFAULT 3,
    -- FK → users (NULL = system-level camera ที่ไม่ผูกกับ user)
    user_id    INTEGER REFERENCES public.users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Index ที่ใช้บ่อย
CREATE INDEX IF NOT EXISTS idx_rtsp_streams_user_id  ON public.rtsp_streams(user_id);
CREATE INDEX IF NOT EXISTS idx_rtsp_streams_enabled  ON public.rtsp_streams(enabled);

COMMENT ON TABLE  public.rtsp_streams               IS 'Camera / video-source configs ของแต่ละ user';
COMMENT ON COLUMN public.rtsp_streams.rtsp_url      IS 'rtsp:// URL หรือ path ไฟล์วิดีโอ ( /app/videos/xxx.mp4 )';
COMMENT ON COLUMN public.rtsp_streams.user_id       IS 'FK → users.user_id  NULL = system-level';

-- เพิ่ม column service_type ใน video_logs (ถ้ายังไม่มี)
-- ใช้สำหรับแยกว่า log นั้นมาจาก rtsp หรือ video upload
ALTER TABLE public.video_logs
    ADD COLUMN IF NOT EXISTS service_type VARCHAR(50) DEFAULT 'VIDEO_WEBSOCKET';

-- เพิ่ม column stream_id ใน video_logs เพื่อ FK กลับ rtsp_streams (optional)
ALTER TABLE public.video_logs
    ADD COLUMN IF NOT EXISTS stream_id INTEGER REFERENCES public.rtsp_streams(stream_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_video_logs_stream_id ON public.video_logs(stream_id);
CREATE INDEX IF NOT EXISTS idx_video_logs_service_type ON public.video_logs(service_type);
