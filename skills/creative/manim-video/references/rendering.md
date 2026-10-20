# Rendering Reference

## Prerequisites

```bash
manim --version       # Manim CE
pdflatex --version    # LaTeX
ffmpeg -version       # ffmpeg
```

## CLI Reference

```bash
manim -ql script.py Scene1 Scene2    # draft (480p 15fps)
manim -qm script.py Scene1           # medium (720p 30fps)
manim -qh script.py Scene1           # production (1080p 60fps)
manim -ql --format=png -s script.py Scene1  # preview still (last frame)
manim -ql --format=gif script.py Scene1     # GIF output
```

## Quality Presets

| Flag | Resolution | FPS | Use case |
|------|-----------|-----|----------|
| `-ql` | 854x480 | 15 | Draft iteration (layout, timing) |
| `-qm` | 1280x720 | 30 | Preview (use for text-heavy scenes) |
| `-qh` | 1920x1080 | 60 | Production |

**Text rendering quality:** `-ql` (480p15) produces noticeably poor text kerning and readability. For scenes with significant text, preview stills at `-qm` to catch issues invisible at 480p. Use `-ql` only for testing layout and animation timing.

## Output Structure

```
media/videos/script/480p15/Scene1_Intro.mp4
media/images/script/Scene1_Intro.png  (from -s flag)
```

## Stitching with ffmpeg

```bash
cat > concat.txt << 'EOF'
file 'media/videos/script/480p15/Scene1_Intro.mp4'
file 'media/videos/script/480p15/Scene2_Core.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final.mp4
```

## Add Voiceover

```bash
# Mux narration
ffmpeg -y -i final.mp4 -i narration.mp3 -c:v copy -c:a aac -b:a 192k -shortest final_narrated.mp4

# Concat per-scene audio first
cat > audio_concat.txt << 'EOF'
file 'audio/scene1.mp3'
file 'audio/scene2.mp3'
EOF
ffmpeg -y -f concat -safe 0 -i audio_concat.txt -c copy full_narration.mp3
```

## Add Background Music

```bash
ffmpeg -y -i final.mp4 -i music.mp3 \
  -filter_complex "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=shortest" \
  -c:v copy final_with_music.mp4
```

## Full Audio Pipeline: TTS Narration + Ambient Music + Video

When no pre-recorded audio exists, generate everything from scratch:

### Step 1: Generate narration segments with Hermes TTS

Use the built-in `text_to_speech` tool to create narration per scene group. Output is `.ogg` format.
Split narration into 2-4 segments aligned to scene boundaries.

**CRITICAL: Match TTS voice to content language.** The default Edge TTS voice is `en-US-AriaNeural` (English/American). For non-English narration, change the voice in `~/.hermes/config.yaml` BEFORE generating:

```yaml
tts:
  provider: edge
  edge:
    voice: id-ID-ArdiNeural    # Indonesian male (natural, friendly)
    # voice: id-ID-GadisNeural # Indonesian female
    # voice: en-US-AriaNeural  # English (default)
    # voice: ja-JP-KeitaNeural # Japanese male
```

List all available voices: `edge-tts --list-voices | grep "id-ID"` (replace with target locale).

Common Indonesian voices:
- `id-ID-ArdiNeural` — Male, general, friendly/positive tone
- `id-ID-GadisNeural` — Female, general, friendly/positive tone

**Pitfall**: If narration sounds "bule" (foreign accent) on Indonesian text, the voice is still set to `en-US-*`. The English voice will attempt Indonesian words but with wrong pronunciation and cadence. Always verify the voice locale matches the script language.

### Step 2: Combine narration segments with timed offsets

```bash
# Get durations of each part
ffprobe -v quiet -show_entries format=duration -of csv=p=0 narasi_part1.ogg

# Mix with adelay to place each segment at the right timestamp
ffmpeg -y \
  -i narasi_part1.ogg -i narasi_part2.ogg -i narasi_part3.ogg \
  -filter_complex "\
    [0:a]atrim=0:15,asetpts=PTS-STARTPTS[a0]; \
    [1:a]atrim=0:18,asetpts=PTS-STARTPTS,adelay=16000|16000[a1]; \
    [2:a]atrim=0:14,asetpts=PTS-STARTPTS,adelay=35000|35000[a2]; \
    [a0][a1][a2]amix=inputs=3:duration=longest:dropout_transition=2[out]" \
  -map "[out]" -ac 2 -ar 44100 narasi_full.wav
```

Key: `adelay=16000|16000` = start at 16 seconds (milliseconds, both channels).
Use `atrim=0:N` to cut each segment to fit its scene's duration.

### Step 3: Generate synthetic ambient background music

No external music file needed — ffmpeg can synthesize dark ambient drones:

```bash
ffmpeg -y \
  -f lavfi -i "sine=frequency=80:duration=48:sample_rate=44100" \
  -f lavfi -i "sine=frequency=120:duration=48:sample_rate=44100" \
  -f lavfi -i "sine=frequency=160:duration=48:sample_rate=44100" \
  -f lavfi -i "anoisesrc=d=48:c=pink:r=44100:a=0.02" \
  -filter_complex "\
    [0:a]volume=0.15[s1]; [1:a]volume=0.08[s2]; [2:a]volume=0.05[s3]; \
    [3:a]volume=0.3[noise]; \
    [s1][s2][s3][noise]amix=inputs=4:duration=longest[mixed]; \
    [mixed]afade=t=in:st=0:d=3,afade=t=out:st=44:d=4,lowpass=f=500,volume=0.4[out]" \
  -map "[out]" -ac 2 -ar 44100 ambient_bg.wav
```

Adjust frequencies for mood: 60-100Hz = ominous, 200-400Hz = warm, add `anoisesrc=c=brown` for deeper rumble.

### Step 4: Mux narration onto video

```bash
ffmpeg -y -i final_draft.mp4 -i narasi_full.wav \
  -filter_complex "[1:a]atrim=0:47.6,asetpts=PTS-STARTPTS,volume=1.3[narr]" \
  -map 0:v -map "[narr]" -c:v copy -c:a aac -b:a 128k -shortest \
  final_with_voice.mp4
```

### Step 5: Layer background music under narration

```bash
ffmpeg -y -i final_with_voice.mp4 -i ambient_bg.wav \
  -filter_complex "\
    [0:a]volume=1.0[voice]; \
    [1:a]atrim=0:47.6,asetpts=PTS-STARTPTS,volume=0.5[bg]; \
    [voice][bg]amix=inputs=2:duration=shortest:dropout_transition=2[audio_out]" \
  -map 0:v -map "[audio_out]" -c:v copy -c:a aac -b:a 192k -shortest \
  final_complete.mp4
```

Voice at 1.0, background at 0.3-0.5 for clear narration over ambient bed.

## GIF Export

```bash
ffmpeg -y -i scene.mp4 \
  -vf "fps=15,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  output.gif
```

## Aspect Ratios

```bash
manim -ql --resolution 1080,1920 script.py Scene  # 9:16 vertical
manim -ql --resolution 1080,1080 script.py Scene  # 1:1 square
```

## Render Workflow

1. Draft render all scenes at `-ql`
2. Preview stills at key moments (`-s`)
3. Fix and re-render only broken scenes
4. Stitch with ffmpeg
5. Review stitched output
6. Production render at `-qh`
7. Re-stitch + add audio

## manim.cfg — Project Configuration

Create `manim.cfg` in the project directory for per-project defaults:

```ini
[CLI]
quality = low_quality
preview = True
media_dir = ./media

[renderer]
background_color = #0D1117

[tex]
tex_template_file = custom_template.tex
```

This eliminates repetitive CLI flags and `self.camera.background_color` in every scene.

## Sections — Chapter Markers

Mark sections within a scene for organized output:

```python
class LongVideo(Scene):
    def construct(self):
        self.next_section("Introduction")
        # ... intro content ...

        self.next_section("Main Concept")
        # ... main content ...

        self.next_section("Conclusion")
        # ... closing ...
```

Render individual sections: `manim --save_sections script.py LongVideo`
This outputs separate video files per section — useful for long videos where you want to re-render only one part.

## manim-voiceover Plugin (Recommended for Narrated Videos)

The official `manim-voiceover` plugin integrates TTS directly into scene code, auto-syncing animation duration to voiceover length. This is significantly cleaner than the manual ffmpeg muxing approach above.

### Installation

```bash
pip install "manim-voiceover[elevenlabs]"
# Or for free/local TTS:
pip install "manim-voiceover[gtts]"    # Google TTS (free, lower quality)
pip install "manim-voiceover[azure]"   # Azure Cognitive Services
```

### Usage

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService

class NarratedScene(VoiceoverScene):
    def construct(self):
        self.set_speech_service(ElevenLabsService(
            voice_name="Alice",
            model_id="eleven_multilingual_v2"
        ))

        # Voiceover auto-controls scene duration
        with self.voiceover(text="Here is a circle being drawn.") as tracker:
            self.play(Create(Circle()), run_time=tracker.duration)

        with self.voiceover(text="Now let's transform it into a square.") as tracker:
            self.play(Transform(circle, Square()), run_time=tracker.duration)
```

### Key Features

- `tracker.duration` — total voiceover duration in seconds
- `tracker.time_until_bookmark("mark1")` — sync specific animations to specific words
- Auto-generates subtitle `.srt` files
- Caches audio locally — re-renders don't re-generate TTS
- Works with: ElevenLabs, Azure, Google TTS, pyttsx3 (offline), and custom services

### Bookmarks for Precise Sync

```python
with self.voiceover(text='This is a <bookmark mark="circle"/>circle.') as tracker:
    self.wait_until_bookmark("circle")
    self.play(Create(Circle()), run_time=tracker.time_until_bookmark("circle", limit=1))
```

This is the recommended approach for any video with narration. The manual ffmpeg muxing workflow above is still useful for adding background music or post-production audio mixing.
