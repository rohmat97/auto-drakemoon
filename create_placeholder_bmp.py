# create_placeholder_bmp.py — Create a tiny placeholder community.bmp
import struct
import os

resource_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resource')
output_path = os.path.join(resource_dir, 'community.bmp')

# Create a minimal 2x2 pixel 24-bit BMP (will never match anything in-game)
width, height = 2, 2
row_size = (width * 3 + 3) & ~3  # Pad rows to 4-byte boundary
pixel_data_size = row_size * height
file_size = 54 + pixel_data_size  # 14 (file header) + 40 (DIB header) + pixels

bmp = bytearray()

# BMP File Header (14 bytes)
bmp += b'BM'                              # Signature
bmp += struct.pack('<I', file_size)        # File size
bmp += struct.pack('<HH', 0, 0)           # Reserved
bmp += struct.pack('<I', 54)              # Pixel data offset

# DIB Header (BITMAPINFOHEADER, 40 bytes)
bmp += struct.pack('<I', 40)              # DIB header size
bmp += struct.pack('<i', width)           # Width
bmp += struct.pack('<i', height)          # Height
bmp += struct.pack('<HH', 1, 24)          # Planes, Bits per pixel
bmp += struct.pack('<I', 0)               # Compression (none)
bmp += struct.pack('<I', pixel_data_size) # Image size
bmp += struct.pack('<i', 2835)            # X pixels per meter
bmp += struct.pack('<i', 2835)            # Y pixels per meter
bmp += struct.pack('<I', 0)               # Colors in color table
bmp += struct.pack('<I', 0)               # Important color count

# Pixel data (2x2 magenta pixels - will never match game content)
for y in range(height):
    for x in range(width):
        bmp += bytes([255, 0, 255])  # BGR: Magenta
    # Pad row to 4-byte boundary
    bmp += bytes(row_size - width * 3)

with open(output_path, 'wb') as f:
    f.write(bmp)

print(f'Created placeholder: {output_path}')
print(f'File size: {os.path.getsize(output_path)} bytes')
print()
print('NOTE: This is a PLACEHOLDER (magenta 2x2 px) that will never match anything.')
print('Replace it with a real capture from the game using capture_community.py')
