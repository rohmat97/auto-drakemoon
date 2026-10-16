"""
Generate full-screen game illustration for FORMATION_REGIONS in Battle/Rexd/ikan_tol/config.py.
Draws exact pixel bounds on a 1024x768 game canvas with side-by-side coordinate specs and visual legend.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
ARTIFACT_DIR = r'C:\Users\rd\.gemini\antigravity-ide\brain\8af236ec-3f0c-4e90-98aa-e84c92680291'

# Data directly from Battle/Rexd/ikan_tol/config.py
FORMATION_REGIONS = {
    'East': [(949, 140, 994, 257), (985, 437, 1002, 463)],
    'South': [(940, 461, 998, 497), (23, 494, 66, 558)],
    'West': [(13, 105, 33, 165), (14, 560, 48, 623)],
    'North': [(935, 100, 1004, 238), (31, 153, 117, 270)],
}

OPTIONAL_FORMATIONS = {
    'WestSouth': [(0, 600, 50, 674), (407, 642, 455, 670)],
    'NorthEast': [(803, 68, 864, 111), (803, 68, 864, 111)],
}

MONSTER_DIRECTION_REGIONS = {
    'East': (172, 713, 189, 722),
    'South': (117, 730, 136, 745),
    'West': (76, 714, 83, 728),
    'North': (121, 689, 136, 704),
}

OPPOSITE_REGION = (546, 101, 938, 294)
OPPOSITE_TARGET = (961, 100)

OPPOSITE_REGION_2 = (183, 93, 465, 374)
OPPOSITE_TARGET_2 = (139, 584)

COLORS = {
    'East': {'fill': (59, 130, 246, 60), 'stroke': '#3b82f6', 'text': '#60a5fa'},      # Blue
    'South': {'fill': (16, 185, 129, 60), 'stroke': '#10b981', 'text': '#34d399'},    # Green
    'West': {'fill': (245, 158, 11, 65), 'stroke': '#f59e0b', 'text': '#fbbf24'},     # Amber / Orange
    'North': {'fill': (239, 68, 68, 60), 'stroke': '#ef4444', 'text': '#f87171'},      # Red
    'WestSouth': {'fill': (139, 92, 246, 45), 'stroke': '#8b5cf6', 'text': '#a78bfa'},# Purple
    'NorthEast': {'fill': (20, 184, 166, 45), 'stroke': '#14b8a6', 'text': '#2dd4bf'},# Teal
}


def draw_dashed_line(draw, pt1, pt2, color, width=1, dash_len=5, gap_len=4):
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


def generate_diagram(output_paths):
    canvas_w, canvas_h = 1840, 1040
    img = Image.new('RGBA', (canvas_w, canvas_h), (11, 15, 23, 255))
    overlay = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))

    draw = ImageDraw.Draw(img)
    draw_ol = ImageDraw.Draw(overlay)

    # Fonts
    try:
        font_title = ImageFont.truetype('arialbd.ttf', 24)
        font_sub = ImageFont.truetype('arial.ttf', 13)
        font_h1 = ImageFont.truetype('arialbd.ttf', 16)
        font_h2 = ImageFont.truetype('arialbd.ttf', 13)
        font_body = ImageFont.truetype('arial.ttf', 12)
        font_mono = ImageFont.truetype('consola.ttf', 11)
        font_mono_bold = ImageFont.truetype('consolab.ttf', 11)
        font_small = ImageFont.truetype('arial.ttf', 10)
    except IOError:
        font_title = font_sub = font_h1 = font_h2 = font_body = font_mono = font_mono_bold = font_small = ImageFont.load_default()

    # Header
    draw.text((60, 20), "Gersang Full Screen Formation Regions Illustration", fill="#ffffff", font=font_title)
    draw.text((60, 52), "Visual coordinates of FORMATION_REGIONS from Battle/Rexd/ikan_tol/config.py on full 1024x768 game window", fill="#94a3b8", font=font_sub)

    # Game Canvas Offset
    ox, oy = 60, 120
    gw, gh = 1024, 768

    # Background screen rectangle
    draw.rectangle([ox, oy, ox + gw, oy + gh], fill=(17, 24, 39, 255), outline=(55, 65, 81, 255), width=2)

    # Screen dimensions badge (placed cleanly above ruler)
    draw.rectangle([ox, oy - 42, ox + 330, oy - 18], fill=(31, 41, 55, 255), outline=(75, 85, 99, 255), width=1)
    draw.text((ox + 10, oy - 38), "GAME CLIENT AREA: 1024 x 768 (Origin: 0, 0)", fill="#e5e7eb", font=font_h2)

    # Grid lines every 100px & ruler tick labels
    for x in range(0, 1025, 100):
        gx = ox + x
        draw.line([gx, oy, gx, oy + gh], fill=(31, 41, 55, 140), width=1)
        draw.line([gx, oy - 6, gx, oy], fill="#94a3b8", width=1)
        draw.text((gx - 9, oy - 16), str(x), fill="#94a3b8", font=font_small)

    for y in range(0, 769, 100):
        gy = oy + y
        draw.line([ox, gy, ox + gw, gy], fill=(31, 41, 55, 140), width=1)
        draw.line([ox - 6, gy, ox, gy], fill="#94a3b8", width=1)
        draw.text((ox - 28, gy - 6), str(y), fill="#94a3b8", font=font_small)

    # Screen Center Crosshair
    cx, cy = ox + 512, oy + 384
    draw_dashed_line(draw, (cx, oy), (cx, oy + gh), (75, 85, 99, 180), width=1, dash_len=4, gap_len=4)
    draw_dashed_line(draw, (ox, cy), (ox + gw, cy), (75, 85, 99, 180), width=1, dash_len=4, gap_len=4)
    draw.text((cx + 6, cy + 6), "Center (512, 384)", fill="#64748b", font=font_small)

    # Draw Formation Regions
    for direction, regions in FORMATION_REGIONS.items():
        cfg = COLORS.get(direction)
        r_centers = []

        for idx, (x1, y1, x2, y2) in enumerate(regions, start=1):
            px1, py1 = ox + x1, oy + y1
            px2, py2 = ox + x2, oy + y2
            w, h = x2 - x1, y2 - y1
            r_centers.append(((px1 + px2) // 2, (py1 + py2) // 2))

            # Translucent box fill
            draw_ol.rectangle([px1, py1, px2, py2], fill=cfg['fill'], outline=cfg['stroke'], width=2)

            # Label box
            label = f"{direction} #{idx} ({w}x{h})"
            tw = draw.textlength(label, font=font_small)
            
            # Smart placement for labels so they don't overlap or go offscreen
            if px1 < ox + 100:  # near left edge
                lx = px2 + 8
                ly = py1 + (h // 2) - 8
            elif px2 > ox + gw - 120:  # near right edge
                lx = px1 - tw - 10
                ly = py1 + (h // 2) - 8
            elif py1 < oy + 120:  # near top edge
                lx = px1
                ly = py2 + 6
            else:
                lx = px1
                ly = py1 - 18

            draw_ol.rectangle([lx - 4, ly - 2, lx + tw + 4, ly + 14], fill=(15, 23, 42, 240), outline=cfg['stroke'], width=1)
            draw.text((lx, ly), label, fill="#ffffff", font=font_small)

        # Connect pair with dashed indicator line
        if len(r_centers) == 2:
            draw_dashed_line(draw_ol, r_centers[0], r_centers[1], cfg['stroke'], width=1, dash_len=6, gap_len=5)

    # Draw Optional / Commented Formations with dashed outline
    for direction, regions in OPTIONAL_FORMATIONS.items():
        cfg = COLORS.get(direction)
        for idx, (x1, y1, x2, y2) in enumerate(regions, start=1):
            px1, py1 = ox + x1, oy + y1
            px2, py2 = ox + x2, oy + y2
            w, h = x2 - x1, y2 - y1
            # Outline
            draw_dashed_line(draw_ol, (px1, py1), (px2, py1), cfg['stroke'], width=1)
            draw_dashed_line(draw_ol, (px2, py1), (px2, py2), cfg['stroke'], width=1)
            draw_dashed_line(draw_ol, (px2, py2), (px1, py2), cfg['stroke'], width=1)
            draw_dashed_line(draw_ol, (px1, py2), (px1, py1), cfg['stroke'], width=1)
            draw_ol.rectangle([px1, py1, px2, py2], fill=(cfg['fill'][0], cfg['fill'][1], cfg['fill'][2], 25))

    # Minimap HUD Zone (Bottom Left: ~70, 680 to 200, 760)
    mm_x1, mm_y1 = ox + 70, oy + 680
    mm_x2, mm_y2 = ox + 200, oy + 760
    draw_ol.rectangle([mm_x1, mm_y1, mm_x2, mm_y2], fill=(255, 255, 255, 12), outline="#64748b", width=1)
    draw.text((mm_x1 + 6, mm_y1 + 4), "Minimap Area (70..200, 680..760)", fill="#94a3b8", font=font_small)

    for direction, (mx1, my1, mx2, my2) in MONSTER_DIRECTION_REGIONS.items():
        cfg = COLORS.get(direction)
        draw_ol.rectangle([ox + mx1, oy + my1, ox + mx2, oy + my2], fill=cfg['stroke'], outline="#ffffff", width=1)

    # Opposite Monster Search Region 1 (546, 101, 938, 294)
    opp_x1, opp_y1 = ox + OPPOSITE_REGION[0], oy + OPPOSITE_REGION[1]
    opp_x2, opp_y2 = ox + OPPOSITE_REGION[2], oy + OPPOSITE_REGION[3]
    draw_ol.rectangle([opp_x1, opp_y1, opp_x2, opp_y2], fill=(236, 72, 153, 30), outline="#ec4899", width=2)
    draw.text((opp_x1 + 10, opp_y1 + 10), "Opposite 1: (546, 101) to (938, 294) [392x193]", fill="#f472b6", font=font_h2)

    # Opposite Target Cursor 1 (961, 100)
    tx, ty = ox + OPPOSITE_TARGET[0], oy + OPPOSITE_TARGET[1]
    draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill="#e11d48", outline="#ffffff", width=2)
    draw.line([tx - 12, ty, tx + 12, ty], fill="#e11d48", width=2)
    draw.line([tx, ty - 12, tx, ty + 12], fill="#e11d48", width=2)
    draw.text((tx - 120, ty - 16), "Target 1: (961, 100)", fill="#fda4af", font=font_small)

    # Opposite Monster Search Region 2 (183, 93, 465, 374)
    opp2_x1, opp2_y1 = ox + OPPOSITE_REGION_2[0], oy + OPPOSITE_REGION_2[1]
    opp2_x2, opp2_y2 = ox + OPPOSITE_REGION_2[2], oy + OPPOSITE_REGION_2[3]
    draw_ol.rectangle([opp2_x1, opp2_y1, opp2_x2, opp2_y2], fill=(168, 85, 247, 30), outline="#a855f7", width=2)
    draw.text((opp2_x1 + 10, opp2_y1 + 10), "Opposite 2: (183, 93) to (465, 374) [282x281]", fill="#c084fc", font=font_h2)

    # Opposite Target Cursor 2 (139, 584)
    tx2, ty2 = ox + OPPOSITE_TARGET_2[0], oy + OPPOSITE_TARGET_2[1]
    draw.ellipse([tx2 - 6, ty2 - 6, tx2 + 6, ty2 + 6], fill="#a855f7", outline="#ffffff", width=2)
    draw.line([tx2 - 12, ty2, tx2 + 12, ty2], fill="#a855f7", width=2)
    draw.line([tx2, ty2 - 12, tx2, ty2 + 12], fill="#a855f7", width=2)
    draw.text((tx2 + 12, ty2 - 6), "Target 2: (139, 584)", fill="#d8b4fe", font=font_small)

    # Side Panel (Offset x=1120)
    sx = 1120
    sy = 120
    sw = 660
    sh = 768

    draw.rectangle([sx, sy, sx + sw, sy + sh], fill=(17, 24, 39, 255), outline=(55, 65, 81, 255), width=2)

    # Panel Title (placed cleanly above panel top)
    draw.rectangle([sx, sy - 42, sx + 280, sy - 18], fill=(31, 41, 55, 255), outline=(75, 85, 99, 255), width=1)
    draw.text((sx + 10, sy - 38), "COORDINATE SPECIFICATIONS", fill="#e5e7eb", font=font_h2)

    # Sub-header
    curr_y = sy + 20
    draw.text((sx + 20, curr_y), "Formation Detection Logic (check_formation)", fill="#ffffff", font=font_h1)
    curr_y += 24
    draw.text((sx + 20, curr_y), "dm.FindPic checks for black boundary/marker (080808.bmp) in BOTH Region 1 and Region 2.", fill="#94a3b8", font=font_body)
    curr_y += 18
    draw.text((sx + 20, curr_y), "If x1 > 0 AND x2 > 0 simultaneously -> formation position is confirmed.", fill="#38bdf8", font=font_body)
    curr_y += 30

    # Table Header
    draw.rectangle([sx + 20, curr_y, sx + sw - 20, curr_y + 28], fill=(31, 41, 55, 255))
    draw.text((sx + 30, curr_y + 7), "Direction", fill="#e5e7eb", font=font_h2)
    draw.text((sx + 120, curr_y + 7), "Region 1 (x1, y1)-(x2, y2) [WxH]", fill="#e5e7eb", font=font_h2)
    draw.text((sx + 380, curr_y + 7), "Region 2 (x1, y1)-(x2, y2) [WxH]", fill="#e5e7eb", font=font_h2)
    curr_y += 35

    # Active Formations
    for direction, regions in FORMATION_REGIONS.items():
        cfg = COLORS.get(direction)
        r1, r2 = regions[0], regions[1]
        w1, h1 = r1[2] - r1[0], r1[3] - r1[1]
        w2, h2 = r2[2] - r2[0], r2[3] - r2[1]

        # Row background
        draw.rectangle([sx + 20, curr_y, sx + sw - 20, curr_y + 46], fill=(23, 32, 51, 160), outline=(55, 65, 81, 120), width=1)

        # Direction badge
        draw.rectangle([sx + 28, curr_y + 10, sx + 100, curr_y + 36], fill=cfg['fill'], outline=cfg['stroke'], width=1)
        draw.text((sx + 36, curr_y + 14), direction, fill=cfg['text'], font=font_h2)

        # Region 1 specs
        draw.text((sx + 120, curr_y + 8), f"({r1[0]}, {r1[1]}) to ({r1[2]}, {r1[3]})", fill="#f3f4f6", font=font_mono_bold)
        draw.text((sx + 120, curr_y + 26), f"Width: {w1}px  |  Height: {h1}px", fill="#9ca3af", font=font_small)

        # Region 2 specs
        draw.text((sx + 380, curr_y + 8), f"({r2[0]}, {r2[1]}) to ({r2[2]}, {r2[3]})", fill="#f3f4f6", font=font_mono_bold)
        draw.text((sx + 380, curr_y + 26), f"Width: {w2}px  |  Height: {h2}px", fill="#9ca3af", font=font_small)

        curr_y += 52

    curr_y += 10
    # Optional / Commented section
    draw.text((sx + 20, curr_y), "Optional / Commented Formations in config.py:", fill="#a78bfa", font=font_h2)
    curr_y += 24
    for direction, regions in OPTIONAL_FORMATIONS.items():
        cfg = COLORS.get(direction)
        r1, r2 = regions[0], regions[1]
        w1, h1 = r1[2] - r1[0], r1[3] - r1[1]
        w2, h2 = r2[2] - r2[0], r2[3] - r2[1]

        draw.rectangle([sx + 20, curr_y, sx + sw - 20, curr_y + 40], fill=(20, 27, 45, 120), outline=(55, 65, 81, 80), width=1)
        draw.text((sx + 30, curr_y + 12), f"{direction} (Inactive)", fill="#9ca3af", font=font_mono_bold)
        draw.text((sx + 180, curr_y + 12), f"R1: ({r1[0]},{r1[1]})-({r1[2]},{r1[3]}) [{w1}x{h1}]", fill="#6b7280", font=font_mono)
        draw.text((sx + 410, curr_y + 12), f"R2: ({r2[0]},{r2[1]})-({r2[2]},{r2[3]}) [{w2}x{h2}]", fill="#6b7280", font=font_mono)
        curr_y += 46

    curr_y += 15
    # Minimap scan summary
    draw.text((sx + 20, curr_y), "Minimap Monster Dot Scan (MONSTER_DIRECTION_REGIONS):", fill="#ffffff", font=font_h2)
    curr_y += 24
    for idx, (direction, reg) in enumerate(MONSTER_DIRECTION_REGIONS.items()):
        cfg = COLORS.get(direction)
        col_x = sx + 20 + (idx % 2) * 320
        col_y = curr_y + (idx // 2) * 26
        draw.rectangle([col_x, col_y + 2, col_x + 12, col_y + 14], fill=cfg['stroke'])
        draw.text((col_x + 18, col_y), f"{direction:<6}: ({reg[0]}, {reg[1]}) to ({reg[2]}, {reg[3]}) [{reg[2]-reg[0]}x{reg[3]-reg[1]}]", fill="#e5e7eb", font=font_mono)

    curr_y += 50
    # Opposite direction summary
    draw.rectangle([sx + 20, curr_y, sx + sw - 20, curr_y + 80], fill=(236, 72, 153, 20), outline="#ec4899", width=1)
    draw.text((sx + 30, curr_y + 8), "Opposite Monster Search Conditions (Drake.py):", fill="#f472b6", font=font_h2)
    draw.text((sx + 30, curr_y + 26), f"Cond 1: Area {OPPOSITE_REGION} (392x193) -> Target: {OPPOSITE_TARGET}", fill="#fbcfe8", font=font_mono)
    draw.text((sx + 30, curr_y + 44), f"Cond 2: Area {OPPOSITE_REGION_2} (282x281) -> Target: {OPPOSITE_TARGET_2}", fill="#e9d5ff", font=font_mono)
    draw.text((sx + 30, curr_y + 62), "Triggered when formation minimap dots are absent; casts prep aura + skill loop.", fill="#94a3b8", font=font_small)

    # Merge overlay
    img = Image.alpha_composite(img, overlay)

    # Save to all requested paths
    for p in output_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        img.convert('RGB').save(p, 'PNG')
        print(f"Saved illustration to: {p}")


if __name__ == '__main__':
    local_path = os.path.join(_SCRIPT_DIR, 'formation_regions_illustration.png')
    artifact_path = os.path.join(ARTIFACT_DIR, 'formation_regions_illustration.png')
    generate_diagram([local_path, artifact_path])
