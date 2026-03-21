from flask import Flask, request, jsonify
import base64
import io
import json
import os
import requests
import traceback
from canvas_generator import generate_images, generate_story_images

app = Flask(__name__)

CLOUDINARY_CLOUD = 'dz6mwug4p'
CLOUDINARY_PRESET = 'mm_unsigned'


def upload_to_cloudinary(img):
    """Upload a PIL image to Cloudinary, return secure URL."""
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')

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
        return result['secure_url']
    public_id = result.get('public_id', '')
    if public_id:
        return f"https://res.cloudinary.com/{CLOUDINARY_CLOUD}/image/upload/{public_id}.png"
    raise ValueError(f'Cloudinary error: {result}')


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

        # format: "post" (default), "story", or "both"
        fmt = data.get('format', 'post').lower()

        print(f"Generating canvas for {len(slips)} slips, format={fmt}: {slips}")

        result_payload = {'success': True}

        # ── Post images (1080×1080) ──────────────────────────────────────────
        if fmt in ('post', 'both'):
            images = generate_images(slips)
            print(f"Post canvas generated: {len(images)} images")
            image_urls = []
            for i, img in enumerate(images):
                print(f"Uploading post image {i+1} to Cloudinary...")
                url = upload_to_cloudinary(img)
                image_urls.append(url)
            result_payload['image_urls'] = image_urls
            result_payload['count'] = len(image_urls)

        # ── Story images (1080×1920) ─────────────────────────────────────────
        if fmt in ('story', 'both'):
            stories = generate_story_images(slips)
            print(f"Story canvas generated: {len(stories)} images")
            story_urls = []
            for i, img in enumerate(stories):
                print(f"Uploading story image {i+1} to Cloudinary...")
                url = upload_to_cloudinary(img)
                story_urls.append(url)
            result_payload['story_urls'] = story_urls
            result_payload['story_count'] = len(story_urls)

        return jsonify(result_payload)

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"ERROR: {error_msg}")
        return jsonify({'error': str(e), 'traceback': error_msg}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
