---
name: ai-video-generation
description: AI video generation patterns using Sora, Runway, Pika, and other AI video tools. Use when generating videos from text prompts, image-to-video conversion, AI video editing, or integrating AI video APIs.
---

# AI Video Generation Patterns

Best practices for generating videos with AI tools.

## Platform Overview

| Platform | Type | Strengths | Free Tier |
|----------|------|-----------|-----------| 
| Runway Gen-4.5 | Text/Image-to-Video | #1 benchmark, realistic physics, hair/fabric coherence | Free forever plan |
| Google Veo 3.1 | Text-to-Video | Native audio, high quality, Veo 3.1 Fast/Lite variants | Via Replicate credits |
| Kling Video 3.0 | Text/Image-to-Video | Multi-shot (6 scenes), lip-sync dialogue, 15s clips | 66 credits/day |
| Seedance 2.0 (ByteDance) | Multimodal-to-Video | 9 ref images + 3 videos + 3 audio, motion transfer | Via Replicate credits |
| Hailuo 2.3 / MiniMax | Text/Image-to-Video | Best human motion, standard/pro quality tiers | Free daily credits |
| PixVerse v6 | Text/Image-to-Video | Multi-shot, camera control, synchronized audio | **90 credits/day** |
| Wan 2.7 T2V | Text-to-Video | Open source, 27B MoE, competitive quality | Self-hosted or Replicate |
| Grok Imagine Video (xAI) | Text-to-Video | ~30s generation, multi aspect ratio (9:16, 16:9, 1:1) | Via Replicate credits |
| Vidu Q3 Pro | Start/End-to-Video | First+last frame control, 16s@1080p with audio | Via Replicate credits |
| PrunaAI p-video | T2V/I2V/A2V | Draft mode 4x faster, 1080p@48fps | Via Replicate credits |
| Stable Video Diffusion | Image-to-Video | Open source | Self-hosted |

### Free Tier Strategy for Narrative Projects

For multi-scene storytelling (short films, TikTok series), use multiple platforms in parallel to maximize free credits:

1. **PixVerse** (app.pixverse.ai) — 90 daily credits, best for narrative with multi-shot and panel features
2. **Kling AI** (klingai.com) — 66 daily credits, best facial realism and consistency
3. **Hailuo AI** (hailuoai.video) — free daily credits, best natural human motion
4. **Vidu AI** (vidu.com) — multi-reference consistency keeps characters looking the same across scenes

**Workflow:** Generate consistent character reference images first (via AI image gen), then use image-to-video on each platform. Spread scenes across platforms: 3-4 scenes/day across 2-3 platforms = full short film in 3-5 days.

**No API keys needed** for web-based use on any of these — just email registration.

## Runway API Integration

```python
import requests
from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class GenerationRequest:
    prompt: str
    image_url: Optional[str] = None
    duration: int = 4  # seconds
    aspect_ratio: str = "16:9"
    motion_strength: int = 5  # 1-10

@dataclass
class GenerationResult:
    id: str
    status: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class RunwayClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.runwayml.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate_video(self, request: GenerationRequest) -> GenerationResult:
        """Generate video from text or image prompt."""
        payload = {
            "model": "gen3a_turbo",
            "prompt": request.prompt,
            "duration": request.duration,
            "aspectRatio": request.aspect_ratio
        }

        if request.image_url:
            payload["imageUrl"] = request.image_url
            payload["mode"] = "image-to-video"
        else:
            payload["mode"] = "text-to-video"

        response = requests.post(
            f"{self.base_url}/generations",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()

        return GenerationResult(
            id=data["id"],
            status=data["status"]
        )

    def get_generation(self, generation_id: str) -> GenerationResult:
        """Check status of generation."""
        response = requests.get(
            f"{self.base_url}/generations/{generation_id}",
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()

        return GenerationResult(
            id=data["id"],
            status=data["status"],
            video_url=data.get("output", {}).get("videoUrl"),
            thumbnail_url=data.get("output", {}).get("thumbnailUrl")
        )

    def wait_for_completion(
        self,
        generation_id: str,
        poll_interval: float = 5.0,
        timeout: float = 300.0
    ) -> GenerationResult:
        """Poll until generation completes."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.get_generation(generation_id)

            if result.status == "SUCCEEDED":
                return result
            elif result.status == "FAILED":
                raise Exception(f"Generation failed: {generation_id}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Generation timed out: {generation_id}")

    def generate_and_wait(self, request: GenerationRequest) -> GenerationResult:
        """Generate video and wait for completion."""
        initial = self.generate_video(request)
        return self.wait_for_completion(initial.id)
```

## Pika Labs Integration

```python
class PikaClient:
    """Pika Labs API client (when API available)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pika.art/v1"

    def text_to_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "realistic",  # realistic, anime, 3d-animation
        duration: int = 3,
        fps: int = 24
    ) -> dict:
        """Generate video from text prompt."""
        response = requests.post(
            f"{self.base_url}/generate",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "prompt": prompt,
                "negativePrompt": negative_prompt,
                "style": style,
                "duration": duration,
                "fps": fps
            }
        )
        return response.json()

    def image_to_video(
        self,
        image_url: str,
        motion_prompt: str,
        motion_strength: float = 1.0
    ) -> dict:
        """Animate an image."""
        response = requests.post(
            f"{self.base_url}/animate",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "imageUrl": image_url,
                "motionPrompt": motion_prompt,
                "motionStrength": motion_strength
            }
        )
        return response.json()
```

## Stable Video Diffusion (Local)

```python
import torch
from diffusers import StableVideoDiffusionPipeline
from PIL import Image

class StableVideoGenerator:
    def __init__(self, model_id: str = "stabilityai/stable-video-diffusion-img2vid-xt"):
        self.pipe = StableVideoDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            variant="fp16"
        )
        self.pipe.to("cuda")

    def generate(
        self,
        image_path: str,
        num_frames: int = 25,
        fps: int = 7,
        motion_bucket_id: int = 127,
        noise_aug_strength: float = 0.02,
        decode_chunk_size: int = 8
    ) -> list:
        """Generate video from image."""
        image = Image.open(image_path).resize((1024, 576))

        frames = self.pipe(
            image,
            num_frames=num_frames,
            motion_bucket_id=motion_bucket_id,
            noise_aug_strength=noise_aug_strength,
            decode_chunk_size=decode_chunk_size
        ).frames[0]

        return frames

    def save_video(self, frames: list, output_path: str, fps: int = 7):
        """Save frames as video."""
        from diffusers.utils import export_to_video
        export_to_video(frames, output_path, fps=fps)
```

## Prompt Engineering for Video

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class VideoPrompt:
    subject: str
    action: str
    setting: str
    style: Optional[str] = None
    camera: Optional[str] = None
    lighting: Optional[str] = None
    mood: Optional[str] = None

    def to_prompt(self) -> str:
        """Build optimized prompt string."""
        parts = [
            f"{self.subject} {self.action}",
            f"in {self.setting}" if self.setting else "",
        ]

        modifiers = []
        if self.style:
            modifiers.append(self.style)
        if self.camera:
            modifiers.append(f"{self.camera} shot")
        if self.lighting:
            modifiers.append(f"{self.lighting} lighting")
        if self.mood:
            modifiers.append(f"{self.mood} mood")

        if modifiers:
            parts.append(", ".join(modifiers))

        return ", ".join(filter(None, parts))


class PromptLibrary:
    """Common prompt patterns for video generation."""

    CAMERA_MOVEMENTS = [
        "slow zoom in",
        "slow zoom out",
        "dolly shot",
        "tracking shot",
        "pan left to right",
        "crane shot",
        "steady cam",
        "handheld",
        "aerial drone shot",
        "first person POV"
    ]

    STYLES = [
        "cinematic",
        "photorealistic",
        "anime style",
        "3D animation",
        "stop motion",
        "vintage film grain",
        "documentary style",
        "music video aesthetic",
        "noir",
        "cyberpunk"
    ]

    LIGHTING = [
        "golden hour",
        "blue hour",
        "dramatic shadows",
        "soft diffused",
        "neon lights",
        "natural sunlight",
        "studio lighting",
        "candlelight",
        "moonlight",
        "backlit silhouette"
    ]

    @staticmethod
    def build_cinematic_prompt(
        subject: str,
        action: str,
        setting: str
    ) -> str:
        """Build a cinematic video prompt."""
        prompt = VideoPrompt(
            subject=subject,
            action=action,
            setting=setting,
            style="cinematic, high production value",
            camera="slow tracking",
            lighting="dramatic",
            mood="epic"
        )
        return prompt.to_prompt()

    @staticmethod
    def build_product_prompt(product: str, features: List[str]) -> str:
        """Build product showcase prompt."""
        return f"{product} rotating on clean white background, {', '.join(features)}, professional product photography, soft studio lighting, 4K quality"

    @staticmethod
    def build_nature_prompt(scene: str, atmosphere: str) -> str:
        """Build nature/landscape prompt."""
        return f"beautiful {scene}, {atmosphere} atmosphere, cinematic wide shot, golden hour lighting, National Geographic style, 8K quality"
```

## Batch Generation

```python
import asyncio
from dataclasses import dataclass
from typing import List
from enum import Enum

class GenerationStatus(Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BatchJob:
    id: str
    prompt: str
    status: GenerationStatus = GenerationStatus.PENDING
    result_url: Optional[str] = None
    error: Optional[str] = None


class BatchGenerator:
    def __init__(self, runway_client: RunwayClient):
        self.client = runway_client
        self.jobs: List[BatchJob] = []

    def add_job(self, prompt: str) -> str:
        """Add generation job to batch."""
        import uuid
        job_id = str(uuid.uuid4())
        job = BatchJob(id=job_id, prompt=prompt)
        self.jobs.append(job)
        return job_id

    async def process_job(self, job: BatchJob, semaphore: asyncio.Semaphore):
        """Process single job with concurrency control."""
        async with semaphore:
            job.status = GenerationStatus.GENERATING
            try:
                request = GenerationRequest(prompt=job.prompt)
                result = await asyncio.to_thread(
                    self.client.generate_and_wait, request
                )
                job.status = GenerationStatus.COMPLETED
                job.result_url = result.video_url
            except Exception as e:
                job.status = GenerationStatus.FAILED
                job.error = str(e)

    async def process_all(self, max_concurrent: int = 3):
        """Process all jobs with concurrency limit."""
        semaphore = asyncio.Semaphore(max_concurrent)

        tasks = [
            self.process_job(job, semaphore)
            for job in self.jobs
        ]

        await asyncio.gather(*tasks)

    def get_results(self) -> dict:
        """Get summary of all jobs."""
        return {
            "total": len(self.jobs),
            "completed": sum(1 for j in self.jobs if j.status == GenerationStatus.COMPLETED),
            "failed": sum(1 for j in self.jobs if j.status == GenerationStatus.FAILED),
            "jobs": [
                {
                    "id": j.id,
                    "prompt": j.prompt[:50] + "...",
                    "status": j.status.value,
                    "url": j.result_url,
                    "error": j.error
                }
                for j in self.jobs
            ]
        }
```

## Video Enhancement

```python
class VideoEnhancer:
    """Post-process AI-generated videos."""

    def __init__(self):
        pass

    def upscale(
        self,
        input_path: str,
        output_path: str,
        scale: int = 2
    ):
        """Upscale video using AI."""
        import subprocess

        # Using Real-ESRGAN for upscaling
        subprocess.run([
            "realesrgan-ncnn-vulkan",
            "-i", input_path,
            "-o", output_path,
            "-s", str(scale),
            "-n", "realesrgan-x4plus"
        ])

    def interpolate_frames(
        self,
        input_path: str,
        output_path: str,
        target_fps: int = 60
    ):
        """Interpolate frames for smoother video."""
        import subprocess

        # Using RIFE for frame interpolation
        subprocess.run([
            "ffmpeg",
            "-i", input_path,
            "-vf", f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            output_path
        ])

    def remove_artifacts(
        self,
        input_path: str,
        output_path: str
    ):
        """Remove common AI artifacts."""
        import subprocess

        subprocess.run([
            "ffmpeg",
            "-i", input_path,
            "-vf", "unsharp=5:5:0.8:3:3:0.4,hqdn3d=3:3:6:6",
            "-c:v", "libx264",
            "-crf", "18",
            output_path
        ])

    def add_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ):
        """Add audio track to silent AI video."""
        import subprocess

        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ])
```

## Storyboard to Video

```python
from dataclasses import dataclass
from typing import List

@dataclass
class StoryboardScene:
    description: str
    duration: int  # seconds
    transition: str = "cut"  # cut, fade, dissolve
    audio: Optional[str] = None

@dataclass
class Storyboard:
    title: str
    scenes: List[StoryboardScene]


class StoryboardRenderer:
    def __init__(self, video_client: RunwayClient):
        self.client = video_client

    async def render_storyboard(self, storyboard: Storyboard) -> List[str]:
        """Generate video for each scene."""
        video_paths = []

        for i, scene in enumerate(storyboard.scenes):
            print(f"Generating scene {i + 1}/{len(storyboard.scenes)}")

            request = GenerationRequest(
                prompt=scene.description,
                duration=scene.duration
            )

            result = self.client.generate_and_wait(request)

            # Download video
            output_path = f"scene_{i:03d}.mp4"
            self._download_video(result.video_url, output_path)
            video_paths.append(output_path)

        return video_paths

    def _download_video(self, url: str, output_path: str):
        """Download video from URL."""
        import requests

        response = requests.get(url, stream=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def concatenate_scenes(
        self,
        video_paths: List[str],
        output_path: str
    ):
        """Combine scenes into final video."""
        import subprocess

        # Create file list
        with open('scenes.txt', 'w') as f:
            for path in video_paths:
                f.write(f"file '{path}'\n")

        subprocess.run([
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", "scenes.txt",
            "-c", "copy",
            output_path
        ])
```

## Unified API Gateway: fal.ai (Recommended)

fal.ai provides a single API to access ALL major video models. **$1 free credit on signup** = ~15-20 video clips.

```python
# pip install fal-client
import os, fal_client
os.environ["FAL_KEY"] = "YOUR_KEY"  # https://fal.ai/dashboard/keys

# Hailuo/MiniMax (best human motion)
result = fal_client.subscribe("fal-ai/minimax/hailuo-02/standard/text-to-video", arguments={
    "prompt": "A woman walking through a garden, cinematic, photorealistic",
})
print(result['video']['url'])

# PixVerse V6 (cheapest, 90 free credits/day on web)
result = fal_client.subscribe("fal-ai/pixverse/v6/text-to-video", arguments={
    "prompt": "...", "quality": "360p", "duration": 5,
})

# Kling v3 (best realistic faces)
result = fal_client.subscribe("fal-ai/kling-video/v3/standard/text-to-video", arguments={
    "prompt": "...", "duration": "5", "aspect_ratio": "16:9",
})
```

### fal.ai Model Endpoints & Pricing

| Model | Endpoint | Cost/sec |
|-------|----------|----------|
| Wan 2.5 T2V | `fal-ai/wan-25-preview/text-to-video` | $0.05-0.15 |
| Hailuo 02 T2V | `fal-ai/minimax/hailuo-02/standard/text-to-video` | $0.045 |
| PixVerse V6 T2V | `fal-ai/pixverse/v6/text-to-video` | $0.025@360p |
| Kling v3 Std T2V | `fal-ai/kling-video/v3/standard/text-to-video` | $0.084 |
| Vidu Q3 I2V | `fal-ai/vidu/q3/image-to-video` | $0.07@360p |
| Luma Ray 2 I2V | `fal-ai/luma-dream-machine/ray-2/image-to-video` | varies |
| Seedance 2.0 T2V | `bytedance/seedance-2.0/text-to-video` | $0.30 |

## Free Tier Comparison (Web-Based, No API Key)

| Platform | Free Credits/Day | Clip Duration | Best For |
|----------|-----------------|---------------|----------|
| PixVerse (app.pixverse.ai) | 90/day | 4-8s | Multi-shot storytelling, cheapest |
| Kling AI (klingai.com) | 66/day | 5s | Best realistic human faces |
| Hailuo AI (hailuoai.video) | Free daily | 5-6s | Best human motion realism |
| Vidu (vidu.com) | "Unlimited" | varies | Character consistency across scenes |
| Runway (runwayml.com) | Free plan | varies | Characters feature for identity |

## Other API Options

### Luma AI (Direct SDK)
```python
# pip install lumaai
from lumaai import LumaAI
client = LumaAI(auth_token="luma-xxxx")  # https://lumalabs.ai/dream-machine/api/keys
generation = client.generations.video.create(
    prompt="...", model="ray-2", resolution="720p", duration="5s",
)
```

### Replicate (Pay-per-use, many video models)

Replicate hosts many video generation models (Wan 2.1, Minimax, LTX Video, etc.).

```python
# pip install replicate
import os
os.environ["REPLICATE_API_TOKEN"] = "r8_..."  # from replicate.com/account/api-tokens
import replicate

# Text-to-video (Wan 2.1)
output = replicate.run("wavespeedai/wan-2.1-t2v-480p", input={
    "prompt": "...", "num_frames": 81,
})

# Minimax (Hailuo) via Replicate
output = replicate.run("minimax/video-01", input={
    "prompt": "...", "prompt_optimizer": True,
})
```

**REST API (curl):**
```bash
# Auth header MUST be "Authorization: Bearer r8_..." (not "Token")
# Use model endpoint (no version ID needed):
curl -s -X POST https://api.replicate.com/v1/models/minimax/video-01/predictions \
  -H "Authorization: Bearer r8_YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "...", "prompt_optimizer": true}}'

# Or with explicit version:
curl -s -X POST https://api.replicate.com/v1/predictions \
  -H "Authorization: Bearer r8_YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "MODEL_VERSION_ID", "input": {"prompt": "..."}}'

# Check status (output field has video URL when succeeded)
curl -s https://api.replicate.com/v1/predictions/PREDICTION_ID \
  -H "Authorization: Bearer r8_YOUR_TOKEN"

# Verify token works
curl -s -H "Authorization: Bearer r8_YOUR_TOKEN" https://api.replicate.com/v1/account
```

**Batch generation with rate limiting (Python):**
```python
import json, urllib.request, time

API_KEY = "r8_..."
url = "https://api.replicate.com/v1/models/minimax/video-01/predictions"

scenes = {"scene_01": "prompt...", "scene_02": "prompt..."}
predictions = {}

for name, prompt in scenes.items():
    time.sleep(12)  # REQUIRED: 10-12s between requests for free accounts
    data = json.dumps({"input": {"prompt": prompt, "prompt_optimizer": True}}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        predictions[name] = result["id"]
        print(f"✅ {name}: {result['id']}")

# Poll for results (minimax/video-01 takes ~3-5 min per clip)
for name, pred_id in predictions.items():
    while True:
        req = urllib.request.Request(
            f"https://api.replicate.com/v1/predictions/{pred_id}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        with urllib.request.urlopen(req) as resp:
            r = json.loads(resp.read())
        if r["status"] == "succeeded":
            print(f"✅ {name}: {r['output']}")
            break
        elif r["status"] == "failed":
            print(f"❌ {name}: {r.get('error')}")
            break
        time.sleep(15)
```

**Available video models on Replicate (ranked, mid-2025):**
- `runway/gen-4-turbo` — Runway Gen-4.5 (#1 benchmark, best physics/realism)
- `google/veo-3` / `google/veo-3-fast` — Google Veo 3.1 (native audio, high quality)
- `kwaivgi/kling-v3-omni-video` — Kling 3.0 Omni (multi-shot 6 scenes, lip-sync, audio)
- `bytedance/seedance-2.0` — Seedance 2.0 (9 ref images, motion transfer, lip-sync)
- `minimax/video-01` — Hailuo 2.3/MiniMax (balanced cost/quality, human motion)
- `pixverse/pixverse-v6` — PixVerse v6 (multi-shot, camera control, audio)
- `wavespeedai/wan-2.1-t2v-480p` — Wan 2.7 T2V (open source, 27B MoE)
- `prunaai/p-video` — PrunaAI (draft mode 4x faster, T2V+I2V+A2V)
- `xai/grok-imagine-video` — Grok Imagine Video (~30s gen, social content)

See `references/replicate-batch-workflow.md` for detailed comparison and pricing.

### HuggingFace Spaces (Free but limited)
```python
# pip install gradio_client
from gradio_client import Client
client = Client("Wan-AI/Wan2.1-T2V-1.3B")  # Requires HF_TOKEN
result = client.predict(prompt="...", api_name="/generate")
```

**Note:** HuggingFace Spaces require `HF_TOKEN` even for "public" spaces (401 errors without it). Most video spaces also hit GPU duration limits on free tier.

## Pitfalls

1. **No GPU server = no local generation.** Video diffusion models need ≥12GB VRAM. On CPU-only servers, you MUST use cloud APIs (fal.ai, Replicate, Luma, etc.). Always run `nvidia-smi` first.
2. **HuggingFace "public" spaces still need auth.** Always set `HF_TOKEN` environment variable. Even spaces listed as public return 401 without it.
3. **Free tier clip durations are 4-8 seconds.** For a 15-second scene, generate 2-3 clips and concatenate with ffmpeg.
4. **Character consistency across scenes** is the hardest problem. Use PixVerse's Character Reference, Vidu's Multi-Reference, or Runway's Characters feature.
5. **fal.ai is the best unified gateway** — one API key accesses Kling, Hailuo, PixVerse, Vidu, Luma, Wan, and more. Avoids managing multiple accounts.
6. **fal.ai "exhausted balance" error.** When the $1 free credit runs out, ALL endpoints return 403 with `"User is locked. Reason: Exhausted balance. Top up your balance at fal.ai/dashboard/billing."` — no model works, not even cheap ones. User must top up or create a new account with a different email.
7. **HuggingFace Spaces GPU duration limits.** Even accessible spaces like `Pyramid-Flow/pyramid-flow` cap GPU at ~60-140s, which is often insufficient for video generation. Error: `"The requested GPU duration (140s) is larger than the maximum allowed"`. Reducing duration/fps doesn't help if the model itself needs more compute.
8. **Replicate API auth issues.** The auth header MUST be `Authorization: Bearer r8_...` (not `Token r8_...`). If you get 401 "You did not pass a valid authentication token": (a) token may not be active yet — wait a few minutes after creation; (b) token was revoked or copy-pasted incorrectly (check for trailing spaces/missing chars); (c) account needs email verification or billing setup. Verify with `curl -s -H "Authorization: Bearer r8_..." https://api.replicate.com/v1/account`. The Python SDK reads `REPLICATE_API_TOKEN` env var automatically.
9. **Replicate rate limiting (free accounts).** Without a payment method, rate limit is 6 requests/min with burst of 1. Submitting multiple predictions in rapid succession returns 429. **Fix:** Add `time.sleep(12)` between each prediction submission. The `retry_after` field in the 429 response tells you exactly how long to wait (~10s). Adding a payment method removes this restriction.
10. **Replicate credit exhaustion.** Free accounts get limited credits. When exhausted, you get `{"title": "Insufficient credit"}` 402 error. Must add billing at replicate.com/account/billing. Unlike fal.ai, there's no daily refresh — once credits are gone, they're gone until you pay.
11. **Replicate model endpoint shortcut.** Use `POST /v1/models/{owner}/{name}/predictions` instead of `/v1/predictions` with a version ID. This always uses the latest version and is simpler. Example: `POST /v1/models/minimax/video-01/predictions`.
12. **minimax/video-01 on Replicate** generates 6-second clips, takes 3-5 minutes per prediction. It's the same as Hailuo AI. Supports `prompt_optimizer: true` (recommended) and optional `first_frame_image` for image-to-video. No aspect ratio control in text-to-video mode — output is always 16:9 landscape.
13. **LM model ≠ video quality.** Users may think upgrading the orchestrating LM (e.g., Opus 4.6 → 4.7, or using OpenRouter) will improve video output. It won't. The LM only writes prompts and calls APIs — video quality is 100% determined by the video generation model (Kling, Veo, Hailuo, etc.). OpenRouter is an LLM gateway (text models only), not a video/image/audio router. Clarify this when users ask about "which model to use for video."
14. **Audio production for AI video.** AI video generators produce silent clips. Always plan for post-production audio: TTS narration (Edge TTS `id-ID-ArdiNeural` for Indonesian), ambient background (ffmpeg sine/noise generators), and music. Mix with ffmpeg `amix` filter. See `references/video-audio-postproduction.md`.

## References

- `references/free-video-api-landscape.md` — Detailed comparison of all free AI video generation platforms with working Python code
- `references/cinematic-prompt-patterns.md` — Prompt engineering patterns, camera/lighting keywords, platform recommendations per scene type, character consistency tips
- `references/video-audio-postproduction.md` — Adding narration, ambient music, and sound design to AI-generated silent video clips
- `references/replicate-batch-workflow.md` — Proven workflow for batch video generation via Replicate API (rate limiting, polling, cost estimates)
- [fal.ai Documentation](https://fal.ai/docs)
- [Runway API Documentation](https://docs.runwayml.com/)
- [Luma AI API](https://docs.lumalabs.ai/)
- [Replicate](https://replicate.com/)
- [Kling AI](https://klingai.com/)
