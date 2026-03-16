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
        data = request.get_json(force=True, silent=True) or {}
        slips = data.get('slips', [])

        # Handle all possible input types
        if isinstance(slips, str) and slips:
            slips = json.loads(slips)
        elif not isinstance(slips, list):
            slips = []

        if not slips:
            return jsonify({'error': 'No slips provided', 'received': str(data)}), 400

        print(f"Generating canvas for {len(slips)} slips: {slips}")
        images = generate_images(slips)
        print(f"Canvas generated: {len(images)} images")

        image_urls = []
        for i, img in enumerate(images):
            print(f"Uploading image {i+1} to Cloudinary...")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            b64 = base64.b64encode(buffer.read()).decode('utf-8')

            response = requests.post(
                f'https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD}/image/upload',
                json={
                    'file': f'data:image/png;base64,{b64}',
                    'upload_preset': CLOUDINARY_PRESET
                },
                timeout=60
            )
            result = response.json()
            print(f"Cloudinary keys: {list(result.keys())}")

            if 'secure_url' in result:
                image_urls.append(result['secure_url'])
            else:
                public_id = result.get('public_id', '')
                if public_id:
                    manual_url = f"https://res.cloudinary.com/{CLOUDINARY_CLOUD}/image/upload/{public_id}.png"
                    image_urls.append(manual_url)
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
