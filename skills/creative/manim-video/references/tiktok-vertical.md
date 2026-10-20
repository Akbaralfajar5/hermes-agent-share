# TikTok / Reels Vertical Video with Manim

## Config for 9:16 Vertical Format

```python
# Place at top of script.py, BEFORE class definitions
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.background_color = "#0A0A0A"
```

This gives a 9:16 aspect ratio at 1080x1920 — native TikTok/Reels/Shorts resolution.

## Frame Dimensions

With `frame_width=9, frame_height=16`:
- Horizontal range: -4.5 to +4.5
- Vertical range: -8 to +8
- `to_edge(UP, buff=0.8)` places at y ≈ 7.2
- `to_edge(DOWN, buff=1.0)` places at y ≈ -7.0

## Duration Guidelines

| Platform | Ideal Duration | Max |
|----------|---------------|-----|
| TikTok | 30-60s | 3 min |
| Instagram Reels | 15-30s | 90s |
| YouTube Shorts | 30-60s | 60s |

For motivational/educational content: 45-55 seconds is the sweet spot.

## Scene Structure for Short-Form

Typical 5-scene arc for a 45-60s video:

1. **Hook** (0-8s) — Bold statement, question, or shocking number. Must grab in first 2 seconds.
2. **Setup/Visualization** (8-20s) — Show the concept visually. Grid, chart, animation.
3. **Escalation** (20-35s) — Build tension. Statistics, comparisons, "did you know" moments.
4. **Climax** (35-45s) — Dramatic reveal, countdown, or emotional peak.
5. **CTA/Closing** (45-55s) — Call to action. Single powerful phrase. Fade to black.

## Creative Patterns That Work on TikTok

### The "Shocking Number" Pattern
```python
# Flash effect for dramatic number reveal
flash_rect = Rectangle(
    width=config.frame_width + 1,
    height=config.frame_height + 1,
    fill_color=WHITE, fill_opacity=0.8, stroke_width=0
)
self.play(FadeIn(flash_rect, run_time=0.15))
self.add(big_number)
self.play(FadeOut(flash_rect, run_time=0.5))
```

### The "Grid of Life" Pattern
Visualize quantities as grids of small squares. Each square = 1 unit (week, day, dollar).
Color-code phases. Show "used" vs "remaining" dramatically.

### The "Cascading Stats" Pattern
Show a chain of calculations where each result feeds the next, escalating to a shocking conclusion.

### The "Countdown" Pattern
```python
# Animated counter ticking down
for count in counts:
    new_text = Text(f"{count:,}", font_size=100, color=GOLD, weight=BOLD, font=MONO)
    new_text.move_to(old_text)
    self.play(
        FadeOut(old_text, shift=DOWN * 0.2),
        FadeIn(new_text, shift=DOWN * 0.2),
        run_time=0.3
    )
    old_text = new_text
```

## Typography for Vertical

- Title text: `font_size=60-72` (fills ~60% width)
- Big numbers: `font_size=100-120` (hero element)
- Body text: `font_size=26-32`
- Labels/captions: `font_size=20-24`
- Always use `font=MONO` (monospace) for clean rendering
- Max ~20 characters per line to avoid overflow

## Color Palette for Dark TikTok Content

```python
BG = "#0A0A0A"          # Near-black background
TEXT_COLOR = "#FFFFFF"   # Primary text
DIM_TEXT = "#888888"     # Secondary/subtitle text
ACCENT = "#FF4444"       # Danger/urgency (red)
CURRENT_COLOR = "#FFD700"  # Gold — highlights, key numbers
```

## Rendering & Stitching Workflow

```bash
# 1. Render all scenes at draft quality (fast iteration)
manim -ql script.py Scene1_Hook Scene2_Grid Scene3_Scroll Scene4_Countdown Scene5_CTA

# 2. Create concat file
cat > concat.txt << 'EOF'
file 'media/videos/script/1920p15/Scene1_Hook.mp4'
file 'media/videos/script/1920p15/Scene2_Grid.mp4'
file 'media/videos/script/1920p15/Scene3_Scroll.mp4'
file 'media/videos/script/1920p15/Scene4_Countdown.mp4'
file 'media/videos/script/1920p15/Scene5_CTA.mp4'
EOF

# 3. Stitch with ffmpeg (copy codec = instant, no re-encode)
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final_draft.mp4

# 4. For production quality (1080x1920 @ 60fps):
manim -qh script.py Scene1_Hook Scene2_Grid ...
# Output lands in media/videos/script/1920p60/
```

Note: `-ql` renders at 1920p but only 15fps. For TikTok upload this is acceptable for draft review. Use `-qm` (30fps) or `-qh` (60fps) for final upload.

## Post-Production Tips

- **Audio**: Add via ffmpeg: `ffmpeg -i final.mp4 -i music.mp3 -c:v copy -c:a aac -shortest output.mp4`
- **Captions**: Use `self.add_subcaption("text", duration=N)` in each scene for auto-generated SRT
- **Hashtags**: #motivasi #mindblown #fyp #edutok #facts
- **Best posting times**: 19:00-21:00 local time for engagement

## Pitfalls

1. **Text overflow**: Vertical frames are narrow. Keep text under 20 chars/line or use `\n` breaks.
2. **Safe zones**: TikTok overlays UI at top (username) and bottom (caption/buttons). Keep critical content in the middle 70% vertically (y range -5 to +5).
3. **Animation speed**: TikTok viewers scroll fast. First 2 seconds must have motion. Never start with a static frame.
4. **Large VGroups**: Animating 4000+ squares individually is slow to render. Use `LaggedStart` with high `lag_ratio` for wave effects, or batch-animate subgroups.
5. **Font rendering**: `font="Monospace"` is the safest cross-platform choice. Avoid custom fonts unless verified installed.
