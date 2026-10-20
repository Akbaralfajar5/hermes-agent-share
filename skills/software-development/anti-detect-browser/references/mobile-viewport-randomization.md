# Mobile Viewport Randomization for Anti-Detection

When running multiple browser workers, NEVER use the same viewport. Randomize from 25+ real device profiles.

## Device Pool (25 devices)

### iPhones (13)
| Device | Width | Height | DPR |
|--------|-------|--------|-----|
| iPhone SE 3 | 375 | 667 | 2 |
| iPhone 12 | 390 | 844 | 3 |
| iPhone 12 Mini | 360 | 780 | 3 |
| iPhone 13 | 390 | 844 | 3 |
| iPhone 13 Pro | 390 | 844 | 3 |
| iPhone 13 Pro Max | 428 | 926 | 3 |
| iPhone 14 | 390 | 844 | 3 |
| iPhone 14 Plus | 428 | 926 | 3 |
| iPhone 14 Pro | 393 | 852 | 3 |
| iPhone 14 Pro Max | 430 | 932 | 3 |
| iPhone 15 | 393 | 852 | 3 |
| iPhone 15 Pro | 393 | 852 | 3 |
| iPhone 15 Pro Max | 430 | 932 | 3 |

### Samsung (6)
| Device | Width | Height | DPR |
|--------|-------|--------|-----|
| Galaxy S21 | 360 | 800 | 3 |
| Galaxy S22 | 360 | 780 | 3 |
| Galaxy S23 | 360 | 780 | 3 |
| Galaxy S24 | 360 | 780 | 3 |
| Galaxy A54 | 412 | 915 | 2.625 |
| Galaxy A34 | 412 | 915 | 2.625 |

### Xiaomi (3)
| Device | Width | Height | DPR |
|--------|-------|--------|-----|
| Redmi Note 12 | 393 | 873 | 2.75 |
| Xiaomi 13 | 393 | 873 | 2.75 |
| Poco F5 | 393 | 873 | 2.75 |

### Others (3)
| Device | Width | Height | DPR |
|--------|-------|--------|-----|
| Oppo Reno 8 | 412 | 915 | 2.625 |
| Vivo V27 | 412 | 915 | 2.625 |
| Google Pixel 7 | 412 | 915 | 2.625 |

## Python Implementation

```python
import random

MOBILE_VIEWPORTS = [
    {'name': 'iPhone SE 3',          'width': 375, 'height': 667,  'dpr': 2},
    {'name': 'iPhone 12',            'width': 390, 'height': 844,  'dpr': 3},
    {'name': 'iPhone 12 Mini',       'width': 360, 'height': 780,  'dpr': 3},
    {'name': 'iPhone 13',            'width': 390, 'height': 844,  'dpr': 3},
    {'name': 'iPhone 13 Pro',        'width': 390, 'height': 844,  'dpr': 3},
    {'name': 'iPhone 13 Pro Max',    'width': 428, 'height': 926,  'dpr': 3},
    {'name': 'iPhone 14',            'width': 390, 'height': 844,  'dpr': 3},
    {'name': 'iPhone 14 Plus',       'width': 428, 'height': 926,  'dpr': 3},
    {'name': 'iPhone 14 Pro',        'width': 393, 'height': 852,  'dpr': 3},
    {'name': 'iPhone 14 Pro Max',    'width': 430, 'height': 932,  'dpr': 3},
    {'name': 'iPhone 15',            'width': 393, 'height': 852,  'dpr': 3},
    {'name': 'iPhone 15 Pro',        'width': 393, 'height': 852,  'dpr': 3},
    {'name': 'iPhone 15 Pro Max',    'width': 430, 'height': 932,  'dpr': 3},
    {'name': 'Samsung Galaxy S21',   'width': 360, 'height': 800,  'dpr': 3},
    {'name': 'Samsung Galaxy S22',   'width': 360, 'height': 780,  'dpr': 3},
    {'name': 'Samsung Galaxy S23',   'width': 360, 'height': 780,  'dpr': 3},
    {'name': 'Samsung Galaxy S24',   'width': 360, 'height': 780,  'dpr': 3},
    {'name': 'Samsung Galaxy A54',   'width': 412, 'height': 915,  'dpr': 2.625},
    {'name': 'Samsung Galaxy A34',   'width': 412, 'height': 915,  'dpr': 2.625},
    {'name': 'Xiaomi Redmi Note 12', 'width': 393, 'height': 873,  'dpr': 2.75},
    {'name': 'Xiaomi 13',            'width': 393, 'height': 873,  'dpr': 2.75},
    {'name': 'Xiaomi Poco F5',       'width': 393, 'height': 873,  'dpr': 2.75},
    {'name': 'Oppo Reno 8',          'width': 412, 'height': 915,  'dpr': 2.625},
    {'name': 'Vivo V27',             'width': 412, 'height': 915,  'dpr': 2.625},
    {'name': 'Google Pixel 7',       'width': 412, 'height': 915,  'dpr': 2.625},
]

def pick_random_viewport():
    return random.choice(MOBILE_VIEWPORTS)
```

## Touch Event Injection

Simulate mobile touch events for sites that check touch support:

```javascript
() => {
    const origClick = HTMLElement.prototype.click;
    HTMLElement.prototype.click = function() {
        const touch = new Touch({
            identifier: Date.now(),
            target: this,
            clientX: this.getBoundingClientRect().x + this.offsetWidth/2,
            clientY: this.getBoundingClientRect().y + this.offsetHeight/2,
            radiusX: 2.5, radiusY: 2.5, rotationAngle: 10, force: 0.5,
        });
        this.dispatchEvent(new TouchEvent('touchstart', {
            cancelable: true, bubbles: true, touches: [touch],
            targetTouches: [touch], changedTouches: [touch]
        }));
        this.dispatchEvent(new TouchEvent('touchend', {
            cancelable: true, bubbles: true, touches: [],
            targetTouches: [], changedTouches: [touch]
        }));
        return origClick.call(this);
    };
}
```

## Why This Works

Sites fingerprint browsers via:
1. **Viewport dimensions** — if all workers have 414x896, they're linked
2. **DPR (device pixel ratio)** — matching DPR + viewport = same device
3. **Touch support** — mobile sites check `TouchEvent` constructor
4. **Window vs viewport** — window should be viewport + 6-40px (browser chrome)

By randomizing across 25 real devices, each worker appears as a different physical phone.
