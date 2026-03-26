from flask import Flask, request, jsonify
import base64
import io
import json
import os
import requests
import traceback
from canvas_generator import generate_images, generate_story_images, generate_custom_card, generate_custom_story, generate_match_card, generate_match_story, generate_daily_results

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



@app.route('/generate/custom', methods=['POST'])
def generate_custom():
    try:
        data = request.get_json(force=True, silent=True) or {}
        title = data.get('title', '').strip()
        subtitle = data.get('subtitle', '').strip()
        fmt = data.get('format', 'both').lower()

        if not title:
            return jsonify({'error': 'title is required'}), 400

        print(f"Generating custom card: title={title!r}, subtitle={subtitle!r}, format={fmt}")
        result_payload = {'success': True}

        if fmt in ('post', 'both'):
            img = generate_custom_card(title, subtitle)
            url = upload_to_cloudinary(img)
            result_payload['image_urls'] = [url]

        if fmt in ('story', 'both'):
            story_img = generate_custom_story(title, subtitle)
            story_url = upload_to_cloudinary(story_img)
            result_payload['story_urls'] = [story_url]

        return jsonify(result_payload)
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"ERROR in /generate/custom: {error_msg}")
        return jsonify({'error': str(e), 'traceback': error_msg}), 500


@app.route('/generate/matchcard', methods=['POST'])
def generate_matchcard():
    try:
        data = request.get_json(force=True, silent=True) or {}
        home_team      = data.get('home_team', '').strip()
        away_team      = data.get('away_team', '').strip()
        home_score     = data.get('home_score', 0)
        away_score     = data.get('away_score', 0)
        home_logo_url  = data.get('home_logo_url', '').strip()
        away_logo_url  = data.get('away_logo_url', '').strip()
        title          = data.get('title', 'MATCH RESULT').strip()
        subtitle       = data.get('subtitle', '').strip()
        label          = data.get('label', 'PREMIER LEAGUE').strip()
        fmt            = data.get('format', 'both').lower()

        if not home_team or not away_team:
            return jsonify({'error': 'home_team and away_team are required'}), 400

        print(f"Generating match card: {home_team} {home_score}-{away_score} {away_team}, format={fmt}")
        result_payload = {'success': True}

        if fmt in ('post', 'both'):
            img = generate_match_card(home_team, away_team, home_score, away_score,
                                      home_logo_url, away_logo_url, title, subtitle, label)
            url = upload_to_cloudinary(img)
            result_payload['image_urls'] = [url]

        if fmt in ('story', 'both'):
            story_img = generate_match_story(home_team, away_team, home_score, away_score,
                                             home_logo_url, away_logo_url, title, subtitle, label)
            story_url = upload_to_cloudinary(story_img)
            result_payload['story_urls'] = [story_url]

        return jsonify(result_payload)
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"ERROR in /generate/matchcard: {error_msg}")
        return jsonify({'error': str(e), 'traceback': error_msg}), 500


@app.route('/generate/daily-results', methods=['POST'])
def generate_daily_results_endpoint():
    """
    Generate a daily results infographic.

    Required body:
      picks  – list of pick objects:
               { home_team, away_team, home_score, away_score,
                 home_logo_url?, away_logo_url?,
                 market, pick, odds, won }
    Optional:
      date   – display date string, e.g. "24 MAR 2026"
      force  – if true, skip the ≥50% win-rate check (default false)
    """
    try:
        data   = request.get_json(force=True, silent=True) or {}
        picks  = data.get('picks', [])
        date_str = data.get('date', '').strip()
        force  = bool(data.get('force', False))

        if not isinstance(picks, list) or not picks:
            return jsonify({'error': 'picks array is required'}), 400

        total  = len(picks)
        won    = sum(1 for p in picks if p.get('won', False))
        pct    = won / total if total else 0

        if not force and pct < 0.5:
            return jsonify({
                'success': False,
                'skipped': True,
                'reason': f'Win rate {won}/{total} ({int(pct*100)}%) is below 50% threshold',
                'won': won,
                'total': total
            }), 200

        print(f"Generating daily results: {won}/{total} won, date={date_str!r}")

        imgs = generate_daily_results(picks, date_str)
        # Support both single image (legacy) and list of images (new)
        if not isinstance(imgs, list):
            imgs = [imgs]

        urls = []
        for i, img in enumerate(imgs):
            print(f"Uploading daily results image {i+1}/{len(imgs)} to Cloudinary...")
            urls.append(upload_to_cloudinary(img))

        # Labels: dark-card1, dark-card2, white-card1, white-card2
        labels = ['dark_card1', 'dark_card2', 'white_card1', 'white_card2']
        labeled = {labels[i]: urls[i] for i in range(min(len(urls), len(labels)))}

        return jsonify({
            'success': True,
            'image_url': urls[0],        # backward compat
            'image_urls': urls,
            'cards': labeled,
            'won': won,
            'total': total,
            'win_rate': round(pct * 100, 1)
        })

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"ERROR in /generate/daily-results: {error_msg}")
        return jsonify({'error': str(e), 'traceback': error_msg}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
