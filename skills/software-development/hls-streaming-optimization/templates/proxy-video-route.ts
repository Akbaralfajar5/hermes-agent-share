import { NextRequest, NextResponse } from "next/server";
import https from "https";
import http from "http";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
// Pin to Singapore — closest to ID users, cuts proxy round-trip ~150ms vs default US.
export const preferredRegion = ["sin1", "hnd1"];

// Reusable keep-alive agents — TLS handshake reuse cuts ~80-200ms on every segment fetch.
// MUST be module-scope, not inside the handler.
const httpsAgent = new https.Agent({ rejectUnauthorized: false, keepAlive: true, maxSockets: 64 });
const httpAgent = new http.Agent({ keepAlive: true, maxSockets: 64 });

// Helper: Fetch stream with redirect handling
function fetchStream(
  url: string,
  headers: Record<string, string>,
  redirectCount = 5
): Promise<{ res: http.IncomingMessage; url: string }> {
  return new Promise((resolve, reject) => {
    if (redirectCount <= 0) return reject(new Error("Too many redirects"));

    const isHttp = url.startsWith("http:");
    const requestModule = isHttp ? http : https;

    const options = {
      headers,
      agent: isHttp ? httpAgent : httpsAgent,
      rejectUnauthorized: false,
      method: "GET",
    };

    const req = requestModule.request(url, options, (res) => {
      if (
        res.statusCode &&
        [301, 302, 303, 307, 308].includes(res.statusCode) &&
        res.headers.location
      ) {
        const newUrl = new URL(res.headers.location, url).href;
        res.resume();
        return resolve(fetchStream(newUrl, headers, redirectCount - 1));
      }
      resolve({ res, url });
    });

    req.on("error", (e) => reject(e));
    req.end();
  });
}

// Helper: Consume stream to buffer (for rewriting text)
function streamToBuffer(stream: http.IncomingMessage): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    stream.on("data", (c) => chunks.push(c));
    stream.on("end", () => resolve(Buffer.concat(chunks)));
    stream.on("error", reject);
  });
}

// Helper: Convert Node stream to Web ReadableStream (for streaming response)
function nodeToWebStream(nodeStream: http.IncomingMessage): ReadableStream {
  let isClosed = false;

  return new ReadableStream({
    start(controller) {
      const safeClose = () => {
        if (!isClosed) {
          isClosed = true;
          try { controller.close(); } catch (_) {}
        }
      };
      const safeError = (err: Error) => {
        if (!isClosed) {
          isClosed = true;
          try { controller.error(err); } catch (_) {}
        }
      };

      nodeStream.on("data", (chunk) => {
        if (!isClosed) {
          try { controller.enqueue(chunk); } catch (_) {
            isClosed = true;
            nodeStream.destroy();
          }
        }
      });

      nodeStream.on("end", safeClose);
      nodeStream.on("error", safeError);
      nodeStream.on("close", safeClose);
    },
    cancel() {
      isClosed = true;
      nodeStream.destroy();
    },
  });
}

export async function GET(req: NextRequest) {
  const urlParams = req.nextUrl.searchParams;
  const url = urlParams.get("url");
  const refererParam = urlParams.get("referer");

  if (!url) {
    return new NextResponse("Missing URL parameter", { status: 400 });
  }

  try {
    const range = req.headers.get("range");
    const headers: Record<string, string> = {
      "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      Accept: "*/*",
      Referer: refererParam || new URL(url).origin + "/",
      // NOTE: Do NOT send Origin header — video CDN returns 403 if Origin doesn't match whitelist
    };

    if (range) headers["Range"] = range;

    const { res: upstreamRes, url: finalUrl } = await fetchStream(url, headers);

    if ((upstreamRes.statusCode || 500) >= 400) {
      return new NextResponse(`Upstream Error: ${upstreamRes.statusMessage}`, {
        status: upstreamRes.statusCode,
      });
    }

    const contentType = (upstreamRes.headers["content-type"] || "").toLowerCase();
    const lowUrl = finalUrl.toLowerCase();

    const isM3u8 =
      contentType.includes("application/vnd.apple.mpegurl") ||
      contentType.includes("application/x-mpegurl") ||
      lowUrl.includes(".m3u8");

    const isVtt =
      contentType.includes("text/vtt") ||
      lowUrl.endsWith(".vtt") ||
      lowUrl.endsWith(".srt") ||
      urlParams.get("type") === "sub";

    // Binary segments — stream directly with aggressive edge cache
    if (
      !isM3u8 &&
      !isVtt &&
      (lowUrl.includes(".mp4") ||
        lowUrl.includes(".ts") ||
        lowUrl.includes(".m4s") ||
        contentType.includes("video/"))
    ) {
      const stream = nodeToWebStream(upstreamRes);
      const responseHeaders = new Headers();
      responseHeaders.set("Content-Type", contentType || "video/mp4");
      responseHeaders.set("Access-Control-Allow-Origin", "*");
      responseHeaders.set("Accept-Ranges", "bytes");
      // Binary segments are immutable content-addressed by URL — safe to cache aggressively.
      responseHeaders.set(
        "Cache-Control",
        "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800, immutable"
      );
      if (upstreamRes.headers["content-length"])
        responseHeaders.set("Content-Length", upstreamRes.headers["content-length"]);
      if (upstreamRes.headers["content-range"])
        responseHeaders.set("Content-Range", upstreamRes.headers["content-range"]);

      return new NextResponse(stream as any, {
        status: upstreamRes.statusCode || 200,
        statusText: upstreamRes.statusMessage,
        headers: responseHeaders,
      });
    }

    // Text content — buffer and rewrite
    const buffer = await streamToBuffer(upstreamRes);
    const decoder = new TextDecoder();
    const firstChunk = decoder.decode(buffer.slice(0, 100));
    const isM3u8Content = firstChunk.includes("#EXTM3U");

    const host = req.headers.get("x-forwarded-host") || req.headers.get("host");
    const proto = req.headers.get("x-forwarded-proto") || "https";
    const origin = `${proto}://${host}`;

    if (isM3u8 || isM3u8Content) {
      const text = decoder.decode(buffer);
      const baseUrl = new URL(finalUrl);
      const subUrl = urlParams.get("sub");
      const isMasterPlaylist = text.includes("#EXT-X-STREAM-INF");

      let rewritten = text
        .split(/\r?\n/)
        .map((line) => {
          const trimmed = line.trim();
          if (!trimmed) return line;

          const createProxyUrl = (targetUrl: string) => {
            let base = `${origin}/api/proxy/video?url=${encodeURIComponent(targetUrl)}`;
            if (refererParam) base += `&referer=${encodeURIComponent(refererParam)}`;
            return base;
          };

          if (trimmed.startsWith("#")) {
            return line.replace(/URI="([^"]+)"/g, (match, uri) => {
              try {
                const absoluteUrl = new URL(uri, baseUrl.href).href;
                return `URI="${createProxyUrl(absoluteUrl)}"`;
              } catch (_) {
                return match;
              }
            });
          }

          try {
            const absoluteUrl = new URL(trimmed, baseUrl.href).href;
            return createProxyUrl(absoluteUrl);
          } catch (_) {
            return line;
          }
        })
        .join("\n");

      if (isMasterPlaylist && subUrl) {
        let proxiedSubUrl = `${origin}/api/proxy/video?url=${encodeURIComponent(subUrl)}`;
        if (refererParam) proxiedSubUrl += `&referer=${encodeURIComponent(refererParam)}`;
        const mediaLine = `#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="Indonesia",DEFAULT=YES,AUTOSELECT=YES,LANGUAGE="id",URI="${proxiedSubUrl}"`;
        rewritten = rewritten.replace("#EXTM3U", "#EXTM3U\n" + mediaLine);
        rewritten = rewritten.replace(/#EXT-X-STREAM-INF:(.*)/g, (match, attrs) => {
          if (attrs.includes("SUBTITLES=")) return match;
          return `#EXT-X-STREAM-INF:${attrs},SUBTITLES="subs"`;
        });
      }

      return new NextResponse(rewritten, {
        status: 200,
        headers: {
          "Content-Type": "application/vnd.apple.mpegurl",
          "Access-Control-Allow-Origin": "*",
          // Manifests rarely change for VOD — short edge cache is safe.
          "Cache-Control": "public, max-age=60, s-maxage=300, stale-while-revalidate=1800",
        },
      });
    }

    // VTT/SRT subtitles
    if (isVtt || lowUrl.endsWith(".srt") || urlParams.get("type") === "sub") {
      let vttContent = decoder.decode(buffer);
      const isSrt = lowUrl.includes(".srt") || urlParams.get("type") === "sub";

      if (isSrt && !firstChunk.includes("WEBVTT")) {
        vttContent = vttContent.replace(/\r\n/g, "\n").replace(/(\d{2}:\d{2}:\d{2}),(\d{3})/g, "$1.$2");
        vttContent = "WEBVTT\n\n" + vttContent;
      }

      vttContent = vttContent.replace(
        /((?:\d{2}:)?\d{2}:\d{2}\.\d{3} --> (?:\d{2}:)?\d{2}:\d{2}\.\d{3})(.*)/g,
        (match, time, rest) => (rest.includes("line:") ? match : `${time} line:75%${rest}`)
      );

      return new NextResponse(vttContent, {
        status: 200,
        headers: {
          "Content-Type": "text/vtt",
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "public, max-age=86400, s-maxage=604800, immutable",
        },
      });
    }

    // Fallback
    return new NextResponse(buffer as any, {
      status: upstreamRes.statusCode || 200,
      headers: {
        "Content-Type": contentType,
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (error) {
    console.error("Proxy error:", error);
    return new NextResponse("Internal Server Error", { status: 500 });
  }
}
