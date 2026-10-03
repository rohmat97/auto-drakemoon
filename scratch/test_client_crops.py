import sys, os, cv2
sys.path.append(os.path.abspath('.'))
from captcha_solver import solve_captcha

img = cv2.imread(r'C:\Users\rd\.gemini\antigravity-ide\brain\62c97d29-370f-4b93-adab-a7aec08345cd\.user_uploaded\media_1790628162287.jpg')
client_img = img[29:, :] # 1024 x 768

candidates = [
    (331, 265, 665, 380, 'x1=331, y1=265, x2=665, y2=380'),
    (350, 265, 665, 380, 'x1=350, y1=265, x2=665, y2=380'),
    (331, 275, 650, 375, 'x1=331, y1=275, x2=650, y2=375'),
    (360, 270, 650, 375, 'x1=360, y1=270, x2=650, y2=375'),
    (331, 245, 562, 323, 'User (331, 245, 562, 323) [Y-75 applied to 320..398]'),
    (331, 320, 562, 398, 'User literal (331, 320, 562, 398)'),
]

for x1, y1, x2, y2, desc in candidates:
    crop = client_img[y1:y2, x1:x2]
    res = solve_captcha(crop)
    print(f'{desc} -> res="{res}"')
