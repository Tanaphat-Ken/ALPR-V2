#!/usr/bin/env python3
"""
Test video pipeline with PlateDetector -> PlateSplitter -> Province/OCR.
Saves annotated frames + crops and writes per-frame metadata.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Ensure project root is in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.image_processor import ImageProcessor  # noqa: E402

VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}


def open_video_capture(video_path: Path) -> cv2.VideoCapture:
    """Open a video with best-effort backend fallbacks.

    Some OpenCV builds don't ship with FFmpeg enabled, or can't decode certain codecs
    (e.g., HEVC). This function tries a few common backends and returns the first
    that successfully opens.
    """

    backend_candidates = []
    for name in ("CAP_FFMPEG", "CAP_MSMF", "CAP_DSHOW", "CAP_GSTREAMER"):
        backend = getattr(cv2, name, None)
        if isinstance(backend, int):
            backend_candidates.append((name, backend))

    # Try explicit backends first
    for backend_name, backend in backend_candidates:
        try:
            cap = cv2.VideoCapture(str(video_path), backend)
            if cap is not None and cap.isOpened():
                return cap
        except Exception:
            continue

    # Finally, let OpenCV choose (CAP_ANY)
    return cv2.VideoCapture(str(video_path))


def slugify(value: str) -> str:
    """Filesystem-friendly name."""
    keep = []
    for ch in value:
        if ch.isalnum() or ch in ("-", "_", "."):
            keep.append(ch)
        elif ch.isspace():
            keep.append("_")
        else:
            keep.append("_")
    s = "".join(keep).strip("._ ")
    return s[:120] if len(s) > 120 else s


def get_tahoma_font(size: int = 20) -> ImageFont.ImageFont:
    """Load Tahoma font (best effort)."""
    candidates = [
        r"C:\\Windows\\Fonts\\tahoma.ttf",
        r"C:\\Windows\\Fonts\\tahomabd.ttf",
        "tahoma.ttf",
        "Tahoma.ttf",
    ]
    for p in candidates:
        try:
            if os.path.exists(p):
                return ImageFont.truetype(p, size=size)
            return ImageFont.truetype(p, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


TAHOMA_FONT = get_tahoma_font(20)


def find_first_video(data_dir: Path) -> Optional[Path]:
    if not data_dir.exists():
        return None
    for path in sorted(data_dir.rglob("*")):
        if path.suffix.lower() in VIDEO_EXTS:
            return path
    return None


def resolve_video_path(video_arg: Optional[str], data_dir: Path) -> Optional[Path]:
    """Resolve input video.

    - If video_arg is an existing path, use it.
    - If video_arg is provided but not an existing path, treat it as a filename under data_dir.
    - If video_arg is None, pick the first video found under data_dir.
    """

    if video_arg:
        candidate = Path(video_arg)
        if candidate.exists():
            return candidate

        candidate_in_data = data_dir / video_arg
        if candidate_in_data.exists():
            return candidate_in_data

        matches = [
            p
            for p in data_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in VIDEO_EXTS and p.name.lower() == video_arg.lower()
        ]
        if matches:
            return sorted(matches)[0]

        return None

    return find_first_video(data_dir)


def safe_crop(image: np.ndarray, bbox) -> Optional[np.ndarray]:
    try:
        x1, y1, x2, y2 = map(int, bbox)
        h, w = image.shape[:2]
        x1 = max(0, min(x1, w - 1))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h - 1))
        y2 = max(0, min(y2, h))
        if x2 <= x1 or y2 <= y1:
            return None
        return image[y1:y2, x1:x2]
    except Exception:
        return None


def draw_bbox(image: np.ndarray, bbox, color=(0, 255, 0), label: Optional[str] = None):
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    if label:
        # Draw label with Tahoma (Thai-friendly) using PIL
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        draw = ImageDraw.Draw(pil_img)

        text_x = x1
        text_y = max(0, y1 - 28)
        try:
            left, top, right, bottom = draw.textbbox((text_x, text_y), label, font=TAHOMA_FONT)
            pad = 4
            draw.rectangle((left - pad, top - pad, right + pad, bottom + pad), fill=(0, 0, 0))
        except Exception:
            pass

        draw.text((text_x, text_y), label, font=TAHOMA_FONT, fill=(color[2], color[1], color[0]))
        bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        image[:, :] = bgr


def process_frame(processor: ImageProcessor, frame: np.ndarray) -> Dict[str, Any]:
    timings = {}
    t0 = time.perf_counter()

    plate_detections = processor.plate_detector.predict(frame, conf=0.25, iou=0.7, imgsz=1280)
    timings["plate_detect_ms"] = (time.perf_counter() - t0) * 1000

    if not plate_detections:
        timings["total_ms"] = (time.perf_counter() - t0) * 1000
        return {
            "detected": False,
            "message": "No plate detected",
            "timings": timings,
        }

    best_plate = max(plate_detections, key=lambda x: x["confidence"])
    plate_bbox = best_plate["bbox"]
    plate_conf = best_plate["confidence"]
    plate_crop = safe_crop(frame, plate_bbox)

    if plate_crop is None:
        timings["total_ms"] = (time.perf_counter() - t0) * 1000
        return {
            "detected": False,
            "message": "Empty plate crop",
            "plate_bbox": plate_bbox,
            "plate_conf": plate_conf,
            "timings": timings,
        }

    t1 = time.perf_counter()
    split_result = processor.plate_splitter.predict(plate_crop, conf=0.25, iou=0.6, imgsz=640)
    timings["split_ms"] = (time.perf_counter() - t1) * 1000

    text_region = split_result.get("license_text")
    prov_region = split_result.get("province")

    plate_id = None
    province = None
    ocr_conf = None  # OCR model does not return confidence yet
    province_conf = None

    t2 = time.perf_counter()
    if text_region is not None:
        text_crop = safe_crop(plate_crop, text_region["bbox"])
        if text_crop is not None:
            plate_id = processor.ocr_reader.predict(text_crop)
    timings["ocr_ms"] = (time.perf_counter() - t2) * 1000

    t3 = time.perf_counter()
    if prov_region is not None:
        prov_crop = safe_crop(plate_crop, prov_region["bbox"])
        if prov_crop is not None:
            prov_results = processor.province_classifier.predict(prov_crop, topk=1)
            if prov_results:
                province, province_conf = prov_results[0]
    timings["province_ms"] = (time.perf_counter() - t3) * 1000

    parts = []
    if plate_id:
        parts.append(plate_id)
    if province:
        parts.append(province)
    full_plate = " ".join(parts) if parts else None

    timings["total_ms"] = (time.perf_counter() - t0) * 1000

    return {
        "detected": True,
        "plate_bbox": plate_bbox,
        "plate_conf": plate_conf,
        "text_region": text_region,
        "province_region": prov_region,
        "plate_id": plate_id,
        "ocr_conf": ocr_conf,
        "province": province,
        "province_conf": province_conf,
        "full_plate": full_plate,
        "timings": timings,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test video pipeline and save results.")
    parser.add_argument(
        "--video",
        type=str,
        default=None,
        help="Video path or filename inside the data folder (default: first video found in data)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Override data directory (default: <plate_recognizer>/data)",
    )
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--frame-step", type=int, default=1, help="Process every Nth frame")
    parser.add_argument("--max-frames", type=int, default=0, help="Max frames to process (0 = all)")
    parser.add_argument(
        "--max-read-failures",
        type=int,
        default=600,
        help="Max consecutive read failures before stopping (helps with corrupted/HEVC videos)",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=50,
        help="Print progress every N processed frames (0 disables)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else (PROJECT_ROOT / "data")
    video_path = resolve_video_path(args.video, data_dir)

    if video_path is None or not video_path.exists():
        available = []
        if data_dir.exists():
            available = [
                str(p.relative_to(data_dir))
                for p in sorted(data_dir.rglob("*"))
                if p.is_file() and p.suffix.lower() in VIDEO_EXTS
            ]
        print("No video found.")
        print(f"- Expected video inside data folder: {data_dir}")
        print("- You can pass --video as a full path OR a filename inside data")
        if available:
            print("Available videos in data:")
            for v in available[:25]:
                print(f"  - {v}")
        else:
            print("(No videos found under data folder)")
        sys.exit(1)

    if args.output:
        output_dir = Path(args.output)
    else:
        video_slug = slugify(video_path.stem)
        output_dir = CURRENT_DIR / "output_video" / video_slug
    frames_dir = output_dir / "frames"
    plates_dir = output_dir / "plates"
    text_dir = output_dir / "text"
    prov_dir = output_dir / "province"

    for d in [output_dir, frames_dir, plates_dir, text_dir, prov_dir]:
        d.mkdir(parents=True, exist_ok=True)

    metadata_path = output_dir / "metadata.jsonl"
    summary_path = output_dir / "summary.json"

    print(f"Video: {video_path}")
    print(f"Output: {output_dir}")

    processor = ImageProcessor()

    cap = open_video_capture(video_path)
    if not cap.isOpened():
        print(f"Failed to open video: {video_path}")
        print("Tips:")
        print("- If this is an HEVC/H.265 file, your OpenCV build may not support it.")
        print("- Try re-encoding to H.264 (AVC) and retry.")
        print("- Or install an OpenCV build with FFmpeg enabled.")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    duration_sec = (total_frames / fps) if fps else 0

    print(f"Video FPS: {fps}")
    print(f"Video frames: {total_frames}")
    if duration_sec:
        print(f"Video duration (sec): {duration_sec:.2f}")

    processed = 0
    detected = 0
    timing_total = []
    consecutive_failures = 0

    with open(metadata_path, "w", encoding="utf-8") as meta_f:
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                consecutive_failures += 1
                if args.max_read_failures and consecutive_failures > args.max_read_failures:
                    print(f"Stopping: too many read failures ({consecutive_failures}).")
                    break
                # Try to seek forward and continue (helpful for HEVC decode glitches)
                try:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx + 1)
                except Exception:
                    pass
                frame_idx += 1
                continue

            consecutive_failures = 0

            if args.frame_step > 1 and frame_idx % args.frame_step != 0:
                frame_idx += 1
                continue

            if args.max_frames > 0 and processed >= args.max_frames:
                break

            result = process_frame(processor, frame)
            result["frame_index"] = frame_idx
            result["video_path"] = str(video_path)
            result["video_fps"] = fps
            result["video_total_frames"] = total_frames

            timing_total.append(result["timings"].get("total_ms", 0))

            if result.get("detected"):
                detected += 1
                label = f"{result.get('full_plate') or 'plate'} | conf={result.get('plate_conf'):.3f}"
                draw_bbox(frame, result["plate_bbox"], (0, 255, 0), label=label)

                frame_name = f"frame_{frame_idx:06d}.jpg"
                frame_path = frames_dir / frame_name
                cv2.imwrite(str(frame_path), frame)

                plate_crop = safe_crop(frame, result["plate_bbox"])
                if plate_crop is not None:
                    cv2.imwrite(str(plates_dir / frame_name), plate_crop)

                if result.get("text_region"):
                    text_crop = safe_crop(plate_crop, result["text_region"]["bbox"]) if plate_crop is not None else None
                    if text_crop is not None:
                        cv2.imwrite(str(text_dir / frame_name), text_crop)

                if result.get("province_region"):
                    prov_crop = safe_crop(plate_crop, result["province_region"]["bbox"]) if plate_crop is not None else None
                    if prov_crop is not None:
                        cv2.imwrite(str(prov_dir / frame_name), prov_crop)

            meta_f.write(json.dumps(result, ensure_ascii=False) + "\n")
            processed += 1
            frame_idx += 1

            if args.progress_every and processed % args.progress_every == 0:
                pct = (frame_idx / total_frames * 100.0) if total_frames else 0
                print(f"Progress: processed={processed} detected={detected} frame_idx={frame_idx} ({pct:.1f}%)")

    cap.release()

    avg_total = sum(timing_total) / len(timing_total) if timing_total else 0
    summary = {
        "video_path": str(video_path),
        "video_total_frames": total_frames,
        "video_fps": fps,
        "video_duration_sec": duration_sec,
        "processed_frames": processed,
        "detected_frames": detected,
        "frame_step": args.frame_step,
        "avg_total_ms": avg_total,
        "output_dir": str(output_dir),
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("Done.")
    print(f"Processed: {processed} frames")
    print(f"Detected: {detected} frames")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
