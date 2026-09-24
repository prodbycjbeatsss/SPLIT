# SPLIT.v8 Web Prototype

Browser-only experiment for turning one landscape video into named, full-screen 9:16 clips. The source video remains on the device and is processed with FFmpeg WebAssembly; there is no upload, account or application server.

SPLIT.v7 remains the stable Termux/Python release on the `main` branch and `v7.0.0` tag. Develop this edition only on `web-v8` until its Android stress test passes.

## Prototype scope

- Preview the source inside a movable 9:16 crop.
- Default to six 15-second clips from `0:00` at 1080p.
- Preserve source audio when present.
- Rename every clip before export.
- Process clips sequentially in the browser.
- View finished clips without uploading them.
- Download one ZIP containing a `master-name-clips` folder.
- Preserve the v7 paper-and-terracotta interface and saved light/dark setting.

## Known limitations

- The FFmpeg browser engine is downloaded on the first export and is roughly 31 MB before browser caching.
- Browser processing is slower than native Termux FFmpeg.
- Keep the page open and the screen awake while exporting.
- Large-file reliability must be proven on the target Android phone before this branch can replace v7.
- Generated clips are temporary until the ZIP is downloaded.

## Run for development

Node.js 20.19 or newer is recommended for the current Vite toolchain.

```bash
npm install
npm run dev
```

Open the network URL shown by Vite on the Android device.

## Build

```bash
npm run build
npm run preview
```

The production output is created in `dist/`.

## Deploy to Vercel

Import the GitHub repository into Vercel and select the `web-v8` branch. Vercel should detect Vite and use:

```text
Build command: npm run build
Output directory: dist
```

No environment variables or server functions are required for the prototype.

## Required physical-device test

Before merging, test one 250–300 MB landscape video using:

- six clips;
- 15 seconds each;
- 1080p;
- retained audio;
- non-centred crop position;
- individually edited filenames;
- in-app playback;
- final ZIP extraction.

See `docs/ARCHITECTURE.md` for the decision record and promotion criteria.
