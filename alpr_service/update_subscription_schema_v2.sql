-- Drop the restrictive check constraint on service_type
ALTER TABLE subscription DROP CONSTRAINT IF EXISTS subscription_service_type_check;

-- Drop the restrictive check constraint on billing_period if it exists and causes issues (optional but recommended for flexibility)
ALTER TABLE subscription DROP CONSTRAINT IF EXISTS subscription_billing_period_check;

-- Add the new columns (IF NOT EXISTS to be safe if you ran the previous script partially)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscription' AND column_name='api_request_limit') THEN
        ALTER TABLE subscription ADD COLUMN api_request_limit INT DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscription' AND column_name='video_upload_limit') THEN
        ALTER TABLE subscription ADD COLUMN video_upload_limit INT DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscription' AND column_name='has_api_access') THEN
        ALTER TABLE subscription ADD COLUMN has_api_access INT DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscription' AND column_name='has_websocket_access') THEN
        ALTER TABLE subscription ADD COLUMN has_websocket_access INT DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscription' AND column_name='has_video_upload') THEN
        ALTER TABLE subscription ADD COLUMN has_video_upload INT DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscription' AND column_name='has_rtsp_stream') THEN
        ALTER TABLE subscription ADD COLUMN has_rtsp_stream INT DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscription' AND column_name='token_limit') THEN
        ALTER TABLE subscription ADD COLUMN token_limit INT DEFAULT 5;
    END IF;
END $$;

-- Insert sample data for tiers with the new columns
-- Tier 1: WebSocket + API 1000 requests
INSERT INTO subscription (billing_period, service_type, price, description, api_request_limit, video_upload_limit, has_api_access, has_websocket_access, has_video_upload, has_rtsp_stream, token_limit, created_at, updated_at)
VALUES ('MONTHLY', 'TIER_1', 299, 'Tier 1: Starter Plan', 1000, 0, 1, 1, 0, 0, 5, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Tier 2: WebSocket 1000 + API 1000 + Video 1000
INSERT INTO subscription (billing_period, service_type, price, description, api_request_limit, video_upload_limit, has_api_access, has_websocket_access, has_video_upload, has_rtsp_stream, token_limit, created_at, updated_at)
VALUES ('MONTHLY', 'TIER_2', 499, 'Tier 2: Advanced Plan', 1000, 1000, 1, 1, 1, 0, 10, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Tier 3: All above + RTSP
INSERT INTO subscription (billing_period, service_type, price, description, api_request_limit, video_upload_limit, has_api_access, has_websocket_access, has_video_upload, has_rtsp_stream, token_limit, created_at, updated_at)
VALUES ('MONTHLY', 'TIER_3', 899, 'Tier 3: Pro Plan', 5000, 5000, 1, 1, 1, 1, 20, NOW(), NOW())
ON CONFLICT DO NOTHING;
