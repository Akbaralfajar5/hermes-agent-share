# Free AI Video Generation API Landscape (May 2025)

## Strategy: Maximizing Free Video Generation

For projects needing 10-20+ clips without budget:
1. **fal.ai** ($1 free credit) — generate ~15-20 clips via unified API
2. **PixVerse web** (90 credits/day) — manual generation via browser
3. **Kling AI web** (66 credits/day) — best for realistic human faces
4. **Hailuo AI web** (free daily) — best for natural human motion
5. **Replicate** (free predictions for new users) — API-based

Spread generation across platforms over 3-4 days to maximize free credits.

## fal.ai — Best Unified Gateway

**Signup:** fal.ai → GitHub/Google login → Dashboard → Keys
**Free credit:** $1 on signup (enough for ~15-20 five-second clips at 360p)
**Install:** `pip install fal-client`

### All Video Endpoints (as of May 2025)

```python
import os, fal_client
os.environ["FAL_KEY"] = "YOUR_KEY"

# Pattern: fal_client.subscribe(endpoint, arguments={...})
# Returns: {"video": {"url": "https://..."}}

ENDPOINTS = {
    # Text-to-Video
    "wan_25": "fal-ai/wan-25-preview/text-to-video",          # $0.05-0.15/sec
    "hailuo_02": "fal-ai/minimax/hailuo-02/standard/text-to-video",  # $0.045/sec
    "pixverse_v6": "fal-ai/pixverse/v6/text-to-video",        # $0.025/sec@360p
    "kling_v3_std": "fal-ai/kling-video/v3/standard/text-to-video",  # $0.084/sec
    "seedance_20": "bytedance/seedance-2.0/text-to-video",    # $0.30/sec
    
    # Image-to-Video
    "wan_27_i2v": "fal-ai/wan/v2.7/image-to-video",           # $0.10/sec
    "hailuo_23_fast": "fal-ai/minimax/hailuo-2.3-fast/standard/image-to-video",  # $0.19/6s
    "pixverse_c1": "fal-ai/pixverse/c1/image-to-video",       # $0.030/sec@360p
    "kling_v3_pro_i2v": "fal-ai/kling-video/v3/pro/image-to-video",  # $0.112/sec
    "vidu_q3": "fal-ai/vidu/q3/image-to-video",               # $0.07/sec@360p
    "luma_ray2": "fal-ai/luma-dream-machine/ray-2/image-to-video",
    "veo_31_fast": "fal-ai/veo3.1/fast/image-to-video",       # $0.10/sec
}
```

### Cheapest Strategy for Film Project (~13 clips)

Using PixVerse V6 at 360p ($0.025/sec × 5sec = $0.125/clip):
- 13 clips × $0.125 = **$1.63 total** (slightly over $1 free credit)
- Mix with Hailuo 02 for key emotional scenes (better quality)

## Replicate — Free Predictions for New Users

**Signup:** replicate.com → GitHub login
**Free tier:** Free predictions (limited, for new accounts)
**Install:** `pip install replicate`

```python
import os, replicate
os.environ["REPLICATE_API_TOKEN"] = "r8_xxxx"

# Wan 2.1 (good quality, ~$0.09/sec)
output = replicate.run("wavespeedai/wan-2.1-t2v-480p", input={
    "prompt": "...",
    "num_frames": 81,  # ~5 seconds at 16fps
})
# Returns URL to video file
```

## Luma AI — Direct Python SDK

**Signup:** lumalabs.ai → API keys page
**Free tier:** Free credits on signup
**Install:** `pip install lumaai`

```python
from lumaai import LumaAI
import time

client = LumaAI(auth_token="luma-xxxx")
generation = client.generations.video.create(
    prompt="...",
    model="ray-2",        # or "ray-flash-2" (faster/cheaper)
    resolution="720p",
    duration="5s",
)

while generation.state != "completed":
    time.sleep(5)
    generation = client.generations.video.get(id=generation.id)

print(f"Video: {generation.assets.video}")
```

## MiniMax/Hailuo — Direct API

**Signup:** platform.minimaxi.com
**Free tier:** Free credits on signup

```python
import requests, time

API_KEY = "your_minimax_key"
resp = requests.post("https://api.minimaxi.com/v1/video_generation",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={"prompt": "...", "model": "video-01"})
task_id = resp.json()["task_id"]

while True:
    time.sleep(10)
    r = requests.get(f"https://api.minimaxi.com/v1/query/video_generation?task_id={task_id}",
        headers={"Authorization": f"Bearer {API_KEY}"})
    if r.json()["status"] == "Success":
        print(f"Video: {r.json()['file_id']}"); break
```

## HuggingFace — Truly Free but Limited

**Important:** Even "public" spaces return 401 without `HF_TOKEN`. Set it always.
**GPU limits:** Most spaces cap at 60-140s GPU time, which may not be enough for video generation.

```python
# Set token first
os.environ["HF_TOKEN"] = "hf_xxxx"

from gradio_client import Client
client = Client("Wan-AI/Wan2.1-T2V-1.3B")
result = client.predict(prompt="...", api_name="/generate")
```

**Known working spaces (May 2025):**
- `Pyramid-Flow/pyramid-flow` — accessible but GPU-limited (140s max)
- Most others require token and have queue/GPU constraints

## EachLabs — 165+ Models via REST

**Signup:** eachlabs.ai
**API:** Simple REST POST → Poll → Download

```python
import requests, time

API_KEY = "your_eachlabs_key"
resp = requests.post("https://api.eachlabs.ai/v1/prediction",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={"model": "pixverse-v5.6", "config": {"prompt": "...", "duration": 5}})
prediction_id = resp.json()["id"]

while True:
    time.sleep(5)
    r = requests.get(f"https://api.eachlabs.ai/v1/prediction/{prediction_id}",
        headers={"X-API-Key": API_KEY})
    if r.json()["status"] == "completed":
        print(r.json()["output"]["video_url"]); break
```

## Film Production Workflow (Multi-Scene)

For a 10-scene short film like Malin Kundang:

```python
import fal_client, time, subprocess, os

os.environ["FAL_KEY"] = "YOUR_KEY"

scenes = [
    {"name": "scene01_opening", "prompt": "Cinematic aerial shot of rocky Indonesian beach..."},
    {"name": "scene02_village", "prompt": "Indonesian fishing village, mother and son..."},
    # ... more scenes
]

output_dir = "/tmp/film_project/clips"
os.makedirs(output_dir, exist_ok=True)

for scene in scenes:
    print(f"Generating {scene['name']}...")
    result = fal_client.subscribe("fal-ai/pixverse/v6/text-to-video", arguments={
        "prompt": scene["prompt"],
        "quality": "360p",
        "duration": 5,
        "aspect_ratio": "9:16",  # TikTok vertical
    })
    
    # Download video
    video_url = result['video']['url']
    output_path = f"{output_dir}/{scene['name']}.mp4"
    subprocess.run(["curl", "-o", output_path, video_url])
    print(f"  Saved: {output_path}")
    time.sleep(2)  # Rate limiting

# Concatenate all clips
with open(f"{output_dir}/concat.txt", "w") as f:
    for scene in scenes:
        f.write(f"file '{scene['name']}.mp4'\n")

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", f"{output_dir}/concat.txt",
    "-c", "copy", f"{output_dir}/../final_film.mp4"
])
```

## Key Insight: Server Without GPU

On a server without GPU (common for cloud VMs):
- **Cannot run local models** (Stable Video Diffusion, CogVideoX, etc.)
- **Must use cloud APIs** (fal.ai, Replicate, Luma, etc.)
- **ComfyUI local is not an option** without GPU
- **Always check `nvidia-smi` first** before attempting local generation
