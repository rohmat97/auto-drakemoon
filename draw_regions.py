# draw_regions.py
import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Add local path to import config
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.join(_SCRIPT_DIR, 'Battle', 'Nytheris', 'ikan_tol')
if config_dir not in sys.path:
    sys.path.insert(0, config_dir)

try:
    from config import FORMATION_REGIONS, MONSTER_DIRECTION_REGIONS, MONSTER_CHECKS
except ImportError as e:
    print(f"Error importing config: {e}")
    sys.exit(1)

def draw_dashed_line(draw, pt1, pt2, color, width=1, dash_length=4):
    x1, y1 = pt1
    x2, y2 = pt2
    dx = x2 - x1
    dy = y2 - y1
    distance = (dx**2 + dy**2)**0.5
    if distance == 0:
        return
    
    num_dashes = int(distance / (dash_length * 2))
    for i in range(num_dashes):
        start_t = (i * 2) * dash_length / distance
        end_t = (i * 2 + 1) * dash_length / distance
        if end_t > 1:
            end_t = 1
        curr_pt1 = (int(x1 + dx * start_t), int(y1 + dy * start_t))
        curr_pt2 = (int(x1 + dx * end_t), int(y1 + dy * end_t))
        draw.line([curr_pt1, curr_pt2], fill=color, width=width)

def main():
    # Setup canvas sizes
    # Canvas is 1700 x 850
    width, height = 1700, 850
    img = Image.new('RGBA', (width, height), (14, 16, 23, 255)) # Dark blue-gray background
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    draw = ImageDraw.Draw(img)
    draw_ol = ImageDraw.Draw(overlay)
    
    # Try to load fonts
    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_header = ImageFont.truetype("arial.ttf", 18)
        font_body = ImageFont.truetype("arial.ttf", 14)
        font_small = ImageFont.truetype("arial.ttf", 11)
        font_legend = ImageFont.truetype("consola.ttf", 12)
    except IOError:
        # Fallback to default
        font_title = font_header = font_body = font_small = font_legend = ImageFont.load_default()

    # Draw Title
    draw.text((50, 20), "Gersang Screen Region Blueprint", fill="#ffffff", font=font_title)
    draw.text((50, 55), "Visual representation of config coordinates for battle detection & minimap scan", fill="#8f95b2", font=font_body)

    # 1. Main Game Canvas (Offset: 50, 90)
    game_ox, game_oy = 50, 90
    game_w, game_h = 1024, 768
    
    # Draw Game Canvas background & border
    draw.rectangle([game_ox, game_oy, game_ox + game_w, game_oy + game_h], fill=(21, 24, 36, 255), outline=(46, 52, 72, 255), width=2)
    draw.text((game_ox, game_oy - 25), "Main Game Screen Area (1024 x 768)", fill="#e2e8f0", font=font_header)

    # 2. Minimap Zoom Box (Offset: 1120, 90)
    zoom_ox, zoom_oy = 1120, 90
    zoom_w, zoom_h = 530, 768
    
    # Draw Zoom Box background & border
    draw.rectangle([zoom_ox, zoom_oy, zoom_ox + zoom_w, zoom_oy + zoom_h], fill=(21, 24, 36, 255), outline=(46, 52, 72, 255), width=2)
    draw.text((zoom_ox, zoom_oy - 25), "Minimap Scanning Details (Zoomed View)", fill="#e2e8f0", font=font_header)

    # Color configurations
    COLORS = {
        'East': {'fill': (59, 130, 246, 50), 'outline': (59, 130, 246, 255), 'text': '#3b82f6'},     # Blue
        'South': {'fill': (16, 185, 129, 50), 'outline': (16, 185, 129, 255), 'text': '#10b981'},    # Green
        'West': {'fill': (245, 158, 11, 50), 'outline': (245, 158, 11, 255), 'text': '#f59e0b'},     # Orange
        'North': {'fill': (239, 68, 68, 50), 'outline': (239, 68, 68, 255), 'text': '#ef4444'},      # Red
        'WestSouth': {'fill': (139, 92, 246, 50), 'outline': (139, 92, 246, 255), 'text': '#8b5cf6'},# Purple
        'NorthEast': {'fill': (20, 184, 166, 50), 'outline': (20, 184, 166, 255), 'text': '#14b8a6'},# Teal
    }
    
    # Draw Formation Regions
    for direction, regions in FORMATION_REGIONS.items():
        color_info = COLORS.get(direction, {'fill': (156, 163, 175, 50), 'outline': (156, 163, 175, 255), 'text': '#9ca3af'})
        for idx, reg in enumerate(regions):
            rx1, ry1, rx2, ry2 = reg
            # Offset coords to game canvas
            cx1 = game_ox + rx1
            cy1 = game_oy + ry1
            cx2 = game_ox + rx2
            cy2 = game_oy + ry2
            
            # Draw semi-transparent rectangle
            draw_ol.rectangle([cx1, cy1, cx2, cy2], fill=color_info['fill'], outline=color_info['outline'], width=2)
            
            # Label placement logic: place text labels cleanly
            label = f"{direction} F{idx+1}"
            tw = draw.textlength(label, font=font_small)
            
            # Draw label background box
            lx = cx1
            ly = cy1 - 15 if cy1 - 15 > game_oy else cy2 + 2
            
            # Handle right edge overflows
            if lx + tw > game_ox + game_w:
                lx = cx2 - tw
            
            draw_ol.rectangle([lx - 2, ly - 1, lx + tw + 2, ly + 13], fill=(14, 16, 23, 220))
            draw.text((lx, ly), label, fill=color_info['text'], font=font_small)

    # 3. Draw Minimap Bounding Frame on main screen
    # Minimap actual bounds is around x: [70, 200], y: [680, 760]
    mm_x1, mm_y1, mm_x2, mm_y2 = 70, 680, 200, 760
    mcx1 = game_ox + mm_x1
    mcy1 = game_oy + mm_y1
    mcx2 = game_ox + mm_x2
    mcy2 = game_oy + mm_y2
    
    draw_ol.rectangle([mcx1, mcy1, mcx2, mcy2], fill=(255, 255, 255, 10), outline=(156, 163, 175, 180), width=1)
    # Label the minimap area
    draw_ol.rectangle([mcx1 + 2, mcy1 + 2, mcx1 + 90, mcy1 + 16], fill=(14, 16, 23, 200))
    draw.text((mcx1 + 5, mcy1 + 3), "Minimap Area", fill="#9ca3af", font=font_small)

    # 4. Zoomed detailed view layout
    # Center the detailed minimap inside the Zoom Box
    # Target size is width: 440, height: 270 (approx 3.4x zoom of 130x80 src area)
    z_w, z_h = 440, 270
    z_ox = zoom_ox + (zoom_w - z_w) // 2
    z_oy = zoom_oy + 120 # leaving space at the top for title/legend
    
    draw.rectangle([z_ox, z_oy, z_ox + z_w, z_oy + z_h], fill=(28, 32, 48, 255), outline=(59, 66, 96, 255), width=2)
    draw.text((z_ox, z_oy - 20), "Zoomed Minimap Coordinates View (3.4x zoom)", fill="#9ca3af", font=font_body)
    
    # Draw scale grid inside zoom box
    grid_color = (46, 52, 72, 100)
    for x_grid in range(70, 200, 20):
        pct = (x_grid - 70) / 130.0
        gx = int(z_ox + pct * z_w)
        draw.line([gx, z_oy, gx, z_oy + z_h], fill=grid_color, width=1)
        draw.text((gx - 10, z_oy + z_h + 3), f"x={x_grid}", fill="#4e546a", font=font_small)
        
    for y_grid in range(680, 761, 20):
        pct = (y_grid - 680) / 80.0
        gy = int(z_oy + pct * z_h)
        draw.line([z_ox, gy, z_ox + z_w, gy], fill=grid_color, width=1)
        draw.text((z_ox - 40, gy - 6), f"y={y_grid}", fill="#4e546a", font=font_small)

    # Map function to translate minimap coordinates to zoom box coordinates
    def to_zoom(gx, gy):
        px = (gx - 70) / 130.0
        py = (gy - 680) / 80.0
        zx_coord = z_ox + px * z_w
        zy_coord = z_oy + py * z_h
        return int(zx_coord), int(zy_coord)

    # Draw connection lines from Minimap Box to Zoom View
    draw_dashed_line(draw_ol, (mcx2, mcy1), (z_ox, z_oy), (156, 163, 175, 100), width=1)
    draw_dashed_line(draw_ol, (mcx2, mcy2), (z_ox, z_oy + z_h), (156, 163, 175, 100), width=1)

    # Draw Monster Direction Regions inside detailed zoom
    for direction, region in MONSTER_DIRECTION_REGIONS.items():
        color_info = COLORS.get(direction, {'fill': (156, 163, 175, 50), 'outline': (156, 163, 175, 255), 'text': '#9ca3af'})
        rx1, ry1, rx2, ry2 = region
        
        zx1, zy1 = to_zoom(rx1, ry1)
        zx2, zy2 = to_zoom(rx2, ry2)
        
        draw_ol.rectangle([zx1, zy1, zx2, zy2], fill=color_info['fill'], outline=color_info['outline'], width=2)
        
        # Label each box inside zoom
        label = f"{direction} ({rx1},{ry1})-({rx2},{ry2})"
        tw = draw.textlength(label, font=font_small)
        
        # Determine label position to avoid overlapping (since they are close together)
        # Shift East labels slightly to the right, West labels slightly to the left, etc.
        lx = zx1
        ly = zy1 - 16
        
        if direction == 'East':
            lx = zx2 + 5
            ly = zy1 - 5
        elif direction == 'West':
            lx = zx1 - tw - 5
            ly = zy1 - 5
        elif direction == 'South':
            lx = zx1 - 10
            ly = zy2 + 5
        elif direction == 'North':
            lx = zx1 - 10
            ly = zy1 - 18
        elif direction == 'WestSouth':
            lx = zx1 - tw - 5
            ly = zy2 - 5
        elif direction == 'NorthEast':
            lx = zx2 + 5
            ly = zy1 - 15

        draw_ol.rectangle([lx - 2, ly - 1, lx + tw + 2, ly + 13], fill=(14, 16, 23, 200))
        draw.text((lx, ly), label, fill=color_info['text'], font=font_small)

    # Draw Legend and Table details inside the Zoom Box
    # Top legend
    draw.text((zoom_ox + 20, zoom_oy + 15), "Color Legend & Scan Priorities:", fill="#ffffff", font=font_body)
    priority_y = zoom_oy + 40
    EMOJIS = {
        'East': '🟦',
        'South': '🟩',
        'West': '🟧',
        'North': '🟥',
        'WestSouth': '🟪',
        'NorthEast': '🌐',
    }
    priorities = []
    for direction, checks in MONSTER_CHECKS.items():
        emoji = EMOJIS.get(direction, '⬜')
        priority_str = " -> ".join(checks)
        priorities.append((direction, f"{emoji} {direction}: Priority: {priority_str}"))

    for idx, (dir_name, p_desc) in enumerate(priorities):
        c_text = COLORS.get(dir_name, {'text': '#ffffff'})['text']
        col_x = zoom_ox + 20 + (idx % 2) * 250
        col_y = priority_y + (idx // 2) * 22
        draw.text((col_x, col_y), p_desc, fill=c_text, font=font_small)

    # Bottom coordinate table
    draw.text((zoom_ox + 20, z_oy + z_h + 40), "Detailed Coordinates Table", fill="#ffffff", font=font_body)
    
    table_y = z_oy + z_h + 65
    headers = f"{'Region/Dir':<12} | {'Coordinates (x1, y1) to (x2, y2)':<35}"
    draw.text((zoom_ox + 20, table_y), headers, fill="#8f95b2", font=font_legend)
    draw.line([zoom_ox + 20, table_y + 15, zoom_ox + zoom_w - 20, table_y + 15], fill="#2e3440", width=1)
    
    table_y += 20
    # FORMATION REGIONS
    draw.text((zoom_ox + 20, table_y), "--- FORMATION REGIONS ---", fill="#4c566a", font=font_legend)
    table_y += 15
    for direction, regions in FORMATION_REGIONS.items():
        c_text = COLORS.get(direction, {'text': '#ffffff'})['text']
        coords_str = ", ".join([f"({r[0]},{r[1]})-({r[2]},{r[3]})" for r in regions])
        row_str = f"{direction:<12} | {coords_str:<35}"
        draw.text((zoom_ox + 20, table_y), row_str, fill=c_text, font=font_legend)
        table_y += 15
        
    table_y += 5
    # MINIMAP REGIONS
    draw.text((zoom_ox + 20, table_y), "--- MINIMAP SCAN REGIONS ---", fill="#4c566a", font=font_legend)
    table_y += 15
    for direction, region in MONSTER_DIRECTION_REGIONS.items():
        c_text = COLORS.get(direction, {'text': '#ffffff'})['text']
        coords_str = f"({region[0]},{region[1]}) to ({region[2]},{region[3]})"
        row_str = f"{direction:<12} | {coords_str:<35}"
        draw.text((zoom_ox + 20, table_y), row_str, fill=c_text, font=font_legend)
        table_y += 15

    # Alpha composite overlay
    img = Image.alpha_composite(img, overlay)
    
    # Save the output image
    output_png = os.path.join(_SCRIPT_DIR, 'regions_layout.png')
    img.convert('RGB').save(output_png, 'PNG')
    print(f"Successfully generated new diagram at: {output_png}")

if __name__ == '__main__':
    main()
