import os
import subprocess
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename

import os
import subprocess
import ifcopenshell
from werkzeug.utils import secure_filename
from collections import defaultdict

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/convert', methods=['POST'])
def upload_and_convert_file_to_s3():
    
    file = request.files.get('file')
    ifcconvert_path = request.form.get('ifcconvert_path')  # Get the IfcConvert path from the request

    if not file:
        return jsonify({"message": "No file provided"}), 400

    if not file.filename.lower().endswith('.ifc'):
        print("File type validation failed: Only IFC files are allowed.")
        return jsonify({"message": "Only IFC files are allowed"}), 400

    try:
        # Save the uploaded file locally
        filename = secure_filename(file.filename)
        input_path = f'./uploads/{filename}'
        file.save(input_path)

        # Convert the file to GLB
        output_filename = f"{os.path.splitext(filename)[0]}.glb"
        output_path = f'./converted/{output_filename}'

        # Validate or locate IfcConvert
        if not ifcconvert_path:
            current_dir = os.getcwd()
            ifcconvert_path = os.path.join(current_dir, 'IfcConvert')
        if not os.path.exists(ifcconvert_path):
            raise FileNotFoundError(f"IfcConvert executable not found at: {ifcconvert_path}")

        # Run the conversion command
        subprocess.run(
            [
                ifcconvert_path,
                input_path,
                output_path
            ],
            capture_output=True, text=True, check=True
        )

        # Extract GUIDs and Descriptions
        ifc_file = ifcopenshell.open(input_path)
        description_dict = defaultdict(list)
        for element in ifc_file.by_type('IfcElement'):
            guid = element.GlobalId
            description = getattr(element, 'Description', None)
            if description:
                description_dict[description].append(guid)

        # Clean up input file
        os.remove(input_path)

        # Return the GLB file and extracted data
        return jsonify({
            "message": "File converted successfully",
            "glb_file_path": output_path,
            "extracted_data": description_dict
        }), 201

    except subprocess.CalledProcessError as e:
        return jsonify({"message": "Conversion failed", "details": e.stderr}), 500

    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500


@app.route('/found_file_path/<filename>', methods=['GET'])
def find_file(filename):
    script_dir = os.getcwd()  # Get the current working directory
    for root, dirs, files in os.walk(script_dir):
        print(f"Checking in {root}")
        if filename in files:
            return jsonify({"file_path": os.path.join(root, filename)}), 200
    return jsonify({"message": f"File '{filename}' not found"}), 404


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
    app.run(debug=True)