from flask import Flask, request, jsonify
import base64
import io
import json
import os
import requests
import traceback
from canvas_generator import generate_images, generate_story_images, generate_custom_card, generate_custom_story, generate_match_card, generate_match_story, generate_daily_results, generate_compact_results

app = Flask(__name__)

CLOUDINARY_CLOUD = 'dz6mwug4p'
CLOUDINARY_PRESET = 'mm_unsigned'


def cloudinary_transform(url, transform):
    """Inject a Cloudinary transform string into an existing upload URL."""
    return url.replace('/image/upload/', f'/image/upload/{transform}/')


def make_story_url(url):
    """Convert a feed image URL to a 1080×1920 story via Cloudinary transform."""
    return cloudinary_transform(url, 'c_pad,w_1080,h_1920,b_rgb:0a1812')


def make_x_url(url):
    """Convert a feed image URL to a 1600×900 Twitter/X card via Cloudinary transform."""
    return cloudinary_transform(url, 'c_pad,w_1600,h_900,b_rgb:0a1812')


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


APP_VERSION = '2.3.0'  # compact results card endpoint added


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'version': APP_VERSION})


@app.route('/version', methods=['GET'])
def version():
    return jsonify({'version': APP_VERSION})


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
        day_name = data.get('dayName', data.get('day_name', '')).strip()

        print(f"Generating canvas for {len(slips)} slips, format={fmt}, day={day_name}: {slips}")

        result_payload = {'success': True}

        # ── Post images (1080×1080) ──────────────────────────────────────────
        if fmt in ('post', 'both'):
            images = generate_images(slips, day_name=day_name)
            print(f"Post canvas generated: {len(images)} images")
            image_urls = []
            for i, img in enumerate(images):
                print(f"Uploading post image {i+1} to Cloudinary...")
                url = upload_to_cloudinary(img)
                image_urls.append(url)
            result_payload['image_urls'] = image_urls
            result_payload['x_urls'] = [make_x_url(u) for u in image_urls]
            result_payload['count'] = len(image_urls)

        # ── Story images (1080×1920) ─────────────────────────────────────────
        if fmt in ('story', 'both'):
            stories = generate_story_images(slips, day_name=day_name)
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
        picks        = data.get('picks', [])
        date_str     = data.get('date', '').strip()
        force        = bool(data.get('force', False))
        ai_background = bool(data.get('ai_background', False))

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

        imgs = generate_daily_results(picks, date_str, ai_background=ai_background)
        # Support both single image (legacy) and list of images (new)
        if not isinstance(imgs, list):
            imgs = [imgs]

        urls = []
        for i, img in enumerate(imgs):
            print(f"Uploading daily results image {i+1}/{len(imgs)} to Cloudinary...")
            urls.append(upload_to_cloudinary(img))

        # Labels: card1 (Odds < 1.50), card2 (Odds 1.50-2.00), card3 (Odds > 2.00)
        labels = ['card1', 'card2', 'card3']
        labeled = {labels[i]: urls[i] for i in range(min(len(urls), len(labels)))}

        # Platform-specific variants via Cloudinary transforms (no extra upload)
        story_urls = [make_story_url(u) for u in urls]
        x_urls     = [make_x_url(u)     for u in urls]
        story_labeled = {labels[i]: story_urls[i] for i in range(min(len(story_urls), len(labels)))}
        x_labeled     = {labels[i]: x_urls[i]     for i in range(min(len(x_urls), len(labels)))}

        return jsonify({
            'success': True,
            'image_url': urls[0],        # backward compat
            'image_urls': urls,
            'cards': labeled,
            'story_cards': story_labeled,   # 1080×1920 — for IG/FB Stories
            'x_cards': x_labeled,           # 1600×900 — for X/Twitter feed
            'won': won,
            'total': total,
            'win_rate': round(pct * 100, 1)
        })

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"ERROR in /generate/daily-results: {error_msg}")
        return jsonify({'error': str(e), 'traceback': error_msg}), 500


@app.route('/generate/social-image', methods=['POST'])
def generate_social_image():
    """
    Generate a standalone social media image via Gemini (Nano Banana 2).
    Body: { "prompt": "...", "size": "post" | "story" }
    Returns: { "url": "https://..." }
    """
    try:
        data   = request.get_json(force=True, silent=True) or {}
        prompt = data.get('prompt', '').strip()
        size   = data.get('size', 'post').lower()   # post=1080x1080, story=1080x1920

        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400

        api_key = os.environ.get('GEMINI_API_KEY', '')
        if not api_key:
            return jsonify({'error': 'GEMINI_API_KEY not configured on server'}), 500

        W = 1080
        H = 1080 if size == 'post' else 1920

        print(f"Calling Gemini for social image ({W}x{H})...")
        resp = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/'
            f'gemini-3.1-flash-image-preview:generateContent?key={api_key}',
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'responseModalities': ['IMAGE', 'TEXT']}
            },
            timeout=120
        )

        if resp.status_code != 200:
            return jsonify({'error': f'Gemini error {resp.status_code}', 'detail': resp.text[:400]}), 500

        parts = resp.json().get('candidates', [{}])[0].get('content', {}).get('parts', [])
        img_bytes = None
        for part in parts:
            if 'inlineData' in part:
                img_bytes = base64.b64decode(part['inlineData']['data'])
                break

        if not img_bytes:
            return jsonify({'error': 'Gemini returned no image', 'raw': str(parts)[:400]}), 500

        from PIL import Image as PILImage, ImageDraw as PILDraw, ImageChops as PILChops
        from io import BytesIO as _BytesIO
        img = PILImage.open(_BytesIO(img_bytes)).convert('RGBA')
        img = img.resize((W, H), PILImage.LANCZOS)

        # ── Overlay MM logo (bottom-right corner) ──────────────────────────
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo_white.png')
        if os.path.exists(logo_path):
            logo = PILImage.open(logo_path).convert('RGBA')
            logo_h = int(H * 0.07)          # 7% of card height
            logo_w = int(logo_h * logo.width / logo.height)
            logo   = logo.resize((logo_w, logo_h), PILImage.LANCZOS)
            # Semi-transparent: multiply alpha channel by 0.85
            r, g, b, a = logo.split()
            a = a.point(lambda x: int(x * 0.85))
            logo = PILImage.merge('RGBA', (r, g, b, a))
            pad  = int(W * 0.03)
            img.paste(logo, (W - logo_w - pad, H - logo_h - pad), logo)

        img = img.convert('RGB')
        url = upload_to_cloudinary(img)
        print(f"Social image uploaded: {url}")
        return jsonify({'success': True, 'url': url, 'width': W, 'height': H})

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"ERROR in /generate/social-image: {error_msg}")
        return jsonify({'error': str(e), 'traceback': error_msg}), 500


@app.route('/generate/compact-results', methods=['POST'])
def generate_compact_results_endpoint():
    """
    Generate a single compact dark-theme results card with all picks across all tiers.
    CL-style layout: all 15-20 games on one card, three tier sections.

    Required body:
      picks  – list of pick objects:
               { home_team, away_team, home_score, away_score,
                 home_logo_url?, away_logo_url?,
                 market, pick, odds, won }
    Optional:
      date   – display date string, e.g. "24 MAR 2026"
      force  – if true, skip the >=50% win-rate check (default false)
    """
    try:
        data     = request.get_json(force=True, silent=True) or {}
        picks    = data.get('picks', [])
        date_str = data.get('date', '').strip()
        force    = bool(data.get('force', False))

        if not isinstance(picks, list) or not picks:
            return jsonify({'error': 'picks array is required'}), 400

        total = len(picks)
        won   = sum(1 for p in picks if p.get('won', False))
        pct   = won / total if total else 0

        if not force and pct < 0.5:
            return jsonify({
                'success': False,
                'skipped': True,
                'reason': f'Win rate {won}/{total} ({int(pct*100)}%) is below 50% threshold',
                'won': won,
                'total': total
            }), 200

        print(f"Generating compact results: {won}/{total} won, date={date_str!r}, picks={total}")

        img = generate_compact_results(picks, date_str)
        if img is None:
            return jsonify({'error': 'No picks provided'}), 400

        print("Uploading compact results card to Cloudinary...")
        url = upload_to_cloudinary(img)

        return jsonify({
            'success': True,
            'image_url': url,
            'story_url': make_story_url(url),
            'x_url': make_x_url(url),
            'won': won,
            'total': total,
            'win_rate': round(pct * 100, 1)
        })

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"ERROR in /generate/compact-results: {error_msg}")
        return jsonify({'error': str(e), 'traceback': error_msg}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
