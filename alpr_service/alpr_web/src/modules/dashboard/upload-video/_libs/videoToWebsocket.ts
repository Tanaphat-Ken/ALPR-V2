import { message } from "antd";
import type { AppDispatch } from "@/shared/store";
import {
  appendProcessedImageList,
  setProcessedFrames,
  toggleIsPending,
} from "@/shared/store/dashboard/upload-video-slice";

let webSocketInstance: WebSocket | null = null;

const initialWebSocketConnection = async (
  token: string,
  dispatch: AppDispatch,
): Promise<WebSocket> => {
  return new Promise((resolve, reject) => {
    const baseUrl =
      process.env.NEXT_PUBLIC_WEBSOCKET_VIDEO_HANLER ||
      "ws://35.187.233.205/ws/video";
    const ws = new WebSocket(`${baseUrl}/${token}`);
    ws.onopen = () => {
      message.info("Connected to Server");
      resolve(ws);
    };
    ws.onclose = () => {
      message.info("Processing completed - Disconnected from Server");
      dispatch(toggleIsPending());
    };
    ws.onerror = (error) => {
      message.error(`WebSocket Error: ${error}`);
      dispatch(toggleIsPending());
      reject(error);
    };
  });
};

const closeWebSocketConnection = () => {
  if (webSocketInstance) {
    webSocketInstance.close();
    webSocketInstance = null;
  }
};

const sendFramesOverWebSocket = async (
  video: HTMLVideoElement,
  ws: WebSocket,
) => {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  video.addEventListener("loadeddata", async () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Optimized FPS: 10 = good balance between detection accuracy and performance
    // - Lower = fewer duplicates, faster processing
    // - Higher = better detection for fast-moving vehicles
    const fps = 30;
    const frameInterval = 1 / fps;
    let currentFrame = 0;
    let isProcessing = false;
    let hasFinalized = false; // Prevent duplicate finalization

    const processFrame = async () => {
      if (isProcessing) {
        console.warn("Previous frame still processing, skipping");
        return;
      }

      isProcessing = true;
      const targetTime = currentFrame * frameInterval;

      // Check if we've processed all frames
      if (targetTime >= video.duration) {
        if (!hasFinalized) {
          hasFinalized = true;
          console.log(
            `Video processing completed. Processed ${currentFrame} frames (${video.duration.toFixed(2)}s)`
          );
          // Send blank frame to trigger tracker finalization
          const blankCanvas = document.createElement("canvas");
          blankCanvas.width = 100;
          blankCanvas.height = 100;
          const blob = await new Promise<Blob | null>((resolve) =>
            blankCanvas.toBlob(resolve, "image/jpeg", 0.1),
          );
          if (blob && ws.readyState === WebSocket.OPEN) {
            const arrayBuffer = await blob.arrayBuffer();
            ws.send(new Uint8Array(arrayBuffer));
            console.log("Blank frame sent, waiting for server to finish processing...");
            // Server will send completion message and close connection
          }
        }
        isProcessing = false;
        return;
      }

      if (ws.readyState !== WebSocket.OPEN) {
        console.log("WebSocket closed, stopping frame processing");
        isProcessing = false;
        return;
      }

      try {
        // Set video to target time
        video.currentTime = targetTime;

        // Wait for seek to complete
        await new Promise<void>((resolve) => {
          const onSeeked = () => {
            video.removeEventListener("seeked", onSeeked);
            resolve();
          };
          video.addEventListener("seeked", onSeeked);

          // Timeout fallback
          setTimeout(() => {
            video.removeEventListener("seeked", onSeeked);
            resolve();
          }, 1000);
        });

        // Capture and send frame
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          const blob = await new Promise<Blob | null>((resolve) =>
            canvas.toBlob(resolve, "image/jpeg", 0.8),
          );

          if (blob && ws.readyState === WebSocket.OPEN) {
            // Wait for buffer to be ready
            if (ws.bufferedAmount > 1024 * 1024) { // 1MB buffer limit
              console.warn(`Buffer full (${ws.bufferedAmount} bytes), waiting...`);
              await new Promise(resolve => setTimeout(resolve, 100));
            }

            const arrayBuffer = await blob.arrayBuffer();
            ws.send(new Uint8Array(arrayBuffer));
            console.log(
              `Frame ${currentFrame} sent (time: ${targetTime.toFixed(2)}s, duration: ${video.duration.toFixed(2)}s)`
            );

            currentFrame++;
            isProcessing = false;

            // Continue processing next frame
            if (ws.readyState === WebSocket.OPEN && targetTime < video.duration) {
              // Use requestAnimationFrame for better timing
              requestAnimationFrame(() => processFrame());
            }
          } else {
            isProcessing = false;
          }
        } else {
          isProcessing = false;
        }
      } catch (error) {
        console.error("Error processing frame:", error);
        isProcessing = false;
      }
    };

    processFrame();
  });

  video.load();
};

const videoToWebsocket = async (
  videoFile: File,
  token: string,
  dispatch: AppDispatch,
) => {
  try {
    webSocketInstance = await initialWebSocketConnection(token, dispatch);
    const video = document.createElement("video");
    video.src = URL.createObjectURL(videoFile);
    video.crossOrigin = "anonymous";
    video.muted = true;
    video.autoplay = false;
    video.loop = false;
    video.preload = "auto";

    webSocketInstance.onmessage = async (data) => {
      const res = JSON.parse(data.data);

      // Handle status messages from backend
      if (res.status === "progress") {
        // Update progress indicator
        dispatch(setProcessedFrames(res.frame_number));
        console.log(`Processing frame ${res.frame_number}, ${res.queue_size} frames in queue`);
      } else if (res.status === "processing") {
        console.log("Server confirmed: " + res.message);
        message.info(res.message);
      } else if (res.status === "completed") {
        console.log("Server confirmed: " + res.message);
        message.success(res.message);
        // Server will close connection after this
      } else if (res.frame_no) {
        dispatch(setProcessedFrames(parseInt(res.frame_no)));
      } else if (res.image) {
        dispatch(
          appendProcessedImageList({
            image: res.image,
            plateCropImage: res.plateCropImage || null,
            carBbox: res.car_bbox,
            plateBbox: res.plate_bbox,
            plateId: res.plate_id,
            province: res.province,
            timeStamp: new Date().toISOString(),
          }),
        );
      }
    };

    sendFramesOverWebSocket(video, webSocketInstance);
  } catch (error) {
    message.error(`WebSocket failed to connect: ${error}`);
    dispatch(toggleIsPending());
  }
};

export { closeWebSocketConnection };
export default videoToWebsocket;
