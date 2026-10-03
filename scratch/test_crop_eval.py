import sys, os, cv2
sys.path.append(os.path.abspath('.'))
from captcha_solver import solve_captcha

img = cv2.imread(r'C:\Users\rd\.gemini\antigravity-ide\brain\62c97d29-370f-4b93-adab-a7aec08345cd\.user_uploaded\media_1790628162287.jpg')

tests = [
    (331, 320, 562, 398, 'User literal (331, 320, 562, 398)'),
    (331, 320-75, 562, 398-75, 'User Y-75 (331, 245, 562, 323)'),
    (331, 320, 662, 398, 'User X widened (331, 320, 662, 398)'),
    (331, 245, 662, 323, 'User X widened Y-75 (331, 245, 662, 323)'),
    (365, 305, 650, 400, 'Screenshot window coords full card (365, 305, 650, 400)'),
    (365, 305-26, 650, 400-26, 'Screenshot client coords (365, 279, 650, 374)'),
    (350, 275, 660, 380, 'Generous client coords (350, 275, 660, 380)'),
    (330, 260, 670, 400, 'Encompassing dialog inner (330, 260, 670, 400)'),
]

for (x1, y1, x2, y2, desc) in tests:
    crop = img[y1:y2, x1:x2]
    res = solve_captcha(crop)
    print(f'{desc}: res="{res}"')
