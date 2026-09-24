# SPLIT.v8 Web Architecture

## Status

Prototype decision for the `web-v8` branch. SPLIT.v7 remains the stable Termux release on `main` and at the `v7.0.0` tag.

## Goal

Prove that the user's Android phone can turn one large landscape video into six named 15-second portrait clips without uploading the source or requiring an always-on server.

## Stack

- Vite builds and serves the static web application.
- Vercel hosts the built static assets.
- `@ffmpeg/ffmpeg` runs FFmpeg inside a browser Web Worker.
- The single-thread `@ffmpeg/core` runtime is loaded on the first export.
- WORKERFS mounts the selected browser `File` so the complete source is not copied into FFmpeg's in-memory filesystem.
- `fflate` creates an uncompressed ZIP because MP4 files are already compressed.

## Boundaries

- UI and settings remain in `index.html` for the prototype.
- `src/deps.js` owns third-party browser-processing imports.
- Browser state owns selected files, clip plans, output Blob URLs and progress.
- No backend, database, accounts, analytics, cloud storage or environment variables are used.

## Processing flow

1. The user selects a local video and the browser reads its duration.
2. The app validates the start time, segment length, clip count and unique filenames.
3. FFmpeg loads lazily and mounts the original file through WORKERFS.
4. Clips are cropped and encoded sequentially to limit peak output memory.
5. Each completed clip becomes a local Blob URL for in-app playback.
6. The clips are stored without compression inside one `master-name-clips` folder in a ZIP.
7. The user downloads the ZIP. All transient output disappears when the page is closed.

## Failure handling

- The export button remains disabled during processing.
- Processing errors return the filename controls to an editable state.
- Closing or backgrounding the browser may interrupt processing; the prototype tells users to keep the page open and screen awake.
- Generated Blob URLs are revoked before a new batch to avoid avoidable memory retention.

## Rejected alternatives

- Vercel Functions: unsuitable for large request bodies, long FFmpeg work and multi-file temporary output.
- Cloud video worker: reliable but introduces hosting cost, uploads and privacy work before the phone-first path is tested.
- WebCodecs first: potentially faster, but demuxing, audio handling and MP4 muxing would make the initial proof materially larger.

## Promotion criteria

Do not merge `web-v8` into `main` until a physical Android test completes six 15-second 1080p clips from a 250–300 MB source with audio, correct crop, playable outputs and a downloadable ZIP without the browser closing.
