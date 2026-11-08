import { defineConfig } from '@argo-video/cli';
import { lfm3Engine } from './lfm3-engine.mjs';

export default defineConfig({
  baseURL: 'https://arpansm.github.io/forge-rag-lab/',
  demosDir: 'demos',
  outputDir: 'videos',
  tts: {
    engine: lfm3Engine({ voice: 'male', lang: 'en' }),
    defaultVoice: 'male',
    defaultSpeed: 0.97,
  },
  video: {
    width: 1920,
    height: 1080,
    fps: 30,
    browser: 'chromium',
    browserChannel: 'chrome',
    captureMode: 'jpeg-stitch',
    deviceScaleFactor: 2,
    cursorHighlight: {
      mode: 'click',
      color: '#d65a31',
      radius: 26,
      opacity: 0.85,
    },
  },
  export: {
    preset: 'slow',
    crf: 18,
    sharpen: true,
    audio: { loudnorm: true },
    thumbnailPath: 'videos/rag-lab-walkthrough-poster.png',
  },
  overlays: {
    autoBackground: true,
  },
});
