-- Fix all sequence out-of-sync issues
-- Run this after importing data or if you get duplicate key errors

-- Fix image_logs sequence
SELECT setval('websocket_image_logs_log_id_seq', 
    COALESCE((SELECT MAX(log_id) FROM image_logs), 1), 
    (SELECT MAX(log_id) FROM image_logs) IS NOT NULL);

-- Fix car_bbox sequence
SELECT setval('car_bbox_car_bbox_id_seq', 
    COALESCE((SELECT MAX(car_bbox_id) FROM car_bbox), 1), 
    (SELECT MAX(car_bbox_id) FROM car_bbox) IS NOT NULL);

-- Fix plate_bbox sequence
SELECT setval('plate_bbox_plate_bbox_id_seq', 
    COALESCE((SELECT MAX(plate_bbox_id) FROM plate_bbox), 1), 
    (SELECT MAX(plate_bbox_id) FROM plate_bbox) IS NOT NULL);

-- Fix users sequence (if exists)
SELECT setval('users_user_id_seq', 
    COALESCE((SELECT MAX(user_id) FROM users), 1), 
    (SELECT MAX(user_id) FROM users) IS NOT NULL);

-- Fix subscription sequence (if exists)
SELECT setval('subscription_subscription_id_seq', 
    COALESCE((SELECT MAX(subscription_id) FROM subscription), 1), 
    (SELECT MAX(subscription_id) FROM subscription) IS NOT NULL);

-- Verify all sequences
SELECT 
    'image_logs' as table_name,
    (SELECT MAX(log_id) FROM image_logs) as max_id,
    (SELECT last_value FROM websocket_image_logs_log_id_seq) as seq_value
UNION ALL
SELECT 
    'car_bbox',
    (SELECT MAX(car_bbox_id) FROM car_bbox),
    (SELECT last_value FROM car_bbox_car_bbox_id_seq)
UNION ALL
SELECT 
    'plate_bbox',
    (SELECT MAX(plate_bbox_id) FROM plate_bbox),
    (SELECT last_value FROM plate_bbox_plate_bbox_id_seq);
