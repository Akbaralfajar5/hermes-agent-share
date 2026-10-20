---
name: manim-video
description: "Manim CE animations: 3Blue1Brown math/algo videos."
version: 1.0.0
---

# Manim Video Production Pipeline

## When to use

Use when users request: animated explanations, math animations, concept visualizations, algorithm walkthroughs, technical explainers, 3Blue1Brown style videos, or any programmatic animation with geometric/mathematical content. Creates 3Blue1Brown-style explainer videos, algorithm visualizations, equation derivations, architecture diagrams, and data stories using Manim Community Edition.

## Creative Standard

This is educational cinema. Every frame teaches. Every animation reveals structure.

**Before writing a single line of code**, articulate the narrative arc. What misconception does this correct? What is the "aha moment"? What visual story takes the viewer from confusion to understanding? The user's prompt is a starting point — interpret it with pedagogical ambition.

**Geometry before algebra.** Show the shape first, the equation second. Visual memory encodes faster than symbolic memory. When the viewer sees the geometric pattern before the formula, the equation feels earned.

**First-render excellence is non-negotiable.** The output must be visually clear and aesthetically cohesive without revision rounds. If something looks cluttered, poorly timed, or like "AI-generated slides," it is wrong.

**Opacity layering directs attention.** Never show everything at full brightness. Primary elements at 1.0, contextual elements at 0.4, structural elements (axes, grids) at 0.15. The brain processes visual salience in layers.

**Breathing room.** Every animation needs `self.wait()` after it. The viewer needs time to absorb what just appeared. Never rush from one animation to the next. A 2-second pause after a key reveal is never wasted.

**Cohesive visual language.** All scenes share a color palette, consistent typography sizing, matching animation speeds. A technically correct video where every scene uses random different colors is an aesthetic failure.

## Prerequisites

Run `scripts/setup.sh` to verify all dependencies. Requires: Python 3.10+, Manim Community Edition v0.20+ (`pip install manim`), LaTeX (`texlive-full` on Linux, `mactex` on macOS), and ffmpeg. Reference docs tested against Manim CE v0.20.1.

### Installation Pitfalls (Linux)

Manim depends on `pycairo` and `manimpango`, which need C libraries installed FIRST:

```bash
# MUST install these system packages before pip install manim
sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config python3-dev

# Then install in order:
pip install pycairo      # builds C extension against libcairo
pip install manimpango   # builds C extension against libpango
pip install manim        # now succeeds
```

**Common errors if you skip this:**
- `pycairo`: `subprocess.CalledProcessError: Command '['pkg-config', ... 'cairo']'` → install `libcairo2-dev`
- `manimpango`: `'pkg-config', '--atleast-version', '1.30.0', 'pangocairo'` → install `libpango1.0-dev`

### TikTok / Vertical Video (9:16)

To render vertical video for TikTok/Reels/Shorts, add this config at the top of your script:

```python
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
```

This produces native 1080×1920 output. All positioning uses the 9×16 coordinate space. Note that `-ql` (low quality) still renders at the configured pixel dimensions, just at 15fps.

### Installation Pitfalls (Ubuntu/Debian)

`pip install manim` often fails on fresh systems due to missing C libraries. Install in this order:

```bash
# 1. System dependencies FIRST
sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config python3-dev

# 2. pycairo must be built before manim can resolve its dependency tree
pip install pycairo

# 3. manimpango may also need explicit install
pip install manimpango

# 4. NOW manim will install cleanly
pip install manim
```

**Common errors if you skip this:**
- `pangocairo` version check fails → install `libpango1.0-dev`
- `pycairo` metadata generation fails → install `libcairo2-dev` + `pkg-config`

### TikTok Vertical Format

For TikTok/Reels (9:16 vertical), add to the top of your script:

```python
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
```

Note: `-ql` renders at full pixel dimensions (not 480p) when custom config is set. Output lands in `media/videos/script/1920p15/`.

### Ubuntu/Debian Build Dependencies (Critical Pitfall)

Manim depends on `manimpango` and `pycairo` which compile C extensions. Install system libraries **before** pip install:

```bash
sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config python3-dev
pip install pycairo manimpango  # build these first, separately
pip install manim               # then manim installs cleanly
```

**Without `libpango1.0-dev`**: `manimpango` build fails with `pkg-config --atleast-version 1.30.0 pangocairo returned non-zero`.
**Without `libcairo2-dev`**: `pycairo` metadata generation fails silently — pip shows a generic "error: subprocess-exited-with-error" with no clear cause.
**Order matters**: install `pycairo` before `manim` — if you run `pip install manim` first, it tries to build `pycairo` as a dependency and the error is buried in a long traceback.

## Modes

| Mode | Input | Output | Reference |
|------|-------|--------|-----------|
| **Concept explainer** | Topic/concept | Animated explanation with geometric intuition | `references/scene-planning.md` |
| **Equation derivation** | Math expressions | Step-by-step animated proof | `references/equations.md` |
| **Algorithm visualization** | Algorithm description | Step-by-step execution with data structures | `references/graphs-and-data.md` |
| **Data story** | Data/metrics | Animated charts, comparisons, counters | `references/graphs-and-data.md` |
| **Architecture diagram** | System description | Components building up with connections | `references/mobjects.md` |
| **Paper explainer** | Research paper | Key findings and methods animated | `references/scene-planning.md` |
| **3D visualization** | 3D concept | Rotating surfaces, parametric curves, spatial geometry | `references/camera-and-3d.md` |
| **TikTok/Reels short film** | Topic/message + vertical format | 9:16 vertical video, 30-60s, scene-per-concept | `references/tiktok-vertical.md` |

## Stack

Single Python script per project. No browser, no Node.js, no GPU required.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | Manim Community Edition | Scene rendering, animation engine |
| Math | LaTeX (texlive/MiKTeX) | Equation rendering via `MathTex` |
| Video I/O | ffmpeg | Scene stitching, format conversion, audio muxing |
| TTS | ElevenLabs / Qwen3-TTS (optional) | Narration voiceover |

## Pipeline

```
PLAN --> CODE --> RENDER --> STITCH --> AUDIO (optional) --> REVIEW
```

1. **PLAN** — Write `plan.md` with narrative arc, scene list, visual elements, color palette, voiceover script
2. **CODE** — Write `script.py` with one class per scene, each independently renderable
3. **RENDER** — `manim -ql script.py Scene1 Scene2 ...` for draft, `-qh` for production
4. **STITCH** — ffmpeg concat of scene clips into `final.mp4`
5. **AUDIO** — Add voiceover via `text_to_speech` tool + background music via ffmpeg synthesis. Full multi-layer pipeline in `references/rendering.md` § "Full Audio Pipeline"
6. **REVIEW** — Render preview stills, verify against plan, adjust

## Project Structure

```
project-name/
  plan.md                # Narrative arc, scene breakdown
  script.py              # All scenes in one file
  concat.txt             # ffmpeg scene list
  final.mp4              # Stitched output
  media/                 # Auto-generated by Manim
    videos/script/480p15/
```

## Creative Direction

### Color Palettes

| Palette | Background | Primary | Secondary | Accent | Use case |
|---------|-----------|---------|-----------|--------|----------|
| **Classic 3B1B** | `#1C1C1C` | `#58C4DD` (BLUE) | `#83C167` (GREEN) | `#FFFF00` (YELLOW) | General math/CS |
| **Warm academic** | `#2D2B55` | `#FF6B6B` | `#FFD93D` | `#6BCB77` | Approachable |
| **Neon tech** | `#0A0A0A` | `#00F5FF` | `#FF00FF` | `#39FF14` | Systems, architecture |
| **Monochrome** | `#1A1A2E` | `#EAEAEA` | `#888888` | `#FFFFFF` | Minimalist |

### Animation Speed

| Context | run_time | self.wait() after |
|---------|----------|-------------------|
| Title/intro appear | 1.5s | 1.0s |
| Key equation reveal | 2.0s | 2.0s |
| Transform/morph | 1.5s | 1.5s |
| Supporting label | 0.8s | 0.5s |
| FadeOut cleanup | 0.5s | 0.3s |
| "Aha moment" reveal | 2.5s | 3.0s |

### Typography Scale

| Role | Font size | Usage |
|------|-----------|-------|
| Title | 48 | Scene titles, opening text |
| Heading | 36 | Section headers within a scene |
| Body | 30 | Explanatory text |
| Label | 24 | Annotations, axis labels |
| Caption | 20 | Subtitles, fine print |

### Fonts

**Use monospace fonts for all text.** Manim's Pango renderer produces broken kerning with proportional fonts at all sizes. See `references/visual-design.md` for full recommendations.

```python
MONO = "Menlo"  # define once at top of file

Text("Fourier Series", font_size=48, font=MONO, weight=BOLD)  # titles
Text("n=1: sin(x)", font_size=20, font=MONO)                  # labels
MathTex(r"\nabla L")                                            # math (uses LaTeX)
```

Minimum `font_size=18` for readability.

### Per-Scene Variation

Never use identical config for all scenes. For each scene:
- **Different dominant color** from the palette
- **Different layout** — don't always center everything
- **Different animation entry** — vary between Write, FadeIn, GrowFromCenter, Create
- **Different visual weight** — some scenes dense, others sparse

## Workflow

### Step 1: Plan (plan.md)

Before any code, write `plan.md`. See `references/scene-planning.md` for the comprehensive template.

### Step 2: Code (script.py)

One class per scene. Every scene is independently renderable.

```python
from manim import *

BG = "#1C1C1C"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"
MONO = "Menlo"

class Scene1_Introduction(Scene):
    def construct(self):
        self.camera.background_color = BG
        title = Text("Why Does This Work?", font_size=48, color=PRIMARY, weight=BOLD, font=MONO)
        self.add_subcaption("Why does this work?", duration=2)
        self.play(Write(title), run_time=1.5)
        self.wait(1.0)
        self.play(FadeOut(title), run_time=0.5)
```

Key patterns:
- **Subtitles** on every animation: `self.add_subcaption("text", duration=N)` or `subcaption="text"` on `self.play()`
- **Shared color constants** at file top for cross-scene consistency
- **`self.camera.background_color`** set in every scene
- **Clean exits** — FadeOut all mobjects at scene end: `self.play(FadeOut(Group(*self.mobjects)))`

### Step 3: Render

```bash
manim -ql script.py Scene1_Introduction Scene2_CoreConcept  # draft
manim -qh script.py Scene1_Introduction Scene2_CoreConcept  # production
```

### Step 4: Stitch

```bash
cat > concat.txt << 'EOF'
file 'media/videos/script/480p15/Scene1_Introduction.mp4'
file 'media/videos/script/480p15/Scene2_CoreConcept.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final.mp4
```

### Step 5: Add Narration & Audio

Generate narration with Edge TTS (or ElevenLabs), then mix with ambient background:

```bash
# Generate ambient drone background using ffmpeg synth
ffmpeg -y \
  -f lavfi -i "sine=frequency=80:duration=60:sample_rate=44100" \
  -f lavfi -i "anoisesrc=d=60:c=pink:r=44100:a=0.02" \
  -filter_complex "[0:a]volume=0.15[s1];[1:a]volume=0.3[noise]; \
    [s1][noise]amix=inputs=2:duration=longest[mixed]; \
    [mixed]afade=t=in:st=0:d=3,afade=t=out:st=56:d=4,lowpass=f=500,volume=0.4[out]" \
  -map "[out]" ambient_bg.wav

# Mix video + narration + background
ffmpeg -y \
  -i final.mp4 -i narration.ogg -i ambient_bg.wav \
  -filter_complex "[1:a]volume=1.3[narr];[2:a]volume=0.4[bg]; \
    [narr][bg]amix=inputs=2:duration=shortest[audio_out]" \
  -map 0:v -map "[audio_out]" -c:v copy -c:a aac -b:a 192k -shortest \
  final_with_audio.mp4
```

**TTS locale pitfall:** Edge TTS defaults to `en-US-AriaNeural`. For Indonesian content, set voice to `id-ID-ArdiNeural` (male) or `id-ID-GadisNeural` (female) in `~/.hermes/config.yaml` under `tts.edge.voice`. List available voices: `edge-tts --list-voices | grep id-ID`.

### Step 6: Review

```bash
manim -ql --format=png -s script.py Scene2_CoreConcept  # preview still
```

## Critical Implementation Notes

### Raw Strings for LaTeX
```python
# WRONG: MathTex("\frac{1}{2}")
# RIGHT:
MathTex(r"\frac{1}{2}")
```

### buff >= 0.5 for Edge Text
```python
label.to_edge(DOWN, buff=0.5)  # never < 0.5
```

### FadeOut Before Replacing Text
```python
self.play(ReplacementTransform(note1, note2))  # not Write(note2) on top
```

### Never Animate Non-Added Mobjects
```python
self.play(Create(circle))  # must add first
self.play(circle.animate.set_color(RED))  # then animate
```

## Performance Targets

| Quality | Resolution | FPS | Speed |
|---------|-----------|-----|-------|
| `-ql` (draft) | 854x480 | 15 | 5-15s/scene |
| `-qm` (medium) | 1280x720 | 30 | 15-60s/scene |
| `-qh` (production) | 1920x1080 | 60 | 30-120s/scene |

Always iterate at `-ql`. Only render `-qh` for final output.

## TikTok / Vertical Video (9:16)

For TikTok, Reels, or Shorts, set vertical config at the top of the script:

```python
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.background_color = "#0A0A0A"
```

**Key differences for vertical:**
- `-ql` renders at 1920p15 (not 480p15) because height is the larger dimension
- Use `UP * N` and `DOWN * N` for vertical layout (more vertical space available)
- Text `font_size` can be larger (more width relative to content)
- `to_edge(UP/DOWN, buff=0.8)` for safe margins on mobile
- Grid/data visualizations: prefer tall layouts (40 cols × 100 rows, not 100×40)

**Concatenation for TikTok:**
```bash
# Render all scenes
manim -ql script.py Scene1 Scene2 Scene3 Scene4 Scene5

# Concat (files land in media/videos/script/1920p15/)
cat > concat.txt << 'EOF'
file 'media/videos/script/1920p15/Scene1.mp4'
file 'media/videos/script/1920p15/Scene2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final_tiktok.mp4
```

## Ubuntu/Debian Dependency Fix

Manim requires `pycairo` and `manimpango` which need system libraries:

```bash
# Install system deps FIRST
sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config python3-dev

# Then install Python packages in order
pip install pycairo      # Must succeed before manim
pip install manimpango   # Must succeed before manim
pip install manim        # Now this works
```

**Common error:** `pkg-config --atleast-version 1.30.0 pangocairo` fails → install `libpango1.0-dev`.
**Common error:** `pycairo` metadata generation fails → install `libcairo2-dev` and `pkg-config`.

## References

| File | Contents |
|------|----------|
| `references/animations.md` | Core animations, rate functions, composition, `.animate` syntax, timing patterns |
| `references/mobjects.md` | Text, shapes, VGroup/Group, positioning, styling, custom mobjects |
| `references/visual-design.md` | 12 design principles, opacity layering, layout templates, color palettes |
| `references/equations.md` | LaTeX in Manim, TransformMatchingTex, derivation patterns |
| `references/graphs-and-data.md` | Axes, plotting, BarChart, animated data, algorithm visualization |
| `references/camera-and-3d.md` | MovingCameraScene, ThreeDScene, 3D surfaces, camera control |
| `references/scene-planning.md` | Narrative arcs, layout templates, scene transitions, planning template |
| `references/rendering.md` | CLI reference, quality presets, ffmpeg, voiceover workflow, GIF export |
| `references/troubleshooting.md` | LaTeX errors, animation errors, common mistakes, debugging |
| `references/animation-design-thinking.md` | When to animate vs show static, decomposition, pacing, narration sync |
| `references/updaters-and-trackers.md` | ValueTracker, add_updater, always_redraw, time-based updaters, patterns |
| `references/paper-explainer.md` | Turning research papers into animations — workflow, templates, domain patterns |
| `references/decorations.md` | SurroundingRectangle, Brace, arrows, DashedLine, Angle, annotation lifecycle |
| `references/production-quality.md` | Pre-code, pre-render, post-render checklists, spatial layout, color, tempo |

## Templates

| File | Contents |
|------|----------|
| `templates/tiktok_vertical.py` | Starter template for 9:16 TikTok/Reels vertical video with proper config, color palette, and scene structure |
| `references/tiktok-vertical.md` | TikTok/Reels 9:16 vertical format: config, scene structure, creative patterns, stitching |

---

## Creative Divergence (use only when user requests experimental/creative/unique output)

If the user asks for creative, experimental, or unconventional explanatory approaches, select a strategy and reason through it BEFORE designing the animation.

- **SCAMPER** — when the user wants a fresh take on a standard explanation
- **Assumption Reversal** — when the user wants to challenge how something is typically taught

### SCAMPER Transformation
Take a standard mathematical/technical visualization and transform it:
- **Substitute**: replace the standard visual metaphor (number line → winding path, matrix → city grid)
- **Combine**: merge two explanation approaches (algebraic + geometric simultaneously)
- **Reverse**: derive backward — start from the result and deconstruct to axioms
- **Modify**: exaggerate a parameter to show why it matters (10x the learning rate, 1000x the sample size)
- **Eliminate**: remove all notation — explain purely through animation and spatial relationships

### Assumption Reversal
1. List what's "standard" about how this topic is visualized (left-to-right, 2D, discrete steps, formal notation)
2. Pick the most fundamental assumption
3. Reverse it (right-to-left derivation, 3D embedding of a 2D concept, continuous morphing instead of steps, zero notation)
4. Explore what the reversal reveals that the standard approach hides
