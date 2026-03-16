from flask import Flask, request, jsonify
import base64
import io
import json
import os
import requests
from canvas_generator import generate_images

app = Flask(__name__)

CLOUDINARY_CLOUD = 'dz6mwug4p'
CLOUDINARY_PRESET = 'mm_unsigned'

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json(force=True)
        slips = data.get('slips', [])

        if isinstance(slips, str):
            slips = json.loads(slips)

        if not slips:
            return jsonify({'error': 'No slips provided'}), 400

        images = generate_images(slips)

        image_urls = []
        for img in images:
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            b64 = base64.b64encode(buffer.read()).decode('utf-8')

            # Upload to Cloudinary
            response = requests.post(
                f'https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD}/image/upload',
                data={
                    'file': f'data:image/png;base64,{b64}',
                    'upload_preset': CLOUDINARY_PRESET
                }
            )
            result = response.json()
            if 'secure_url' in result:
                image_urls.append(result['secure_url'])
            else:
                return jsonify({'error': f'Cloudinary error: {result}'}), 500

        return jsonify({
            'success': True,
            'count': len(image_urls),
            'image_urls': image_urls
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
