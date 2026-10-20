# Simplified Excalidraw Generator (Python)

For batch wireframe/storyboard generation, use standalone elements without container binding.

## Helper Functions

```python
import json

counter = 0

def make_id():
    global counter
    counter += 1
    return f"elem_{counter:04d}"

def rect(x, y, w, h, bg_color="transparent", stroke="#1e1e1e", rounded=True):
    elem_id = make_id()
    r = {
        "type": "rectangle", "id": elem_id,
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": bg_color,
        "fillStyle": "solid", "strokeWidth": 2, "roughness": 1,
        "opacity": 100, "angle": 0, "seed": hash(elem_id) % 100000,
        "version": 1, "isDeleted": False, "boundElements": [],
        "link": None, "locked": False,
    }
    if rounded:
        r["roundness"] = {"type": 3}
    return r

def text(x, y, content, font_size=20, align="center"):
    elem_id = make_id()
    return {
        "type": "text", "id": elem_id,
        "x": x, "y": y,
        "width": len(content) * font_size * 0.55,
        "height": font_size * 1.4,
        "text": content, "fontSize": font_size, "fontFamily": 1,
        "textAlign": align, "verticalAlign": "top",
        "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "roughness": 1,
        "opacity": 100, "angle": 0, "seed": hash(elem_id) % 100000,
        "version": 1, "isDeleted": False, "boundElements": None,
        "link": None, "locked": False,
        "originalText": content, "autoResize": True,
    }

def arrow(x1, y1, x2, y2):
    elem_id = make_id()
    dx, dy = x2 - x1, y2 - y1
    return {
        "type": "arrow", "id": elem_id,
        "x": x1, "y": y1,
        "width": abs(dx), "height": abs(dy),
        "points": [[0, 0], [dx, dy]],
        "endArrowhead": "arrow", "startArrowhead": None,
        "strokeColor": "#1e1e1e", "strokeWidth": 2, "roughness": 1,
        "opacity": 100, "angle": 0, "seed": hash(elem_id) % 100000,
        "version": 1, "isDeleted": False, "boundElements": [],
        "link": None, "locked": False,
    }
```

## Saving

```python
data = {
    "type": "excalidraw",
    "version": 2,
    "source": "hermes-agent",
    "elements": elements_list,
    "appState": {"viewBackgroundColor": "#ffffff"}
}
with open('output.excalidraw', 'w') as f:
    json.dump(data, f, indent=2)
```

## Wireframe Conventions

- **Browser frame**: `rect(50, 60, 500, 750, stroke="#495057")` — dark border
- **URL bar**: `rect(60, 65, 480, 30, bg_color="#f1f3f5")` — light gray
- **Navbar**: `rect(60, 100, 480, 50, bg_color="#e9ecef")` — medium gray
- **Image placeholder**: `rect(x, y, w, h, bg_color="#dee2e6")` + `text(x, y, "[Foto]")`
- **CTA button**: `rect(x, y, w, h, bg_color="#339af0")` (blue) or `"#25a244"` (green)
- **Annotations**: `text(580, y, "← Label", font_size=14)` — right side, red-ish

## Pitfalls

1. **Don't use emoji** in text elements — Excalidraw's Virgil font doesn't render them
2. **Width estimation** for text: `len(content) * fontSize * 0.55` is approximate
3. **Arrow helper returns single element**, not a list — unlike the multi-element pattern for labeled arrows
4. **Reset counter** between files if generating multiple .excalidraw files in one script, or use a class-based approach
