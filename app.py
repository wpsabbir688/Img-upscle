from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import os
from werkzeug.utils import secure_filename
import uuid
from PIL import Image
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ZIP_FOLDER = 'static/zips'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['ZIP_FOLDER'] = ZIP_FOLDER

# Create folders if not exist
for folder in [UPLOAD_FOLDER, RESULT_FOLDER, ZIP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def upscale_image(input_path, output_path, scale):
    img = Image.open(input_path)
    new_size = (img.width * scale, img.height * scale)
    upscaled = img.resize(new_size, Image.LANCZOS)
    upscaled.save(output_path)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    upload_type = request.form.get('uploadType', 'single')
    scale = int(request.form.get('scale', 4))

    # Generate unique subfolder
    session_id = str(uuid.uuid4())
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    result_path = os.path.join(app.config['RESULT_FOLDER'], session_id)
    os.makedirs(upload_path, exist_ok=True)
    os.makedirs(result_path, exist_ok=True)

    files = request.files.getlist('fileInput')
    results = []

    for file in files:
        filename = secure_filename(file.filename)
        if filename == '':
            continue
        input_filepath = os.path.join(upload_path, filename)
        file.save(input_filepath)

        name, ext = os.path.splitext(filename)
        upscaled_name = f"{name}_{scale}x{ext}"
        upscaled_path = os.path.join(result_path, upscaled_name)
        upscale_image(input_filepath, upscaled_path, scale)

        results.append({
            'original': '/' + input_filepath.replace('\\', '/'),
            'upscaled': '/' + upscaled_path.replace('\\', '/'),
            'download_name': upscaled_name
        })

    # Create ZIP if multiple images
    zip_file = None
    if len(results) > 1:
        zip_filename = f"{session_id}.zip"
        zip_path = os.path.join(app.config['ZIP_FOLDER'], zip_filename)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for r in results:
                zipf.write(r['upscaled'].lstrip('/'), arcname=os.path.basename(r['upscaled']))
        zip_file = '/' + zip_path.replace('\\', '/')

    return render_template('index.html', results=results, scale=scale, zip_file=zip_file)

if __name__ == '__main__':
    app.run(debug=True)
