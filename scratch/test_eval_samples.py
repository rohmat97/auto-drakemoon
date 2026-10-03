import os, sys, cv2
sys.path.append(os.path.abspath('.'))
from captcha_solver import solve_captcha

artifact_dir = r'C:\Users\rd\.gemini\antigravity-ide\brain\62c97d29-370f-4b93-adab-a7aec08345cd'
files = [
    ('captcha_sample_current.png', 'Current Code (331, 275, 650, 365)'),
    ('captcha_sample_user_direct.png', 'User Direct (331, 320, 562, 398)'),
    ('captcha_sample_user_y75.png', 'User Y-75 (331, 245, 562, 323)'),
    ('captcha_sample_optimal.png', 'Optimal Full Card (360, 305, 655, 405)'),
    ('captcha_sample_widened.png', 'Widened User X (331, 305, 660, 405)'),
]

for f, desc in files:
    p = os.path.join(artifact_dir, f)
    img = cv2.imread(p)
    res = solve_captcha(img)
    print(f'{desc} -> Solved: "{res}"')
