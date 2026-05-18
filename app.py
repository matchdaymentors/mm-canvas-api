from flask import Flask, request, jsonify
import base64
import io
import json
import os
import threading
import time
import uuid
import requests
import traceback
from canvas_generator import generate_images, generate_story_images, generate_custom_card, generate_custom_story, generate_match_card, generate_match_story, generate_daily_results, generate_compact_results

app = Flask(__name__)

# Apps Script Web App URL (mm_automation.gs handles telegram + capi actions).
# Telegram cannot hit Apps Script directly because Apps Script responds with 302
# redirects to script.googleusercontent.com (with rotating user_content_key that
# Telegram won't follow). This Flask app proxies POST -> Apps Script and returns
# 200 to Telegram immediately.
APPS_SCRIPT_URL = os.environ.get(
    'APPS_SCRIPT_URL',
    'https://script.google.com/macros/s/AKfycbwXyDTyO3mqOJNisnZe_cnWJ4C5Mg3MxdWEo64V9MY_Kgc3WtndUxw0FecGfuE0H74kKA/exec'
)

# In-memory command queue. PowerShell poller (queue_processor.ps1) on the PC reads
# this every 2 min, sends Telegram confirmations + processes commands using local
# credentials (no secrets in this repo).
# Each entry: {'id': uuid, 'cmd': str, 'hint': str, 'chat_id': int, 'created_at': float, 'raw_text': str}
TOPIC_QUEUE = []
TOPIC_QUEUE_LOCK = threading.Lock()
# Per-chat fix-mode state. When a chat is in fix mode, the NEXT plain text
# message from that chat is treated as the fix instruction (free-form).
FIX_MODE = {}  # chat_id -> True
FIX_MODE_LOCK = threading.Lock()

# Last seen chat_id from ANY incoming Telegram message. Captured so autonomous
# publications can send Telegram preview to the right chat. Persists for container
# lifetime (warmer keeps Render alive 24/7).
LAST_CHAT = {'chat_id': None, 'updated_at': None}
LAST_CHAT_LOCK = threading.Lock()

# 2026-05-14: In-memory ring buffer of every Telegram message received, so Claude
# can read what Iliyan typed (independent of regex matching). Exposed via GET
# /telegram-history. Persists for container lifetime (warmer keeps Render alive).
INBOX = []  # list of {ts, chat_id, text, detected_cmd, action}
INBOX_LOCK = threading.Lock()
INBOX_MAX = 100


def detect_command_(text):
    """Recognize all MM commands. Return ('cmd_name', hint) or (None, None)."""
    if not text:
        return None, None
    lc = text.strip().lower()
    if lc.startswith('/topic'):
        return ('topic', text.strip()[len('/topic'):].strip())
    if lc.startswith('/post'):
        return ('post', text.strip()[len('/post'):].strip())
    if lc.startswith('/news'):
        return ('news', '')
    if lc.startswith('/approve'):
        return ('approve', text.strip()[len('/approve'):].strip())
    if lc.startswith('/fix'):
        return ('fix', text.strip()[len('/fix'):].strip())
    if lc.startswith('/skip'):
        return ('skip', text.strip()[len('/skip'):].strip())
    if lc.startswith('/free'):
        # /free Liverpool over 2.5 @ 1.85 KO 20:00: reasoning text
        # Pass everything after /free as the hint - queue_processor parses fields.
        return ('free', text.strip()[len('/free'):].strip())
    # NEW WORKFLOW (2026-05-05): /go /fix /kill on pending_draft.json
    if lc == '/go' or lc.startswith('/go '):
        return ('go', '')
    if lc == '/kill' or lc.startswith('/kill '):
        return ('kill', '')
    if lc.startswith('/fix '):
        # /fix "old text" "new text"  -> literal find-replace
        return ('fix', text.strip()[len('/fix'):].strip())
    # PLAIN ENGLISH WORKFLOW (2026-05-07, expanded 2026-05-10):
    # See memory/feedback_natural_language_approval.md - Iliyan typed "I approve"
    # and the queue stayed empty. We now match approval intent ANYWHERE in the message.
    #
    # Numbered targets first ('publish N' / 'kill N' / 'approved N' / 'approved all')
    # Then natural-language approval/rejection that includes the intent ANYWHERE
    # 2026-05-13: added "approved" (past tense) to numbered pattern after Iliyan
    # typed "I approved all" and queue stayed empty - "approved" needs to match
    # alongside "approve". Same for past-tense "killed".
    import re
    m = re.match(r'^(?:i\s+)?(?:publish|go|approve[ds]?|ship|post)(?:\s+them)?\s+(\d+|all)\s*\.?\s*$', lc)
    if m:
        return ('publish_row', m.group(1))
    m = re.match(r'^(?:i\s+)?(?:kill|killed|discard|discarded|skip|skipped|cancel|cancelled|delete|deleted)\s+(\d+|all)\s*\.?\s*$', lc)
    if m:
        return ('kill_row', m.group(1))
    # Also catch "approved all 4" / "publish them all" / "i approve everything" variants
    if re.search(r'\b(?:i\s+)?(?:approved?|publish(?:ed)?)\s+(?:them\s+)?all\b', lc):
        return ('publish_row', 'all')
    if re.search(r'\bapproved\s+everything\b', lc) or re.search(r'\bpublish\s+everything\b', lc):
        return ('publish_row', 'all')

    # =========================================================================
    # 2026-05-14: FREE-FORM FIX DETECTION (must run BEFORE approval check
    # because compound messages like "this is good BUT [fix]" need to be
    # treated as FIX, not as silent approval.)
    #
    # Triggered after Iliyan typed "This one is good, but when you get pictures
    # from poste should get the ones with green dicks on them" and the regex
    # treated nothing as command. Also triggered by "The picture you used is
    # not in the right size and is missing the last rules we set."
    # =========================================================================
    fix_patterns = [
        r'\bis\s+(?:wrong|missing|broken|incorrect|off|bad)\b',
        r'\bis\s+not\s+(?:right|correct|good|in\s+the\s+right|matching|working)\b',
        r'\bare\s+(?:wrong|missing|broken|incorrect|off|bad)\b',
        r'\b(?:should|needs?\s+to|need\s+to|must|have\s+to)\s+(?:be|have|use|include|change|get|fix|update|swap|replace)\b',
        r'\bchange\s+(?:to|the|this|it|that)\b',
        r'\bfix\s+(?:it|this|that|the)\b',
        r'\b(?:wrong|missing|broken)\s+(?:size|picture|image|photo|colou?r|font|word|name|player|crest|logo|caption|hashtags?)\b',
        r'\bdoesn\'?t\s+(?:look|fit|work|match|render|seem|read)\b',
        r'\bnot\s+(?:in\s+the\s+right|the\s+right|right)\s+(?:size|colou?r|format|aspect|crop|font)\b',
        r'\b(?:replace|swap|switch)\s+(?:the\s+)?(?:photo|image|picture|word|caption)\b',
        r'\b(?:add|remove|delete|drop)\s+(?:the\s+)?(?:logo|caption|hashtags?|word|line|image|photo)\b',
        r'\b(?:make\s+it|make\s+the)\s+(?:\w+\s+){0,3}(?:bigger|smaller|gold|white|dark|brighter|darker|larger|smaller|bolder|thinner|red|green|blue|black)\b',
        r'\bmissing\s+(?:the\s+)?(?:rules?|logo|hashtags?|caption|attribution|credit)\b',
        r'\b(?:re\s*-?\s*do|redo|rebuild|regenerate)\b',
    ]
    for p in fix_patterns:
        if re.search(p, lc):
            return ('fix', text.strip())

    # Natural-language approval - matches phrases ANYWHERE in message body.
    # Examples that must match:
    #   "I approve" / "I approve this" / "I approve your last message"
    #   "looks good" / "looking good" / "this looks great" / "this is good"
    #   "this one is good" / "that's good" / "it is great" / "perfect"
    #   "I like it" / "I like that"
    #   "go ahead" / "let's go" / "ok go" / "ok publish"
    #   "yes" alone or "yes please" / "yes do it"
    approval_patterns = [
        r'\bi\s+approved?\b',      # "i approve" OR "i approved"
        r'\bapproved\b',
        r'\blooks?\s+(?:good|great|perfect|fine|nice|sick|clean)\b',
        r'\blooking\s+(?:good|great|perfect|nice|sick|clean)\b',
        # 2026-05-14: NEW - "this/it/that (one) is/looks good/great/perfect"
        r'\b(?:this|it|that)\s+(?:one\s+)?(?:is|looks?)\s+(?:good|great|perfect|fine|nice|sick|clean|the\s+one)\b',
        r'\bthat\'?s\s+(?:good|great|perfect|fine|nice|the\s+one)\b',
        r'\bi\s+like\s+(?:it|that|this)\b',
        r'\b(?:lets?|let\'s)\s+go\b',
        r'\bgo\s+(?:ahead|for\s+it|publish)\b',
        r'\bok\s+(?:publish|go|do\s+it)\b',
        r'\b(?:do|send|ship|fire|post)\s+it\b',
        r'\bpublish\s+(?:it|this|that)\b',
        r'\bpost\s+(?:it|this|that)\b',
    ]
    for p in approval_patterns:
        if re.search(p, lc):
            return ('go', '')
    # Bare single-word approvals (incl. "perfect" / "great" / "nice" alone)
    # 2026-05-16 EXPANSION: 26 short-form replies were ALL silent-dropping.
    # Includes A/B/C/D (binary-choice answers), y/yes/yep/yeah/ya, sure/fine/cool/ok/k/kk,
    # ship/doit, and 1/2/3 numbered-choice answers.
    bare_approvals = (
        'go', 'yes', 'publish', 'approve', 'shipit', 'fireit', 'sendit', 'postit',
        'perfect', 'great', 'nice', 'good', 'love it', 'loveit',
        # 2026-05-16 additions:
        'a', 'go a', 'option a', 'pick a', 'do a', 'a please',  # binary choice "A"
        '1', 'go 1', 'option 1', 'pick 1', 'do 1', '1 please',  # numbered choice "1"
        'y', 'yep', 'yeah', 'ya', 'yup', 'yes please',
        'sure', 'fine', 'cool', 'ok', 'okay', 'k', 'kk',
        'ship', 'do it', 'doit', 'send it', 'post it', 'publish it'
    )
    if lc.rstrip('.!') in bare_approvals:
        return ('go', '')

    # Natural-language rejection
    rejection_patterns = [
        r'\bi\s+(?:reject|don\'?t\s+approve|don\'?t\s+want|don\'?t\s+like)\b',
        r'\b(?:kill|discard|cancel|forget)\s+(?:it|this|that)\b',
        r'\bdon\'?t\s+publish\b',
    ]
    for p in rejection_patterns:
        if re.search(p, lc):
            return ('kill', '')
    # Bare rejections - 2026-05-16 expanded with B/C choice answers + nope/nah/n/2
    bare_rejections = (
        'no', 'kill', 'discard', 'cancel', 'skip', 'forget it', 'forget', 'stop', 'abort',
        # 2026-05-16 additions:
        'b', 'go b', 'option b', 'pick b', 'do b', 'b please',  # binary choice "B"
        '2', 'go 2', 'option 2', 'pick 2', 'do 2', '2 please',  # numbered choice "2"
        'n', 'nope', 'nah', 'nay', 'no thanks', 'no thx'
    )
    if lc.rstrip('.!') in bare_rejections:
        return ('kill', '')

    # =========================================================================
    # 2026-05-14: SILENT-FAILURE PROTECTION
    # 2026-05-16 LOWERED FROM 15 to 1 char. The 15-char gate was the source of
    # 26 silent drops including Iliyan's "A" answer to a binary-choice menu.
    # Now ANY unmatched non-slash message gets 'unknown' which queue_processor
    # turns into a "I didn't catch this, reply approve/fix/kill" Telegram.
    # The bare_approvals + bare_rejections lists above should catch most short
    # answers, so 'unknown' fires only for genuinely unparseable input.
    # =========================================================================
    if len(text.strip()) >= 1 and not text.strip().startswith('/'):
        return ('unknown', text.strip())

    return None, None

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


APP_VERSION = '2.4.0'  # compact results: bigger sizes + Gemini bg


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'version': APP_VERSION})


@app.route('/telegram-proxy', methods=['POST', 'GET'])
def telegram_proxy():
    """Telegram -> Apps Script bridge.

    Telegram POSTs an update here. We forward the JSON to Apps Script in a
    background thread (so the long /summary Claude+Canvas chain can run for
    20+ seconds without Telegram timing out at 10s) and return 200 immediately.

    The forwarder uses requests.post with allow_redirects=True so Apps Script's
    302 -> script.googleusercontent.com hop is followed transparently.
    """
    if request.method == 'GET':
        return jsonify({'status': 'ok', 'service': 'mm_telegram_proxy', 'target': APPS_SCRIPT_URL.split('?')[0]})

    payload = request.get_json(silent=True) or {}
    secret_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    action = request.args.get('action', 'telegram')

    # =========================================================================
    # /post /topic /news command interception
    # Handle directly here (Apps Script doesn't have these handlers deployed yet).
    # Store topic in TOPIC_QUEUE -> publication_generator.ps1 polls and processes.
    # =========================================================================
    post = payload.get('channel_post') or payload.get('message') or {}
    text = post.get('text', '') or ''
    chat = post.get('chat', {}) or {}
    chat_id = chat.get('id')

    # Capture last seen chat_id (any message: photo, command, plain text)
    # 2026-05-14: REJECT obviously-test chat_ids. Real Telegram channel ids are
    # large negative integers (-100xxxxxxxxxx). Real DMs are positive ints in the
    # billions. Anything 0 < id < 1_000_000 is a synthetic test id from Claude's
    # regex/proxy testing - polluting LAST_CHAT with these breaks autonomous
    # publication previews (they get sent to a dead chat_id and Iliyan sees nothing).
    if chat_id and not (0 < chat_id < 1_000_000):
        with LAST_CHAT_LOCK:
            LAST_CHAT['chat_id'] = chat_id
            LAST_CHAT['updated_at'] = time.time()
    cmd, hint = detect_command_(text)

    # 2026-05-14: log EVERY received Telegram message to the inbox so Claude can
    # read what Iliyan typed (independent of regex matching).
    # 2026-05-18: ALSO capture photo file_id when message contains a photo so Claude
    # can download it via Telegram getFile + use it in publication compositing
    photo_file_id = None
    photo_caption = post.get('caption', '') or ''
    if post.get('photo'):
        # Largest photo size = last in array (Telegram sorts ascending)
        photos = post.get('photo') or []
        if photos:
            largest = max(photos, key=lambda p: p.get('file_size', 0))
            photo_file_id = largest.get('file_id')

    if text or photo_file_id:
        with INBOX_LOCK:
            INBOX.append({
                'ts': time.time(),
                'chat_id': chat_id,
                'text': text or photo_caption,
                'detected_cmd': cmd,
                'detected_hint': hint,
                'photo_file_id': photo_file_id,
            })
            # Keep only last INBOX_MAX entries
            if len(INBOX) > INBOX_MAX:
                del INBOX[0:len(INBOX) - INBOX_MAX]

    # === FIX MODE STATE MACHINE ===
    # If user sends bare /fix (no args), set chat to fix-mode + tell them to describe.
    # Next plain-text message from that chat is consumed as the fix instruction.
    if cmd == 'fix' and (not hint or hint.strip() == ''):
        with FIX_MODE_LOCK:
            FIX_MODE[chat_id] = True
        # Queue a marker so queue_processor sends the prompt to user via Telegram
        topic_id = uuid.uuid4().hex[:8]
        with TOPIC_QUEUE_LOCK:
            TOPIC_QUEUE.append({
                'id': topic_id, 'cmd': 'fix_prompt', 'hint': '',
                'chat_id': chat_id, 'created_at': time.time(), 'raw_text': text,
            })
        print(f'[tg-proxy] fix mode set for chat {chat_id}')
        return jsonify({'ok': True, 'fix_mode': 'awaiting_description'}), 200

    # If chat is in fix-mode and this message is plain text (no command), use it as the fix.
    if not cmd and chat_id in FIX_MODE and FIX_MODE.get(chat_id) and text.strip():
        with FIX_MODE_LOCK:
            del FIX_MODE[chat_id]
        topic_id = uuid.uuid4().hex[:8]
        with TOPIC_QUEUE_LOCK:
            TOPIC_QUEUE.append({
                'id': topic_id, 'cmd': 'fix', 'hint': text.strip(),
                'chat_id': chat_id, 'created_at': time.time(), 'raw_text': text,
            })
        print(f'[tg-proxy] fix instruction received from chat {chat_id}: "{text[:80]}"')
        return jsonify({'ok': True, 'queued': 'fix', 'id': topic_id}), 200

    if cmd:
        topic_id = uuid.uuid4().hex[:8]
        with TOPIC_QUEUE_LOCK:
            TOPIC_QUEUE.append({
                'id': topic_id,
                'cmd': cmd,
                'hint': hint if cmd != 'news' else '__autonomous_trending__',
                'chat_id': chat_id,
                'created_at': time.time(),
                'raw_text': text,
            })
        # NO Telegram send from Render - all sends happen from PowerShell queue_processor.ps1
        # which has the bot token via local SKILL.md (no GitHub-exposable secrets here).
        # 2026-05-14: 'unknown' is queued the same way - queue_processor will Telegram
        # back asking Iliyan to clarify (approve / fix / kill / ignore).
        print(f'[tg-proxy] queued {cmd} id={topic_id} hint="{hint[:60]}"')
        return jsonify({'ok': True, 'queued': cmd, 'id': topic_id}), 200

    def _forward():
        try:
            url = APPS_SCRIPT_URL
            if '?' not in url:
                url = url + '?action=' + action
            elif 'action=' not in url:
                url = url + '&action=' + action
            r = requests.post(
                url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'X-Telegram-Bot-Api-Secret-Token': secret_header,
                },
                timeout=120,
                allow_redirects=True,
            )
            print(f'[tg-proxy] forwarded action={action} status={r.status_code} len={len(r.text or "")}')
        except Exception as ex:
            print(f'[tg-proxy] forward error: {ex}')

    threading.Thread(target=_forward, daemon=True).start()
    return jsonify({'ok': True}), 200


# =============================================================================
# TOPIC QUEUE endpoints - publication_generator.ps1 polls these
# =============================================================================

@app.route('/topic-queue', methods=['GET'])
def topic_queue_get():
    """Return all pending topics. Also include status counters."""
    with TOPIC_QUEUE_LOCK:
        items = list(TOPIC_QUEUE)
    return jsonify({'count': len(items), 'topics': items})


@app.route('/topic-queue/<topic_id>', methods=['DELETE'])
def topic_queue_delete(topic_id):
    """Remove a topic by id (after publication_generator processes it)."""
    with TOPIC_QUEUE_LOCK:
        before = len(TOPIC_QUEUE)
        TOPIC_QUEUE[:] = [t for t in TOPIC_QUEUE if t['id'] != topic_id]
        after = len(TOPIC_QUEUE)
    return jsonify({'removed': before - after, 'remaining': after})


@app.route('/last-chat-id', methods=['GET'])
def last_chat_id_get():
    """Returns the most recent chat_id captured from any incoming Telegram message.
    Used by publication_generator.ps1 in autonomous mode to know where to send the preview."""
    with LAST_CHAT_LOCK:
        return jsonify(dict(LAST_CHAT))


@app.route('/telegram-history', methods=['GET'])
def telegram_history_get():
    """Returns the last N Telegram messages received (in-memory ring buffer).
    2026-05-14: built so Claude can read what Iliyan typed in Telegram without
    relying on regex matching. Optional ?limit=20 and ?since=<unix_ts>."""
    try:
        limit = int(request.args.get('limit', 30))
    except (TypeError, ValueError):
        limit = 30
    limit = max(1, min(limit, INBOX_MAX))
    try:
        since = float(request.args.get('since', 0))
    except (TypeError, ValueError):
        since = 0
    with INBOX_LOCK:
        out = [m for m in INBOX if m.get('ts', 0) >= since]
    out = out[-limit:]
    return jsonify({'count': len(out), 'messages': out})


# /telegram-notify endpoint removed - PowerShell scripts send directly via Bot API
# (token stays on the PC, never in this repo).


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

        gemini_key = os.environ.get('GEMINI_API_KEY', '')
        print(f"Generating compact results: {won}/{total} won, date={date_str!r}, picks={total}, gemini={'yes' if gemini_key else 'no'}")

        img = generate_compact_results(picks, date_str, gemini_api_key=gemini_key)
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
