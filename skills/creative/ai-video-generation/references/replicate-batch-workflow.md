# Replicate Batch Video Generation Workflow

## Proven Pattern: Multi-Scene Narrative Video (13 scenes via minimax/video-01)

### Key Learnings

1. **Model choice:** `minimax/video-01` (Hailuo) on Replicate is best for cinematic photorealistic scenes with humans
2. **Auth:** `Authorization: Bearer r8_...` — NOT `Token`
3. **Endpoint:** `POST /v1/models/minimax/video-01/predictions` (no version ID needed)
4. **Rate limit (free):** 1 burst, 6/min → must sleep 12s between submissions
5. **Generation time:** ~3-5 minutes per 6-second clip
6. **Credit usage:** 11 clips exhausted free credits (~$5-6 worth)
7. **Output:** Direct MP4 URL in `output` field when status=succeeded

### Workflow Steps

```
1. Verify API key: GET /v1/account
2. Submit predictions one-by-one with 12s delay
3. Save prediction IDs to JSON file for tracking
4. Poll all predictions every 15s until all succeed/fail
5. Download MP4s from output URLs
6. Handle 429 (rate limit) → wait retry_after seconds
7. Handle 402 (insufficient credit) → stop, notify user to top up
```

### Input Schema for minimax/video-01

```json
{
  "input": {
    "prompt": "string (required)",
    "prompt_optimizer": true,
    "first_frame_image": "URL (optional, for image-to-video)",
    "subject_reference": "URL (optional, character reference image)"
  }
}
```

### Response Lifecycle

```
starting → processing → succeeded (output = MP4 URL)
                      → failed (error = reason string)
```

### Cost Estimate (May 2025)

- minimax/video-01: ~$0.50 per 6s clip
- 13-scene short film: ~$6.50 total
- Free tier gives roughly 10-11 clips before exhaustion

### Replicate Video Model Landscape (Mid-2025)

Models available on Replicate, ranked by quality (from replicate.com/collections/text-to-video):

| Rank | Model ID | Description | Best For |
|------|----------|-------------|----------|
| 🥇 | `runway/gen-4-turbo` | Runway Gen-4.5 — #1 on Artificial Analysis benchmark | Cinematic realism, physics accuracy |
| 🥈 | `google/veo-3` / `google/veo-3-fast` | Google Veo 3.1 — native audio generation | High quality + audio, fast turnaround |
| 🥉 | `kwaivgi/kling-v3-omni-video` | Kling Video 3.0 Omni — multi-shot (6 scenes), lip-sync, audio | Short narratives, ads, product demos |
| 4 | `bytedance/seedance-2.0` | Seedance 2.0 — 9 ref images, 3 video clips, 3 audio files | Multimodal reference, character consistency |
| 5 | `minimax/video-01` | Hailuo 2.3 (MiniMax) — standard and pro quality tiers | Balanced cost/quality, human motion |
| 6 | `pixverse/pixverse-v6` | PixVerse v5.6/v6 — multi-shot, camera control, audio | Cost-effective, social content |
| 7 | `wavespeedai/wan-2.1-t2v-480p` | Wan 2.7 T2V — 27B MoE, open source | Open source, competitive quality |
| 8 | `prunaai/p-video` | PrunaAI — draft mode 4x faster, T2V+I2V+A2V | Fast iteration, previews |
| 9 | `xai/grok-imagine-video` | Grok Imagine Video — ~30s generation, multi aspect ratio | TikTok/Reels/Shorts |

**Note:** `minimax/video-01` (what we used) is now mid-tier. For significantly better results, upgrade to Kling 3.0 Omni or Veo 3.1. Kling 3.0's multi-shot mode can generate 6 connected scenes in one call — ideal for narrative projects.

### Pitfalls

- Free accounts cannot submit in parallel (burst=1). Sequential with delay is mandatory.
- No aspect ratio control for text-to-video — always outputs 16:9
- `prompt_optimizer: true` significantly improves output quality (adds cinematic details)
- Predictions stay available for download for ~24h after completion
- If token returns 401 on first try, it may be newly created — wait 2-3 minutes
- **Model 403 errors when credit exhausted.** Once credits run out, even `GET /v1/models/{id}` returns 403 (not just prediction creation). This makes it impossible to browse model info without credits.
