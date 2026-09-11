# draw_overworld_map.py
import os
from PIL import Image, ImageDraw, ImageFont

def main():
    width, height = 1500, 920
    img = Image.new('RGBA', (width, height), (15, 18, 26, 255))
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    draw = ImageDraw.Draw(img)
    draw_ol = ImageDraw.Draw(overlay)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_header = ImageFont.truetype("arial.ttf", 18)
        font_body = ImageFont.truetype("arial.ttf", 13)
        font_small = ImageFont.truetype("arial.ttf", 11)
    except IOError:
        font_title = font_header = font_body = font_small = ImageFont.load_default()

    # Title
    draw.text((40, 20), "Gersang Screen UI & Anti-Cheat Region Map (1024 x 768)", fill="#FFFFFF", font=font_title)
    draw.text((40, 56), "Visual coordinates of detection zones: Anti-cheat, Satiety/Bread, Stamina, Captcha & Monster Search", fill="#8EA0BC", font=font_body)

    # Game Screen Box (Offset x=40, y=100)
    gx, gy = 40, 100
    gw, gh = 1024, 768
    
    # Screen Frame
    draw.rectangle([gx, gy, gx + gw, gy + gh], fill=(24, 28, 40, 255), outline="#38435C", width=2)
    
    # Grid lines / Center
    draw.line([gx + gw//2, gy, gx + gw//2, gy + gh], fill=(35, 42, 60, 255), width=1)
    draw.line([gx, gy + gh//2, gx + gw, gy + gh//2], fill=(35, 42, 60, 255), width=1)
    draw.text((gx + gw//2 + 8, gy + gh//2 + 8), "Center (512, 384)", fill="#4F5D7E", font=font_small)

    # 1. Concentric Monster Search Zones
    # Zone 3: Full (0,0) - (1024,768)
    draw.rectangle([gx, gy, gx + gw, gy + gh], outline="#4A5568", width=1)
    
    # Zone 2: Mid (222, 162) to (802, 522)
    z2_x1, z2_y1 = gx + 222, gy + 162
    z2_x2, z2_y2 = gx + 802, gy + 522
    draw_ol.rectangle([z2_x1, z2_y1, z2_x2, z2_y2], fill=(66, 153, 225, 25), outline="#4299E1", width=1)
    draw.text((z2_x1 + 8, z2_y1 + 8), "Zone 2: Mid-Range (222, 162) to (802, 522)", fill="#63B3ED", font=font_small)

    # Zone 1: Center (352, 242) to (672, 442)
    z1_x1, z1_y1 = gx + 352, gy + 242
    z1_x2, z1_y2 = gx + 672, gy + 442
    draw_ol.rectangle([z1_x1, z1_y1, z1_x2, z1_y2], fill=(72, 187, 120, 35), outline="#48BB78", width=2)
    draw.text((z1_x1 + 8, z1_y1 + 8), "Zone 1: Center / Player Proximity (352, 242) to (672, 442)", fill="#68D391", font=font_small)

    # 2. Horse Stamp: (599, 21) to (650, 49)
    hx1, hy1 = gx + 599, gy + 21
    hx2, hy2 = gx + 650, gy + 49
    draw_ol.rectangle([hx1, hy1, hx2, hy2], fill=(237, 137, 54, 180), outline="#DD6B20", width=2)
    
    # 3. Bread: (50, 650) to (93, 689)
    bx1, by1 = gx + 50, gy + 650
    bx2, by2 = gx + 93, gy + 689
    draw_ol.rectangle([bx1, by1, bx2, by2], fill=(236, 201, 75, 180), outline="#D69E2E", width=2)

    # 4. No Stamina: (90, 695) to (99, 703)
    sx1, sy1 = gx + 90, gy + 695
    sx2, sy2 = gx + 99, gy + 703
    draw_ol.rectangle([sx1, sy1, sx2, sy2], fill=(229, 62, 62, 220), outline="#E53E3E", width=2)

    # 5. In-Battle Check: (959, 666) to (1016, 747)
    bt1_x, bt1_y = gx + 959, gy + 666
    bt2_x, bt2_y = gx + 1016, gy + 747
    draw_ol.rectangle([bt1_x, bt1_y, bt2_x, bt2_y], fill=(159, 122, 234, 180), outline="#9F7AEA", width=2)

    # 6. Captcha Dialog Sample Box (Center Dialog 380, 260 to 640, 480)
    cx1, cy1 = gx + 375, gy + 280
    cx2, cy2 = gx + 645, gy + 470
    draw_ol.rectangle([cx1, cy1, cx2, cy2], fill=(45, 55, 72, 190), outline="#CBD5E0", width=1)
    draw.text((cx1 + 10, cy1 + 10), "Captcha Dialog Popup", fill="#E2E8F0", font=font_small)
    # Button (405, 440)
    btn_x, btn_y = gx + 405, gy + 440
    draw_ol.rectangle([btn_x - 15, btn_y - 10, btn_x + 25, btn_y + 10], fill=(66, 153, 225, 230), outline="#FFFFFF", width=1)
    draw.text((btn_x - 10, btn_y - 6), "Confirm", fill="#FFFFFF", font=font_small)

    # Merge overlay
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Side Panel / Legend
    px = 1100
    py = 100
    draw.text((px, py), "📋 Region Legend & Coordinate Specs", fill="#FFFFFF", font=font_header)
    py += 35

    legends = [
        ("🟠 Horse Stamp Icon (anti_cheat\\horse.bmp)", 
         "(599, 21) to (650, 49)", 
         "Located on top UI bar. In normal play, this seal is visible. If it vanishes while bread is visible, anti-cheat has flagged account.",
         "#ED8936"),
        ("🟡 Satiety / Bread Icon (anti_cheat\\bread.bmp)", 
         "(50, 650) to (93, 689)", 
         "Located on bottom-left HUD. Proves the game is in active overworld play (not loading/disconnected).",
         "#ECC94B"),
        ("🔴 No Stamina Icon (nostamina.bmp)", 
         "(90, 695) to (99, 703)", 
         "Located below satiety bar. Triggers auto-pause and window unbind when stamina is 0.",
         "#E53E3E"),
        ("🟣 Battle Mode Icon (battle.bmp / battle3.bmp)", 
         "(959, 666) to (1016, 747)", 
         "Located on bottom-right corner. Verifies whether client has entered/exited the battle field.",
         "#9F7AEA"),
        ("🔵 Captcha Confirm Button", 
         "(405, 440)", 
         "Where bot clicks submit after solving temp_captcha.bmp with OCR engine.",
         "#63B3ED"),
        ("🟢 Monster Concentric Search Zones", 
         "Zone 1: (352, 242) - (672, 442)\nZone 2: (222, 162) - (802, 522)\nZone 3: (0, 0) - (1024, 768)", 
         "Searches closest proximity first, expanding outward to avoid erratic clicks at window edges.",
         "#48BB78"),
    ]

    for title, coords, desc, color in legends:
        draw.rectangle([px, py, px + 12, py + 12], fill=color)
        draw.text((px + 20, py - 2), title, fill=color, font=font_body)
        py += 20
        draw.text((px + 20, py), f"Coords: {coords}", fill="#E2E8F0", font=font_small)
        py += 18 if "\n" not in coords else 40
        # Wrap description
        words = desc.split(" ")
        line = ""
        for word in words:
            if len(line + " " + word) > 42:
                draw.text((px + 20, py), line, fill="#A0AEC0", font=font_small)
                py += 16
                line = word
            else:
                line = (line + " " + word).strip()
        if line:
            draw.text((px + 20, py), line, fill="#A0AEC0", font=font_small)
            py += 16
        py += 12

    # Save image
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screen_regions_map.png")
    img.save(output_path)
    print(f"Generated map illustration at: {output_path}")

if __name__ == "__main__":
    main()
