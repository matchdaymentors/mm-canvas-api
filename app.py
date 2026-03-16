from flask import Flask, request, jsonify
import base64
import io
import json
import os
import requests
import traceback
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

        print(f"Generating canvas for {len(slips)} slips")
        images = generate_images(slips)
        print(f"Canvas generated: {len(images)} images")

        image_urls = []
        for i, img in enumerate(images):
            print(f"Uploading image {i+1} to Cloudinary...")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            b64 = base64.b64encode(buffer.read()).decode('utf-8')
            print(f"Image {i+1} base64 length: {len(b64)}")

            response = requests.post(
                f'https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD}/image/upload',
                data={
                    'file': f'data:image/png;base64,{b64}',
                    'upload_preset': CLOUDINARY_PRESET
                },
                timeout=60
            )
            print(f"Cloudinary response: {response.status_code} - {response.text[:200]}")
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
        error_msg = traceback.format_exc()
        print(f"ERROR: {error_msg}")
        return jsonify({'error': str(e), 'traceback': error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
