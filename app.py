from flask import Flask, request, jsonify
import base64
import io
import json
import os
from canvas_generator import generate_images

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json(force=True)
        slips = data.get('slips', [])

        # Handle case where slips is a JSON string instead of array
        if isinstance(slips, str):
            slips = json.loads(slips)

        if not slips:
            return jsonify({'error': 'No slips provided'}), 400

        images = generate_images(slips)

        image_base64_list = []
        for img in images:
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            b64 = base64.b64encode(buffer.read()).decode('utf-8')
            image_base64_list.append(b64)

        return jsonify({
            'success': True,
            'count': len(image_base64_list),
            'images': image_base64_list
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
