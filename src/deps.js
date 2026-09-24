import { FFmpeg } from '@ffmpeg/ffmpeg';
import { toBlobURL } from '@ffmpeg/util';
import { zipSync } from 'fflate';

try {
  window.SPLIT_WEB_DEPS = { FFmpeg, toBlobURL, zipSync };
  window.dispatchEvent(new Event('split-deps-ready'));
} catch (error) {
  window.SPLIT_WEB_DEPS_ERROR = error;
  window.dispatchEvent(new Event('split-deps-error'));
}
