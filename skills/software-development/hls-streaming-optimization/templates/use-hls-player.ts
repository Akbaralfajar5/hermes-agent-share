"use client";

import { useEffect, useRef } from "react";
import Hls from "hls.js";

/**
 * Tuned HLS.js config for short drama playback — optimized for fast start.
 *
 * Key decisions:
 * - startLevel: 0 — start at lowest quality immediately, no ABR probe delay.
 *   ABR will upgrade quality after a few segments once bandwidth is known.
 *   This cuts 1-2s of "ABR thinking time" before first frame appears.
 * - maxBufferLength: 8 — only buffer 8s before starting playback. Drama
 *   episodes are 2-5 min; 8s is enough to start fast without hogging memory.
 * - maxMaxBufferLength: 60 — allow up to 60s buffer once playing (smooth seek).
 * - abrEwmaDefaultEstimate: 500_000 (500 Kbps) — conservative seed so ABR
 *   starts low and upgrades, rather than starting high and stalling.
 * - lowLatencyMode: false — VOD content, not live stream.
 * - backBufferLength: 15 — keep 15s for seek-back without bloat.
 * - Timeouts tuned down: proxy is on same Vercel infra, no need for 25s waits.
 *
 * PITFALL: Do NOT set startLevel: -1 (the HLS.js default). It forces ABR to
 * probe all quality levels before fetching the first segment — adds 1-3s of
 * dead time before the video starts. startLevel: 0 is always faster for VOD.
 *
 * PITFALL: Do NOT set maxBufferLength: 30 (the HLS.js default). On proxied
 * routes, HLS.js will try to pre-buffer 30s before starting play — that's
 * 3-5s of dead time. Use 8 for fast start, let maxMaxBufferLength handle depth.
 */
export const DEFAULT_HLS_CONFIG: Partial<ConstructorParameters<typeof Hls>[0]> = {
  enableWorker: true,
  lowLatencyMode: false,
  // Buffer — start fast, grow as needed
  maxBufferLength: 8,
  maxMaxBufferLength: 60,
  backBufferLength: 15,
  maxBufferSize: 30 * 1000 * 1000, // 30 MB
  // ABR / quality — start low, upgrade fast
  capLevelToPlayerSize: true,
  startLevel: 0,                        // lowest quality first → instant start
  abrEwmaDefaultEstimate: 500_000,      // 500 Kbps conservative seed
  abrBandWidthFactor: 0.9,              // use 90% of measured bandwidth (safety margin)
  abrBandWidthUpFactor: 0.7,            // upgrade quality only when clearly stable
  // Retry policy — reasonable for proxied segments on Vercel
  manifestLoadingTimeOut: 10000,
  manifestLoadingMaxRetry: 3,
  manifestLoadingRetryDelay: 500,
  manifestLoadingMaxRetryTimeout: 4000,
  levelLoadingTimeOut: 10000,
  levelLoadingMaxRetry: 3,
  levelLoadingRetryDelay: 500,
  fragLoadingTimeOut: 15000,
  fragLoadingMaxRetry: 4,
  fragLoadingRetryDelay: 500,
  fragLoadingMaxRetryTimeout: 4000,
  // CORS
  xhrSetup: function (xhr) {
    xhr.withCredentials = false;
  },
};

export interface UseHlsPlayerOptions {
  /** Optional override config merged into DEFAULT_HLS_CONFIG. */
  config?: Partial<ConstructorParameters<typeof Hls>[0]>;
  /** Called once the manifest is parsed and playback can start. */
  onReady?: () => void;
  /** Called on fatal error after recovery attempts have been exhausted. */
  onFatal?: (data: unknown) => void;
  /** When true, don't auto-attempt video.play() on manifest parsed. */
  noAutoPlay?: boolean;
}

/**
 * Attach an HLS source (or native MP4/HLS) to a `<video>` element with sane
 * defaults, autoplay, and multi-stage error recovery (network → media → reload).
 *
 * PITFALL: Do NOT attach raw Hls.Events listeners outside this hook.
 * If you need to react to manifest parse or quality switch (e.g. subtitle
 * injection), use video element events (loadeddata, canplay, playing) + a
 * short polling interval instead. Raw Hls.Events listeners attached outside
 * the hook leak and fire after the instance is destroyed.
 */
export function useHlsPlayer(
  videoRef: React.RefObject<HTMLVideoElement | null>,
  src: string | undefined | null,
  options: UseHlsPlayerOptions = {}
) {
  const hlsRef = useRef<Hls | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    // Cleanup previous instance
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    const isHls = src.includes(".m3u8") || src.includes("application/x-mpegURL");
    const merged = { ...DEFAULT_HLS_CONFIG, ...(options.config || {}) };

    let recoveryAttempts = 0;
    const MAX_RECOVERY = 3;

    const attemptPlay = () => {
      const p = video.play();
      if (p) p.catch(() => { /* autoplay blocked — user gesture needed */ });
    };

    if (isHls && Hls.isSupported()) {
      const hls = new Hls(merged);
      hlsRef.current = hls;
      hls.loadSource(src);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        options.onReady?.();
        if (!options.noAutoPlay) attemptPlay();
      });

      hls.on(Hls.Events.ERROR, (_e, data) => {
        if (!data.fatal) return;

        if (recoveryAttempts >= MAX_RECOVERY) {
          console.error("[HLS] giving up after max recovery attempts", data);
          options.onFatal?.(data);
          hls.destroy();
          return;
        }

        recoveryAttempts += 1;
        switch (data.type) {
          case Hls.ErrorTypes.NETWORK_ERROR:
            console.warn("[HLS] network error — retrying load", data.details);
            hls.startLoad();
            break;
          case Hls.ErrorTypes.MEDIA_ERROR:
            console.warn("[HLS] media error — recovering", data.details);
            hls.recoverMediaError();
            break;
          default:
            console.error("[HLS] unrecoverable fatal", data);
            options.onFatal?.(data);
            hls.destroy();
            break;
        }
      });
    } else {
      // Native playback path — Safari HLS or plain MP4
      video.src = src;
      const onLoadedMeta = () => {
        options.onReady?.();
        if (!options.noAutoPlay) attemptPlay();
      };
      video.addEventListener("loadedmetadata", onLoadedMeta, { once: true });
      video.load();
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
    // We intentionally omit options from deps — callers should provide stable refs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src, videoRef]);

  return hlsRef;
}
