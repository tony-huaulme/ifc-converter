import os
import subprocess
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
ALLOWED_EXTENSIONS = {'ifc'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        # Save the uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        # Convert the file
        output_filename = f"{os.path.splitext(filename)[0]}.glb"
        output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)

        # Execute the IfcConverter command
        try:
            result = subprocess.run(
                [
                    'IfcConvert',
                    input_path, 
                    output_path,
                    '--use-element-guids', 
                     '-j', '8'
                ],
                capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            return jsonify({
                "error": "Conversion failed",
                "details": e.stderr
            }), 500

        # Send back the converted file
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True)
        else:
            return jsonify({"error": "Converted file not found"}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
    app.run(debug=True)
