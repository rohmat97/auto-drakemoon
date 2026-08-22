import os
from PIL import Image, ImageDraw, ImageFont

artifact_dir = r'C:\Users\rd\.gemini\antigravity-ide\brain\d9d94d3e-2099-4f79-9e1d-13087953fe8d'
os.makedirs(artifact_dir, exist_ok=True)
out_png = os.path.join(artifact_dir, 'coordinate_blueprint.png')

W, H = 1600, 960
img = Image.new('RGBA', (W, H), (15, 18, 26, 255))
overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))

draw = ImageDraw.Draw(img)
draw_ol = ImageDraw.Draw(overlay)

try:
    font_title = ImageFont.truetype('arial.ttf', 26)
    font_sub = ImageFont.truetype('arial.ttf', 14)
    font_header = ImageFont.truetype('arial.ttf', 16)
    font_body = ImageFont.truetype('arial.ttf', 12)
    font_code = ImageFont.truetype('consola.ttf', 12)
    font_bold = ImageFont.truetype('arialbd.ttf', 13)
    font_small = ImageFont.truetype('arial.ttf', 10)
except IOError:
    font_title = font_sub = font_header = font_body = font_code = font_bold = font_small = ImageFont.load_default()

draw.text((40, 20), 'Gersang 1024x768 Screen Coordinate Blueprint', fill='#ffffff', font=font_title)
draw.text((40, 56), 'Exact pixel coordinate mapping for Food Detection, System Popups, and Overworld HUD regions', fill='#94a3b8', font=font_sub)

ox, oy = 60, 130
gw, gh = 1024, 768

draw.rectangle([ox, oy, ox + gw, oy + gh], fill=(22, 27, 38, 255), outline=(51, 65, 85, 255), width=2)
draw.text((ox, oy - 26), 'Game Client Area (Width: 1024px, Height: 768px)  —  Origin (0,0) at Top-Left', fill='#cbd5e1', font=font_header)

for x in range(0, 1025, 100):
    gx = ox + x
    draw.line([gx, oy, gx, oy + gh], fill=(30, 41, 59, 120), width=1)
    draw.line([gx, oy - 6, gx, oy], fill='#64748b', width=1)
    draw.text((gx - 10, oy - 18), str(x), fill='#64748b', font=font_small)

for y in range(0, 769, 100):
    gy = oy + y
    draw.line([ox, gy, ox + gw, gy], fill=(30, 41, 59, 120), width=1)
    draw.line([ox - 6, gy, ox, gy], fill='#64748b', width=1)
    draw.text((ox - 30, gy - 6), str(y), fill='#64748b', font=font_small)

# 1. Overworld Monster Area
mx1, my1, mx2, my2 = 96, 84, 964, 600
draw_ol.rectangle([ox + mx1, oy + my1, ox + mx2, oy + my2], fill=(59, 130, 246, 15), outline=(59, 130, 246, 80), width=1)
draw.text((ox + mx1 + 8, oy + my1 + 6), 'Monster Search Area (96, 84) - (964, 600)', fill='#60a5fa', font=font_small)

# 2. Mercenary Left Sidebar
draw_ol.rectangle([ox, oy, ox + 120, oy + 700], fill=(168, 85, 247, 25), outline=(168, 85, 247, 180), width=1)
draw.text((ox + 5, oy + 10), 'Mercenaries (0,0)-(120,700)', fill='#c084fc', font=font_small)

# 3. Bread Satiety HUD
draw_ol.rectangle([ox + 43, oy + 644, ox + 101, oy + 692], fill=(16, 185, 129, 90), outline=(16, 185, 129, 255), width=2)
draw.text((ox + 10, oy + 625), 'Bread (43,644)-(101,692)', fill='#34d399', font=font_bold)

# 4. Battle Button
draw_ol.rectangle([ox + 959, oy + 666, ox + 1016, oy + 747], fill=(245, 158, 11, 60), outline=(245, 158, 11, 255), width=1)
draw.text((ox + 880, oy + 650), 'Battle (959,666)-(1016,747)', fill='#fbbf24', font=font_small)

# 5. Center Dialog Popup from screenshot: (370, 335) to (652, 455)
draw.rectangle([ox + 370, oy + 335, ox + 652, oy + 455], fill=(28, 35, 51, 240), outline=(71, 85, 105, 255), width=2)
draw.text((ox + 385, oy + 350), 'System Dialog: \"There are no items registered by you.\"', fill='#f1f5f9', font=font_bold)
draw.text((ox + 385, oy + 375), 'Dialog Box: (370, 335) - (652, 455)', fill='#94a3b8', font=font_small)

# 6. OLD emptyfooddrake region: (582, 418) to (617, 446)
draw_ol.rectangle([ox + 582, oy + 418, ox + 617, oy + 446], fill=(244, 63, 94, 70), outline=(244, 63, 94, 255), width=1)
draw.text((ox + 582, oy + 450), 'Old Cutoff Box (582,418)', fill='#fb7185', font=font_small)

# 7. NEW emptyfoodinter search region: (450, 350) to (680, 480) [PRIMARY FOCUS]
efx1, efy1, efx2, efy2 = 450, 350, 680, 480
draw_ol.rectangle([ox + efx1, oy + efy1, ox + efx2, oy + efy2], fill=(239, 68, 68, 60), outline=(239, 68, 68, 255), width=3)
draw.text((ox + efx1 + 10, oy + efy1 + 8), f'FindPic Search Region: ({efx1}, {efy1}) to ({efx2}, {efy2})', fill='#ef4444', font=font_bold)

# Actual OK button position: (602, 414)
bmp_path = r'c:\Users\rd\Documents\exploration\test\project\Resource\emptyfoodinter.bmp'
if os.path.exists(bmp_path):
    ok_bmp = Image.open(bmp_path)
    ok_x = ox + 602
    ok_y = oy + 414
    img.paste(ok_bmp, (ok_x, ok_y))
    draw_ol.rectangle([ok_x - 2, ok_y - 2, ok_x + ok_bmp.size[0] + 2, ok_y + ok_bmp.size[1] + 2], outline=(56, 189, 248, 255), width=2)
    draw.text((ok_x - 120, ok_y + 1), 'OK at (602, 414) ->', fill='#38bdf8', font=font_bold)

# Right Side Panel
px = 1110
py = 130
pw = 450
ph = 768

draw.rectangle([px, py, px + pw, py + ph], fill=(22, 27, 38, 255), outline=(51, 65, 85, 255), width=2)
draw.text((px + 20, py + 18), 'Coordinate Reference Table', fill='#ffffff', font=font_header)

table_items = [
    ('emptyfoodinter.bmp Search', '(450, 350) to (680, 480)', '230 x 130 px', '[Red Box]', 'Full dialog popup coverage'),
    ('OK Button Exact Location', '(602, 414) to (636, 429)', '34 x 15 px', '[Cyan Box]', 'Exact OK button in game screen'),
    ('Old Box (Why it failed)', '(582, 418) to (617, 446)', '35 x 28 px', '[Pink Line]', 'Cut off OK button at top & right'),
    ('bread.bmp (Satiety)', '(43, 644) to (101, 692)', '58 x 48 px', '[Green Box]', 'HUD food icon (Alt+1, Alt+2)'),
    ('nostamina.bmp', '(90, 695) to (99, 703)', '9 x 8 px', '[White Box]', 'Stamina indicator'),
    ('Mercenary List', '(0, 0) to (120, 700)', '120 x 700 px', '[Purple]', 'Left side mercenary portraits'),
    ('Overworld Monsters', '(96, 84) to (964, 600)', '868 x 516 px', '[Blue Area]', 'Monster hunt search window'),
    ('Battle Field Indicator', '(959, 666) to (1016, 747)', '57 x 81 px', '[Orange Box]', 'In-battle confirmation flag'),
]

ty = py + 55
for name, coords, dim, color_tag, desc in table_items:
    draw.text((px + 20, ty), f'{color_tag} {name}', fill='#f8fafc', font=font_bold)
    ty += 18
    draw.text((px + 40, ty), f'Coords: {coords}', fill='#38bdf8', font=font_code)
    draw.text((px + 270, ty), f'Size: {dim}', fill='#94a3b8', font=font_body)
    ty += 16
    draw.text((px + 40, ty), f'Note: {desc}', fill='#cbd5e1', font=font_small)
    ty += 24
    draw.line([px + 20, ty - 6, px + pw - 20, ty - 6], fill='#334155', width=1)

draw.text((px + 20, ty + 10), 'Fixed Code (Line 98):', fill='#ffffff', font=font_header)
ty += 35
code_box = [
    '(_, x_empty, y_empty) = dm.FindPic(',
    '    450, 350, 680, 480,',
    '    \"emptyfoodinter.bmp\",',
    '    \"050505\", 0.8, 0',
    ')'
]
draw.rectangle([px + 20, ty, px + pw - 20, ty + 100], fill=(15, 18, 26, 255), outline=(56, 189, 248, 150), width=1)
for i, cline in enumerate(code_box):
    draw.text((px + 30, ty + 10 + i * 16), cline, fill='#38bdf8', font=font_code)

ty += 115
draw.text((px + 20, ty), 'Why the Old Box Failed:', fill='#ffffff', font=font_header)
ty += 22
notes = [
    '1. The actual OK button is located at (602, 414) to (636, 429).',
    '2. The old box (582, 418) to (617, 446) ended at x2=617, cutting off',
    '   the right half of the 34px OK button (ends at 636).',
    '3. The old box started at y1=418, cutting off the top 4px of the button.',
    '4. New box (450,350)-(680,480) matches 100% with 0px difference.'
]
for n in notes:
    draw.text((px + 20, ty), n, fill='#94a3b8', font=font_small)
    ty += 16

img = Image.alpha_composite(img, overlay)
img.convert('RGB').save(out_png, 'PNG')
print('Blueprint saved to:', out_png)
