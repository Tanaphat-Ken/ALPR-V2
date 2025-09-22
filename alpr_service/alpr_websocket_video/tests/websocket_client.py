import asyncio
import cv2
import websockets
import logging
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

VIDEO_PATH = "tests/car-passing.mp4"
WS_URL = "ws://localhost:5002/video/token_for_video_service_test_jonhdoe_3"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_video_frames(websocket, video_path: str):
  cap = cv2.VideoCapture(video_path)
  
  if not cap.isOpened():
    logger.error(f"Failed to open video file: {video_path}")
    return

  frame_count = 0
  
  try:
    while True:
      ret, frame = cap.read()
      
      if not ret:
        logger.info("No more frames to read. Exiting.")
        break

      _, buffer = cv2.imencode('.jpg', frame)
      frame_bytes = buffer.tobytes()

      # if frame_count % 2 == 0:
      if frame_count % 3 == 0:
        await websocket.send(frame_bytes)
        logger.info(f"Sent frame {frame_count} (size: {len(frame_bytes)} bytes)")

      frame_count += 1

      await asyncio.sleep(1 / 300) # real video time
      # await asyncio.sleep(1/30)

  except Exception as e:
    logger.error(f"Error in send_video_frames: {e}")
  finally:
    cap.release()


async def receive_server_responses(websocket):
  try:
    while True:
      response = await websocket.recv()

      if isinstance(response, bytes):
        try:
          logger.info(f"Received image bytes)")
        except Exception as e:
          logger.error(f"Error decoding image: {e}")
      else:
        logger.info(f"Received response from server: {response}")

  except websockets.exceptions.ConnectionClosed as e:
    logger.error(f"WebSocket connection closed: {e}")
  except Exception as e:
    logger.error(f"Error in receive_server_responses: {e}")


async def main():
  try:
    async with websockets.connect(WS_URL) as websocket:
      logger.info(f"Connected to WebSocket server at {WS_URL}")
      
      send_task = asyncio.create_task(send_video_frames(websocket, VIDEO_PATH))
      receive_task = asyncio.create_task(receive_server_responses(websocket))
      
      await asyncio.gather(send_task, receive_task)

  except (ConnectionClosedError, ConnectionClosedOK) as e:
    if e.code == 4001:
      logger.error(f"Connection closed: Invalid token - {e.reason}")
    elif e.code == 1011:
      logger.error(f"Connection closed: Internal server error - {e.reason}")
    else:
      logger.error(f"Connection closed: {e.code} - {e.reason}")
  except Exception as e:
    logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
  asyncio.run(main())
