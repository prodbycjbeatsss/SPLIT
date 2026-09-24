#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
import zipfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


APP_DIR = Path(__file__).resolve().parent
WORK_DIR = APP_DIR / ".work"
TERMUX_DOWNLOADS = Path.home() / "storage" / "downloads"
OUTPUT_ROOT = TERMUX_DOWNLOADS / "VerticalSplit" if TERMUX_DOWNLOADS.exists() else APP_DIR / "outputs"
HOST = "127.0.0.1"
PORT = 8765
RESOLUTIONS = {
    720: (720, 1280),
    1080: (1080, 1920),
}

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


def safe_name(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", stem)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-._")
    return cleaned or "clip"


def update_job(job_id: str, **changes) -> None:
    with JOBS_LOCK:
        JOBS[job_id].update(changes)


def probe_duration(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(completed.stdout.strip())


def process_video(
    job_id: str,
    input_path: Path,
    output_dir: Path,
    base_name: str,
    segment: float,
    crop: float,
    clip_limit: int | None,
    start_time: float,
    resolution: int,
    clip_names: list[str] | None,
) -> None:
    try:
        duration = probe_duration(input_path)
        if start_time >= duration:
            raise RuntimeError("Start time must be before the end of the video.")
        available_duration = duration - start_time
        requested_duration = segment * clip_limit if clip_limit is not None else None
        if requested_duration is not None and available_duration + 0.1 < requested_duration:
            available_full_clips = int(available_duration // segment)
            raise RuntimeError(
                f"This video is too short for {clip_limit} full {segment:g}-second clips. "
                f"It can produce {available_full_clips} full clips after the selected start time."
            )
        processing_duration = requested_duration or available_duration
        expected_clips = clip_limit or math.ceil(available_duration / segment)
        if clip_names is not None and len(clip_names) != expected_clips:
            raise RuntimeError("The number of clip names does not match the export plan.")
        target_width, target_height = RESOLUTIONS[resolution]
        crop_fraction = crop / 100
        video_filter = (
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
            f"crop={target_width}:{target_height}:(in_w-out_w)*{crop_fraction:.6f}:(in_h-out_h)/2,"
            "setsar=1"
        )
        output_pattern = output_dir / ".split-%d.mp4"

        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-progress", "pipe:1", "-nostats", "-y",
        ]
        if start_time > 0:
            command.extend(["-ss", f"{start_time:g}"])
        command.extend([
            "-i", str(input_path),
            "-map", "0:v:0", "-map", "0:a:0?",
            "-vf", video_filter,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-force_key_frames", f"expr:gte(t,n_forced*{segment:g})",
            "-c:a", "aac", "-b:a", "192k",
        ])
        if requested_duration is not None:
            command.extend(["-t", f"{requested_duration:g}"])
        command.extend([
            "-f", "segment", "-segment_time", f"{segment:g}", "-reset_timestamps", "1",
            "-segment_start_number", "1", "-segment_format", "mp4", str(output_pattern),
        ])

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        update_job(
            job_id,
            status="processing",
            progress=0,
            expectedClips=expected_clips,
            completedClips=0,
            currentClip=1,
        )

        assert process.stdout is not None
        for raw_line in process.stdout:
            key, _, value = raw_line.strip().partition("=")
            if key in {"out_time_us", "out_time_ms"}:
                try:
                    microseconds = float(value)
                    processed_seconds = microseconds / 1_000_000
                    progress = min(98, max(0, processed_seconds / processing_duration * 100))
                    completed_clips = min(expected_clips, int((processed_seconds + 0.05) // segment))
                    current_clip = (
                        min(expected_clips, int(processed_seconds // segment) + 1)
                        if completed_clips < expected_clips
                        else None
                    )
                    update_job(
                        job_id,
                        progress=round(progress, 1),
                        completedClips=completed_clips,
                        currentClip=current_clip,
                    )
                except (ValueError, ZeroDivisionError):
                    pass

        stderr = process.stderr.read() if process.stderr else ""
        return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(stderr.strip() or f"FFmpeg stopped with code {return_code}.")

        clips = sorted(
            output_dir.glob(".split-*.mp4"),
            key=lambda path: int(path.stem.rsplit("-", 1)[1]),
        )
        if not clips:
            raise RuntimeError("No clips were produced.")

        final_clips: list[Path] = []
        for index, clip in enumerate(clips):
            chosen_name = clip_names[index] if clip_names is not None else f"{index + 1}-{base_name}"
            final_path = output_dir / f"{safe_name(chosen_name)}.mp4"
            if final_path in final_clips or final_path.exists():
                raise RuntimeError("Every clip name must be unique.")
            clip.rename(final_path)
            final_clips.append(final_path)
        clips = final_clips

        update_job(
            job_id,
            status="zipping",
            progress=99,
            completedClips=len(clips),
            currentClip=None,
        )
        zip_path = output_dir / f"{base_name}-clips.zip"
        archive_folder = f"{base_name}-clips"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as archive:
            for clip in clips:
                archive.write(clip, arcname=f"{archive_folder}/{clip.name}")

        public_clips = [
            {
                "name": clip.name,
                "url": f"/api/jobs/{job_id}/clips/{index + 1}",
            }
            for index, clip in enumerate(clips)
        ]

        update_job(
            job_id,
            status="complete",
            progress=100,
            clipCount=len(clips),
            completedClips=len(clips),
            currentClip=None,
            zipPath=str(zip_path),
            clipPaths=[str(clip) for clip in clips],
            clips=public_clips,
            archiveFolder=archive_folder,
        )
    except Exception as error:
        update_job(job_id, status="failed", error=str(error), progress=0)
    finally:
        shutil.rmtree(input_path.parent, ignore_errors=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "SPLIT/7.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            data = (APP_DIR / "index.html").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(data)
            return

        clip_match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/clips/(\d+)", parsed.path)
        if clip_match:
            with JOBS_LOCK:
                job = JOBS.get(clip_match.group(1), {}).copy()
            clip_number = int(clip_match.group(2))
            clip_paths = job.get("clipPaths", [])
            if job.get("status") != "complete" or not 1 <= clip_number <= len(clip_paths):
                return self.send_json({"error": "Clip is not ready."}, HTTPStatus.NOT_FOUND)
            clip_path = Path(clip_paths[clip_number - 1])
            if not clip_path.is_file():
                return self.send_json({"error": "Clip was not found."}, HTTPStatus.NOT_FOUND)
            file_size = clip_path.stat().st_size
            start, end = 0, file_size - 1
            range_header = self.headers.get("Range", "")
            status = HTTPStatus.OK
            if range_header:
                match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
                if not match:
                    self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    self.send_header("Content-Range", f"bytes */{file_size}")
                    self.end_headers()
                    return
                start_text, end_text = match.groups()
                if start_text:
                    start = int(start_text)
                    end = min(int(end_text), file_size - 1) if end_text else file_size - 1
                elif end_text:
                    suffix_length = min(int(end_text), file_size)
                    start = file_size - suffix_length
                if start > end or start >= file_size:
                    self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    self.send_header("Content-Range", f"bytes */{file_size}")
                    self.end_headers()
                    return
                status = HTTPStatus.PARTIAL_CONTENT
            length = end - start + 1
            self.send_response(status)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(length))
            self.send_header("Content-Disposition", f'inline; filename="{clip_path.name}"')
            if status == HTTPStatus.PARTIAL_CONTENT:
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.end_headers()
            with clip_path.open("rb") as file:
                file.seek(start)
                remaining = length
                while remaining:
                    chunk = file.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            return

        match = re.fullmatch(r"/api/jobs/([a-f0-9]+)/download", parsed.path)
        if match:
            with JOBS_LOCK:
                job = JOBS.get(match.group(1), {}).copy()
            zip_path = Path(job.get("zipPath", ""))
            if job.get("status") != "complete" or not zip_path.is_file():
                return self.send_json({"error": "Download is not ready."}, HTTPStatus.NOT_FOUND)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f'attachment; filename="{zip_path.name}"')
            self.send_header("Content-Length", str(zip_path.stat().st_size))
            self.end_headers()
            with zip_path.open("rb") as file:
                shutil.copyfileobj(file, self.wfile, length=1024 * 1024)
            return

        match = re.fullmatch(r"/api/jobs/([a-f0-9]+)", parsed.path)
        if match:
            with JOBS_LOCK:
                job = JOBS.get(match.group(1))
                public_job = {
                    key: value for key, value in (job or {}).items()
                    if key not in {"zipPath", "clipPaths"}
                }
            if not job:
                return self.send_json({"error": "Job not found."}, HTTPStatus.NOT_FOUND)
            return self.send_json(public_job)

        self.send_json({"error": "Not found."}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/jobs":
            return self.send_json({"error": "Not found."}, HTTPStatus.NOT_FOUND)

        query = parse_qs(parsed.query)
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            metadata_length = int(self.headers.get("X-Split-Metadata-Length", "0"))
            if metadata_length < 0 or metadata_length > min(content_length, 1_000_000):
                raise ValueError
            metadata = {}
            if metadata_length:
                metadata_bytes = self.rfile.read(metadata_length)
                if len(metadata_bytes) != metadata_length:
                    return self.send_json({"error": "The upload metadata ended unexpectedly."}, HTTPStatus.BAD_REQUEST)
                metadata = json.loads(metadata_bytes.decode("utf-8"))
            filename = str(metadata.get("filename", query.get("filename", ["video.mp4"])[0]))
            requested_name = str(metadata.get("name", query.get("name", [Path(filename).stem])[0]))
            segment = float(metadata.get("segment", query.get("segment", ["15"])[0]))
            crop = float(metadata.get("crop", query.get("crop", ["50"])[0]))
            raw_clip_limit = str(metadata.get("limit", query.get("limit", [""])[0])).strip()
            clip_limit = int(raw_clip_limit) if raw_clip_limit else None
            start_time = float(metadata.get("start", query.get("start", ["0"])[0]))
            resolution = int(metadata.get("resolution", query.get("resolution", ["1080"])[0]))
            raw_clip_names = metadata.get("clipNames")
            clip_names = [safe_name(str(name)) for name in raw_clip_names] if isinstance(raw_clip_names, list) else None
            video_length = content_length - metadata_length
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.send_json({"error": "Invalid processing settings."}, HTTPStatus.BAD_REQUEST)

        if not 0 < segment <= 600:
            return self.send_json({"error": "Segment length must be between 1 and 600 seconds."}, HTTPStatus.BAD_REQUEST)
        if not 0 <= crop <= 100:
            return self.send_json({"error": "Crop position must be between 0 and 100."}, HTTPStatus.BAD_REQUEST)
        if start_time < 0:
            return self.send_json({"error": "Start time cannot be negative."}, HTTPStatus.BAD_REQUEST)
        if resolution not in RESOLUTIONS:
            return self.send_json({"error": "Resolution must be 720p or 1080p."}, HTTPStatus.BAD_REQUEST)
        if clip_limit is not None and not 1 <= clip_limit <= 1000:
            return self.send_json(
                {"error": "Number of clips must be between 1 and 1000."},
                HTTPStatus.BAD_REQUEST,
            )
        if video_length <= 0:
            return self.send_json({"error": "The uploaded video is empty."}, HTTPStatus.BAD_REQUEST)
        if clip_names is not None and len({name.casefold() for name in clip_names}) != len(clip_names):
            return self.send_json({"error": "Every clip name must be unique."}, HTTPStatus.BAD_REQUEST)

        job_id = uuid.uuid4().hex[:12]
        base_name = safe_name(requested_name)
        extension = Path(filename).suffix[:10] or ".mp4"
        upload_dir = WORK_DIR / job_id
        upload_dir.mkdir(parents=True, exist_ok=False)
        input_path = upload_dir / f"input{extension}"

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = OUTPUT_ROOT / f"{base_name}_vertical_clips_{timestamp}_{job_id[:4]}"
        output_dir.mkdir(parents=True, exist_ok=False)

        remaining = video_length
        with input_path.open("wb") as file:
            while remaining:
                chunk = self.rfile.read(min(1024 * 1024, remaining))
                if not chunk:
                    shutil.rmtree(upload_dir, ignore_errors=True)
                    return self.send_json({"error": "The upload ended unexpectedly."}, HTTPStatus.BAD_REQUEST)
                file.write(chunk)
                remaining -= len(chunk)

        with JOBS_LOCK:
            JOBS[job_id] = {
                "jobId": job_id,
                "status": "queued",
                "progress": 0,
                "clipCount": 0,
                "expectedClips": clip_limit or 0,
                "completedClips": 0,
                "currentClip": None,
                "resolution": f"{resolution}p",
                "outputFolder": str(output_dir),
            }

        worker = threading.Thread(
            target=process_video,
            args=(job_id, input_path, output_dir, base_name, segment, crop, clip_limit, start_time, resolution, clip_names),
            daemon=True,
        )
        worker.start()
        self.send_json({"jobId": job_id}, HTTPStatus.ACCEPTED)


def main() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("FFmpeg is required. In Termux, run: pkg install ffmpeg")

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Vertical Split is running at http://{HOST}:{PORT}")
    print(f"Finished clips will be saved in: {OUTPUT_ROOT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Vertical Split.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
