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
      "ws://localhost:5002/video";
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

  video.addEventListener("loadeddata", () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    video.play();

    const captureFrame = async () => {
      // Check if video has ended
      if (video.currentTime >= video.duration) {
        console.log(
          "Video processing completed, sending blank frame to finalize...",
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
          console.log("Blank frame sent, closing connection in 2 seconds...");
          // Close connection after a short delay to allow server to process
          setTimeout(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.close();
            }
          }, 2000);
        }
        return;
      }

      if (ws.readyState !== WebSocket.OPEN) return;

      ctx?.drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise((resolve) =>
        canvas.toBlob(resolve, "image/jpeg", 0.95),
      );

      if (blob instanceof Blob) {
        const arrayBuffer = await blob.arrayBuffer();
        if (ws.readyState === WebSocket.OPEN)
          ws.send(new Uint8Array(arrayBuffer));
      }

      video.currentTime += 1 / 30;
    };

    video.addEventListener("seeked", captureFrame);
    captureFrame();
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
      if (res.frame_no) {
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
