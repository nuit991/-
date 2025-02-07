import os
import shutil
from flask import Flask, request, render_template, jsonify
from paddleocr import PaddleOCR
import re

app = Flask(__name__)
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 清空 uploads 資料夾
def clear_uploads_folder():
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)  # 刪除檔案

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_images():
    # 每次上傳前先清空資料夾
    clear_uploads_folder()

    if 'files' not in request.files:
        return jsonify({"error": "未提供圖片"}), 400

    uploaded_files = request.files.getlist('files')
    response = []

    for file in uploaded_files:
        if file.filename == '':
            continue

        # 儲存原檔案
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # OCR 處理
        result = ocr.ocr(file_path, cls=True)
        if not result or not result[0]:
            response.append({"original_name": file.filename, "new_name": None, "message": "未能識別圖片文字"})
            continue

        # 處理檔名
        text = "".join([line[1][0] for line in result[0]])
        clean_text = re.sub(r'[^\w\s]', '', text).strip()[:50]

        # 重新命名檔案
        file_ext = os.path.splitext(file.filename)[-1]
        new_file_name = f"{clean_text}{file_ext}" if clean_text else file.filename
        new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_file_name)

        try:
            os.rename(file_path, new_file_path)
            response.append({"original_name": file.filename, "new_name": new_file_name, "message": "成功處理"})
        except Exception as e:
            response.append({"original_name": file.filename, "new_name": None, "message": str(e)})

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
