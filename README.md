# SPLIT.v7

A local, mobile-friendly interface for turning one landscape video into separate full-screen 9:16 clips. Processing happens on your Android device through Termux and FFmpeg.

The v7 interface adds the compact play-panel logo, the `SPL/T.v7` wordmark and a paper-and-terracotta colour system. It retains saved light and dark modes, a GitHub link and a minimal local-first footer.

## What it does

- Previews the video inside a 9:16 canvas.
- Scales proportionally until the complete canvas is filled.
- Crops the overflowing sides without stretching or adding borders.
- Lets you move the crop horizontally to keep the important subject visible.
- Starts at `0:00`, exports six 15-second clips and renders at 1080p by default.
- Lets you choose a start time, clip length, number of clips and either 1080p or 720p output.
- Remembers the start time, resolution, clip count, segment length and crop position on the device.
- Always retains the source audio when an audio track is present.
- Lets you set one master name, then rename every planned clip independently before export.
- Shows a pre-export overview containing each editable filename, source timestamp range and live status.
- Shows batch progress with changing messages while the video uploads, crops, exports and packages.
- Lets you play every completed clip inside the app.
- Saves every clip to `Download/VerticalSplit` and creates a ZIP whose contents sit inside a tidy `master-name-clips` folder.

## One-time Termux setup

```bash
termux-setup-storage
pkg update
pkg install python ffmpeg
```

When Android asks, allow Termux to access your files.

## Start the interface

Move the `vertical-split-gui` folder somewhere Termux can access, then run:

```bash
cd /path/to/vertical-split-gui
bash start.sh
```

Open this address in your Android browser if it does not open automatically:

```text
http://127.0.0.1:8765
```

Keep Termux running while a video is being processed. Press `Ctrl+C` in Termux when you want to stop the local server.

## Output

Each job creates a new folder so existing clips are never overwritten:

```text
Download/VerticalSplit/video_vertical_clips_DATE_TIME_ID/
```

The folder contains the separate MP4 clips and a ZIP file containing the same batch. When the ZIP is extracted, it creates one `master-name-clips` folder rather than placing loose videos directly in Downloads. This keeps file browsing tidier; gallery apps may still group media according to their own rules.

## Important crop behaviour

Filling a 9:16 canvas with a 16:9 video removes a large amount from the left and right sides. Use the horizontal crop slider to position the subject before exporting.
