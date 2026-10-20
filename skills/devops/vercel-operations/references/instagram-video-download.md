# Instagram Reel / Video Download via yt-dlp

## Pattern
Download Instagram Reel tanpa login (public reel) menggunakan yt-dlp yang sudah terinstall di VPS.

```bash
yt-dlp --no-playlist -o "/tmp/output_video.%(ext)s" "https://www.instagram.com/reel/<REEL_ID>/"
```

Output biasanya `.mp4`. Cek hasil:
```bash
ls -lh /tmp/output_video.mp4
file /tmp/output_video.mp4
```

## Deploy ke Vercel (static asset)
Setelah download, copy ke `public/videos/` di project Next.js:

```bash
mkdir -p ~/project/public/videos
cp /tmp/output_video.mp4 ~/project/public/videos/nama-video.mp4
```

Vercel akan serve file dari `public/` sebagai static asset di `/videos/nama-video.mp4`.
Verify setelah deploy: `curl -sI https://domain.com/videos/nama-video.mp4 | grep content-type`

## Embed di Next.js (HTML5 video player)
```tsx
<video
  className="w-full aspect-video object-cover"
  controls
  preload="metadata"
>
  <source src="/videos/nama-video.mp4" type="video/mp4" />
  Browser kamu tidak mendukung pemutaran video.
</video>
```

## Notes
- Public reels bisa didownload tanpa credentials
- Private/login-required reels butuh `--cookies-from-browser` atau cookies file
- File size biasanya 2-5MB untuk reel 30-60 detik
- yt-dlp binary ada di `/home/ubuntu/.local/bin/yt-dlp`
