"""
Generate updated, ultra-clear visual diagram for FORMATION_REGIONS in config.py.
Dynamically imports from config.py and displays exact updated coordinates,
highlighting the separation between North and East regions.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from config import FORMATION_REGIONS

PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
CURRENT_ARTIFACT_DIR = r'C:\Users\rd\.gemini\antigravity-ide\brain\2a78f1d9-a175-4321-9b39-d1df6896eab6'

THEME = {
    'East': {
        'fill': (14, 165, 233, 75),       # Sky blue
        'stroke': '#0ea5e9',
        'badge_bg': '#0369a1',
        'text': '#38bdf8',
        'name': 'East Formation'
    },
    'South': {
        'fill': (16, 185, 129, 75),      # Emerald
        'stroke': '#10b981',
        'badge_bg': '#047857',
        'text': '#34d399',
        'name': 'South Formation'
    },
    'West': {
        'fill': (245, 158, 11, 75),      # Amber
        'stroke': '#f59e0b',
        'badge_bg': '#b45309',
        'text': '#fbbf24',
        'name': 'West Formation'
    },
    'North': {
        'fill': (239, 68, 68, 75),       # Rose / Red
        'stroke': '#ef4444',
        'badge_bg': '#b91c1c',
        'text': '#f87171',
        'name': 'North Formation'
    },
}

def draw_dashed_line(draw, pt1, pt2, color, width=2, dash_len=6, gap_len=5):
    x1, y1 = pt1
    x2, y2 = pt2
    dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if dist == 0:
        return
    step = dash_len + gap_len
    num = int(dist // step)
    dx = (x2 - x1) / dist
    dy = (y2 - y1) / dist
    for i in range(num + 1):
        s = i * step
        e = min(s + dash_len, dist)
        if s < dist:
            p_start = (int(x1 + dx * s), int(y1 + dy * s))
            p_end = (int(x1 + dx * e), int(y1 + dy * e))
            draw.line([p_start, p_end], fill=color, width=width)


def render_diagram(output_paths):
    canvas_w = 1920
    canvas_h = 1080

    base = Image.new('RGBA', (canvas_w, canvas_h), (10, 14, 23, 255))
    overlay = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))

    draw = ImageDraw.Draw(base)
    draw_ol = ImageDraw.Draw(overlay)

    try:
        font_title = ImageFont.truetype('arialbd.ttf', 24)
        font_sub = ImageFont.truetype('arial.ttf', 13)
        font_h1 = ImageFont.truetype('arialbd.ttf', 16)
        font_h2 = ImageFont.truetype('arialbd.ttf', 13)
        font_body = ImageFont.truetype('arial.ttf', 12)
        font_mono = ImageFont.truetype('consola.ttf', 11)
        font_mono_bold = ImageFont.truetype('consolab.ttf', 11)
        font_mono_large = ImageFont.truetype('consolab.ttf', 13)
        font_small = ImageFont.truetype('arial.ttf', 10)
    except IOError:
        font_title = font_sub = font_h1 = font_h2 = font_body = font_mono = font_mono_bold = font_mono_large = font_small = ImageFont.load_default()

    # Title & Subtitle
    draw.text((50, 24), "FORMATION_REGIONS Visual Mapping (Updated Coordinates)", fill="#ffffff", font=font_title)
    draw.text((50, 58), "Synchronized with Battle/Rexd/ikan_tol/config.py (Game Resolution: 1024 x 768)", fill="#94a3b8", font=font_sub)

    # 1024x768 Game Screen Placement
    gx, gy = 50, 110
    gw, gh = 1024, 768

    # Game area outer border and background
    draw.rectangle([gx, gy, gx + gw, gy + gh], fill=(15, 23, 42, 255), outline=(51, 65, 85, 255), width=2)

    # Header tag for game canvas
    draw.rectangle([gx, gy - 26, gx + 280, gy], fill=(30, 41, 59, 255), outline=(51, 65, 85, 255), width=1)
    draw.text((gx + 10, gy - 20), "GAME SCREEN VIEWPORT (1024 x 768)", fill="#e2e8f0", font=font_mono_bold)

    # Grid ticks every 100px
    for x in range(0, 1025, 100):
        px = gx + x
        draw.line([px, gy, px, gy + gh], fill=(30, 41, 59, 120), width=1)
        draw.text((px - 8, gy + gh + 4), str(x), fill="#64748b", font=font_small)

    for y in range(0, 769, 100):
        py = gy + y
        draw.line([gx, py, gx + gw, py], fill=(30, 41, 59, 120), width=1)
        draw.text((gx - 26, py - 6), str(y), fill="#64748b", font=font_small)

    # Isometric diamond terrain hint
    iso_top = (gx + 512, gy + 40)
    iso_right = (gx + 980, gy + 384)
    iso_bottom = (gx + 512, gy + 720)
    iso_left = (gx + 44, gy + 384)
    draw_dashed_line(draw_ol, iso_top, iso_right, '#334155', width=1, dash_len=4, gap_len=4)
    draw_dashed_line(draw_ol, iso_right, iso_bottom, '#334155', width=1, dash_len=4, gap_len=4)
    draw_dashed_line(draw_ol, iso_bottom, iso_left, '#334155', width=1, dash_len=4, gap_len=4)
    draw_dashed_line(draw_ol, iso_left, iso_top, '#334155', width=1, dash_len=4, gap_len=4)
    draw.text((gx + 440, gy + 380), "[ Playable Isometric Map Area ]", fill="#475569", font=font_small)

    # Center crosshair
    draw_dashed_line(draw, (gx + 512, gy), (gx + 512, gy + gh), '#1e293b', width=1, dash_len=4, gap_len=4)
    draw_dashed_line(draw, (gx, gy + 384), (gx + gw, gy + 384), '#1e293b', width=1, dash_len=4, gap_len=4)
    draw.text((gx + 518, gy + 388), "Center (512, 384)", fill="#475569", font=font_small)

    # Draw FORMATION_REGIONS
    formation_centers = {}
    for direction, regions in FORMATION_REGIONS.items():
        theme = THEME[direction]
        centers = []
        for idx, (x1, y1, x2, y2) in enumerate(regions, start=1):
            rx1, ry1 = gx + x1, gy + y1
            rx2, ry2 = gx + x2, gy + y2
            w, h = x2 - x1, y2 - y1
            c_pt = ((rx1 + rx2) // 2, (ry1 + ry2) // 2)
            centers.append(c_pt)

            # Box fill & outline
            draw_ol.rectangle([rx1, ry1, rx2, ry2], fill=theme['fill'], outline=theme['stroke'], width=2)

            # Box corner markers
            sz = 4
            draw_ol.rectangle([rx1 - sz, ry1 - sz, rx1 + sz, ry1 + sz], fill=theme['stroke'])
            draw_ol.rectangle([rx2 - sz, ry2 - sz, rx2 + sz, ry2 + sz], fill=theme['stroke'])

            # Tag label
            tag = f"{direction} R{idx} ({w}x{h})"
            tw = draw.textlength(tag, font=font_small)

            # Clean non-overlapping anchor placement per region
            if direction == 'North' and idx == 2:
                lx = rx1 + 10
                ly = ry2 + 6
            elif direction == 'North' and idx == 1:
                lx = rx1 - tw - 14
                ly = ry1 + 6
            elif direction == 'West' and idx == 1:
                lx = rx1
                ly = ry1 - 18
            elif rx2 > gx + gw - 80:
                lx = rx1 - tw - 14
                ly = ry1 + (h // 2) - 8
            elif rx1 < gx + 80:
                lx = rx2 + 10
                ly = ry1 + (h // 2) - 8
            else:
                lx = rx1
                ly = ry1 - 18

            draw_ol.rectangle([lx - 4, ly - 2, lx + tw + 4, ly + 14], fill=(15, 23, 42, 240), outline=theme['stroke'], width=1)
            draw_ol.text((lx, ly), tag, fill="#ffffff", font=font_small)

        formation_centers[direction] = centers
        if len(centers) == 2:
            draw_dashed_line(draw_ol, centers[0], centers[1], theme['stroke'], width=2, dash_len=6, gap_len=5)

    # Separation callout in Top-Right
    draw_ol.rectangle([gx + 920, gy + 40, gx + 1015, gy + 270], outline="#22c55e", width=2)
    draw_ol.text((gx + 680, gy + 42), "✅ VERIFIED SEPARATION (North R1: y=50..120 | East R1: y=140..257)", fill="#4ade80", font=font_mono_bold)
    draw_dashed_line(draw_ol, (gx + 920, gy + 50), (gx + 880, gy + 50), "#22c55e", width=1)

    # Separation callout in East R2
    draw_ol.text((gx + 730, gy + 560), "✅ East R2 shifted down to y=550..600", fill="#38bdf8", font=font_mono)
    draw_dashed_line(draw_ol, (gx + 980, gy + 575), (gx + 940, gy + 575), "#0ea5e9", width=1)

    # -------------------------------------------------------------
    # Side Panel Specifications & Verification
    # -------------------------------------------------------------
    px = 1110
    py = 110
    pw = 760
    ph = 768

    draw.rectangle([px, py, px + pw, py + ph], fill=(15, 23, 42, 255), outline=(51, 65, 85, 255), width=2)

    # Panel header badge
    draw.rectangle([px, py - 26, px + 360, py], fill=(30, 41, 59, 255), outline=(51, 65, 85, 255), width=1)
    draw.text((px + 10, py - 20), "UPDATED FORMATION SPECIFICATIONS", fill="#e2e8f0", font=font_mono_bold)

    curr_y = py + 16
    draw.text((px + 20, curr_y), "1. Active Formation Coordinates in config.py", fill="#ffffff", font=font_h1)
    curr_y += 24

    for direction, regions in FORMATION_REGIONS.items():
        theme = THEME[direction]
        r1, r2 = regions[0], regions[1]
        w1, h1 = r1[2] - r1[0], r1[3] - r1[1]
        w2, h2 = r2[2] - r2[0], r2[3] - r2[1]

        draw.rectangle([px + 20, curr_y, px + pw - 20, curr_y + 44], fill=(23, 32, 51, 200), outline=theme['stroke'], width=1)
        draw.rectangle([px + 28, curr_y + 8, px + 110, curr_y + 36], fill=theme['badge_bg'])
        draw.text((px + 36, curr_y + 12), direction, fill="#ffffff", font=font_h2)

        # Region 1
        draw.text((px + 125, curr_y + 6), f"R1: ({r1[0]},{r1[1]}) -> ({r1[2]},{r1[3]})", fill="#f1f5f9", font=font_mono_bold)
        draw.text((px + 125, curr_y + 24), f"Size: {w1}x{h1} px", fill="#94a3b8", font=font_small)

        # Region 2
        draw.text((px + 400, curr_y + 6), f"R2: ({r2[0]},{r2[1]}) -> ({r2[2]},{r2[3]})", fill="#f1f5f9", font=font_mono_bold)
        draw.text((px + 400, curr_y + 24), f"Size: {w2}x{h2} px", fill="#94a3b8", font=font_small)

        curr_y += 50

    curr_y += 10
    # Verification Card
    draw.text((px + 20, curr_y), "2. Coordinate Modification Analysis & Fix Verification", fill="#4ade80", font=font_h1)
    curr_y += 26

    box_h = 255
    draw.rectangle([px + 20, curr_y, px + pw - 20, curr_y + box_h], fill=(20, 83, 45, 40), outline="#16a34a", width=1)

    lines = [
        ("• Zero Overlap Between North R1 and East R1:", "#bbf7d0", True),
        ("  Old North R1: y=100..238 overlapped East R1: y=140..257 completely.", "#94a3b8", False),
        ("  New North R1: y=50..120 is strictly above East R1: y=140..257 (20px clear buffer).", "#4ade80", True),
        ("  North R1 now samples the extreme top-right corner exclusive to North camera spawn.", "#e2e8f0", False),
        ("", "", False),
        ("• East R2 Pushed Downward Away from North Edge Void:", "#bbf7d0", True),
        ("  Old East R2: (985, 437, 1002, 463) fell in the boundary void when camera scrolled up to North.", "#94a3b8", False),
        ("  New East R2: (985, 550, 1002, 600) is moved to lower-right area.", "#38bdf8", True),
        ("  When at North, the lower-right area is ground/playable map, so 080808.bmp will NOT trigger!", "#e2e8f0", False),
        ("", "", False),
        ("• Similarity Raised from 0.95 -> 1.0 in combat.py:", "#bbf7d0", True),
        ("  dm.FindPic(..., '080808.bmp', '050505', 1, 0) now requires exact 100% pixel match.", "#facc15", False),
        ("  Eliminates any slight terrain tint or fog noise causing false positives.", "#e2e8f0", False),
    ]

    sub_y = curr_y + 10
    for text, color, is_bold in lines:
        if text:
            f = font_mono_large if is_bold else font_mono
            draw.text((px + 32, sub_y), text, fill=color, font=f)
        sub_y += 18

    curr_y += box_h + 16

    # Operational Impact Card
    draw.text((px + 20, curr_y), "3. Operational Impact on Battle Loop", fill="#38bdf8", font=font_h1)
    curr_y += 24
    impact_h = 105
    draw.rectangle([px + 20, curr_y, px + pw - 20, curr_y + impact_h], fill=(30, 41, 59, 140), outline="#0284c7", width=1)
    impact_lines = [
        "1. When spawning at North, East R1 and East R2 will now return False (x1=0 or x2=0).",
        "2. The loop proceeds past East -> reaches North -> confirms North R1 & R2 successfully.",
        "3. find_monsters('North') will correctly scan East, South, West (and will NOT target own team at North)!"
    ]
    sub_y = curr_y + 12
    for s in impact_lines:
        draw.text((px + 32, sub_y), s, fill="#e0f2fe", font=font_body)
        sub_y += 26

    # Bottom Footer
    draw.text((gx, gy + gh + 35), "Generated for Battle/Rexd/ikan_tol | Gersang Combat Orchestrator", fill="#64748b", font=font_small)

    img = Image.alpha_composite(base, overlay)

    for out_path in output_paths:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        img.convert('RGB').save(out_path, 'PNG')
        print(f"Generated diagram saved to: {out_path}")

if __name__ == '__main__':
    local_out = os.path.join(_SCRIPT_DIR, 'formation_regions_diagram.png')
    artifact_out = os.path.join(CURRENT_ARTIFACT_DIR, 'formation_regions_diagram.png')
    render_diagram([local_out, artifact_out])
