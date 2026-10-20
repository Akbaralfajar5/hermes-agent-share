# Video Audio Post-Production for AI-Generated Clips

AI video generators produce **silent clips**. This reference covers adding narration, ambient music, and sound design using Edge TTS + ffmpeg.

## 1. TTS Narration (Edge TTS)

### Indonesian Voices
```bash
# List available Indonesian voices
edge-tts --list-voices | grep "id-ID"
# id-ID-ArdiNeural    Male    General    Friendly, Positive
# id-ID-GadisNeural   Female  General    Friendly, Positive
```

### Hermes Config for Indonesian TTS
```yaml
# ~/.hermes/config.yaml
tts:
  provider: edge
  edge:
    voice: id-ID-ArdiNeural   # Male Indonesian (dramatic narration)
    # voice: id-ID-GadisNeural  # Female Indonesian
```

### Generate Narration in Parts
Split narration into parts matching scene groups for better timing control:
```python
# Part 1: Opening scenes (0-15s)
text_to_speech("Di pantai Air Manis, Padang...", output="narasi_part1.ogg")
# Part 2: Middle scenes (15-35s)  
text_to_speech("Bertahun-tahun berlalu...", output="narasi_part2.ogg")
# Part 3: Climax + ending (35-end)
text_to_speech("Tapi Malin mendorong ibunya...", output="narasi_part3.ogg")
```

## 2. Ambient Background Music (ffmpeg Synthesis)

Generate dark ambient drone without external files:
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

## 3. Mixing Narration Parts with Timing

Concat narration parts with delays matching video scene timestamps:
```bash
ffmpeg -y \
  -i narasi_part1.ogg \
  -i narasi_part2.ogg \
  -i narasi_part3.ogg \
  -filter_complex "\
    [0:a]atrim=0:14,asetpts=PTS-STARTPTS,adelay=1000|1000[a0]; \
    [1:a]atrim=0:17,asetpts=PTS-STARTPTS,adelay=16000|16000[a1]; \
    [2:a]atrim=0:13,asetpts=PTS-STARTPTS,adelay=34000|34000[a2]; \
    [a0][a1][a2]amix=inputs=3:duration=longest:dropout_transition=2,volume=1.5[out]" \
  -map "[out]" -ac 2 -ar 44100 narasi_full.wav
```

Key parameters:
- `atrim=0:N` — trim each part to N seconds
- `adelay=N|N` — delay start by N milliseconds (left|right channel)
- `volume=1.5` — boost narration volume

## 4. Final Mix: Video + Narration + Background

```bash
ffmpeg -y \
  -i video_silent.mp4 \
  -i narasi_full.wav \
  -i ambient_bg.wav \
  -filter_complex "\
    [1:a]atrim=0:47.6,asetpts=PTS-STARTPTS,volume=1.3[narr]; \
    [2:a]atrim=0:47.6,asetpts=PTS-STARTPTS,volume=0.4[bg]; \
    [narr][bg]amix=inputs=2:duration=shortest:dropout_transition=2[audio_out]" \
  -map 0:v -map "[audio_out]" \
  -c:v copy -c:a aac -b:a 192k \
  -shortest \
  final_with_audio.mp4
```

Volume balance:
- Narration: `volume=1.3` (dominant)
- Background music: `volume=0.4` (subtle, atmospheric)

## 5. Scene Concatenation

```bash
# Create concat list
cat > concat.txt << 'EOF'
file 'scene01.mp4'
file 'scene02.mp4'
file 'scene03.mp4'
EOF

# Lossless concat (same codec)
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final.mp4

# Re-encode if codecs differ
ffmpeg -y -f concat -safe 0 -i concat.txt \
  -c:v libx264 -crf 18 -c:a aac -b:a 192k final.mp4
```

## Common Pitfalls

1. **Edge TTS voice mismatch.** Default is `en-US-AriaNeural` (English/American). For Indonesian content, MUST change to `id-ID-ArdiNeural` in `~/.hermes/config.yaml`. Users will complain it "sounds like a foreigner."
2. **Narration longer than video.** Always check durations with `ffprobe -show_entries format=duration` and trim narration with `atrim` to fit.
3. **amix volume normalization.** `amix` normalizes by dividing by number of inputs. Use `volume` filter AFTER amix to compensate, or set `dropout_transition` to avoid sudden volume drops.
4. **TTS output format.** Edge TTS outputs `.ogg` regardless of requested extension. ffmpeg handles it fine for mixing.
