import ddddocr

# 優先用 beta 模型（新版最強，對你呢類有線 + 扭曲嘅圖效果好啲）
try:
    ocr = ddddocr.DdddOcr(
        beta=True,       # 開啟新模型 common.onnx
        show_ad=False    # 關廣告
    )
    print("成功用 Beta 模型！")
except Exception as e:
    print("Beta 載入失敗，用 fallback 模型：", e)
    ocr = ddddocr.DdddOcr(show_ad=False)

# 讀圖（假設 captcha.png 放喺腳本同一個資料夾）
with open("train1.bmp", "rb") as f:   # ← 改成你實際檔名，例如 "6IEP8P.png"
    img_bytes = f.read()

result = ocr.classification(img_bytes)
print("辨識結果：", result)

# 如果想睇信心度（optional，新版支援）
# result_with_prob = ocr.classification(img_bytes, probability=True)
# print(result_with_prob)