from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os, requests
from io import BytesIO

# ── Palette ──────────────────────────────────────────────────────────────────
BG_TOP        = (10, 34, 18)
BG_BOT        = (6,  20, 10)
GOLD          = (212, 175, 55)
GOLD_DIM      = (140, 112, 28)
WHITE         = (255, 255, 255)
GREY          = (200, 215, 205)       # much lighter for readability
GREY_LABEL    = (160, 180, 165)       # labels
CARD_BG       = (16, 50, 28)
CARD_BG2      = (11, 35, 20)
CARD_BORDER   = (50, 145, 78)
ACCENT_GREEN  = (52, 168, 83)
BETANO_ORANGE = (255, 140, 0)
BETANO_RED    = (220, 40, 55)
BETANO_DARK   = (180, 28, 40)
PATREON_RED   = (255, 66, 77)
BLACK         = (0, 0, 0)

FONT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Country flag data
FLAG_DATA = {
    "ENG": ((0,36,125),   (255,255,255), (207,20,43),  (255,255,255)),
    "GER": ((0,0,0),      (221,0,0),     (255,206,0),  (255,255,255)),
    "ITA": ((0,140,69),   (255,255,255), (206,43,55),  (255,255,255)),
    "FRA": ((0,35,149),   (255,255,255), (237,41,57),  (255,255,255)),
    "TUR": ((227,10,23),  (255,255,255), (227,10,23),  (255,255,255)),
    "POR": ((0,102,0),    (255,0,0),     (255,0,0),    (255,255,255)),
    "ESP": ((170,21,27),  (255,196,0),   (170,21,27),  (255,255,255)),
    "NED": ((174,28,40),  (255,255,255), (33,70,139),  (255,255,255)),
    "BEL": ((0,0,0),      (255,221,0),   (238,39,55),  (255,255,255)),
    "SCO": ((0,90,170),   (255,255,255), (0,90,170),   (255,255,255)),
    "POL": ((255,255,255),(220,20,60),   (220,20,60),  (0,0,0)),
    "SUI": ((255,0,0),    (255,255,255), (255,0,0),    (255,255,255)),
    "AUT": ((237,41,57),  (255,255,255), (237,41,57),  (255,255,255)),
    "GRE": ((13,94,175),  (255,255,255), (13,94,175),  (255,255,255)),
}

def draw_flag_badge(img, cx, cy, country_code, radius=26):
    code = str(country_code).upper()[:3]
    colors = FLAG_DATA.get(code, ((80,80,80),(120,120,120),(80,80,80),(255,255,255)))
    c_left, c_mid, c_right, c_text = colors
    size = radius * 2 + 4
    flag_img = Image.new("RGBA", (size, size), (0,0,0,0))
    fd = ImageDraw.Draw(flag_img)
    third = size // 3
    fd.rectangle([0, 0, third, size], fill=c_left)
    fd.rectangle([third, 0, third*2, size], fill=c_mid)
    fd.rectangle([third*2, 0, size, size], fill=c_right)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([2, 2, size-2, size-2], fill=255)
    flag_img.putalpha(mask)
    bd = ImageDraw.Draw(flag_img)
    bd.ellipse([1, 1, size-2, size-2], outline=(255,255,255), width=2)
    try:
        tf = ImageFont.truetype(os.path.join(FONT_DIR, 'Outfit-Bold.ttf'), radius//2+1)
    except:
        tf = ImageFont.load_default()
    td = ImageDraw.Draw(flag_img)
    bb = td.textbbox((0,0), code, font=tf)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    td.text(((size-tw)//2+1, (size-th)//2), code, font=tf, fill=(0,0,0,160))
    td.text(((size-tw)//2, (size-th)//2-1), code, font=tf, fill=c_text)
    img.paste(flag_img, (cx - size//2, cy - size//2), flag_img)


def F(name, size):
    m = {'BB':'BigShoulders-Bold.ttf','BR':'BigShoulders-Regular.ttf',
         'OB':'Outfit-Bold.ttf','OR':'Outfit-Regular.ttf'}
    try:    return ImageFont.truetype(os.path.join(FONT_DIR, m[name]), size)
    except: return ImageFont.load_default()

# ── Pitch background ─────────────────────────────────────────────────────────
def make_pitch_bg(W, H):
    bg = Image.new("RGB", (W, H), BG_TOP)
    d  = ImageDraw.Draw(bg)

    # Gradient bands
    for y in range(0, H, 2):
        t = y / H
        r = int(BG_TOP[0]*(1-t) + BG_BOT[0]*t)
        g = int(BG_TOP[1]*(1-t) + BG_BOT[1]*t)
        b = int(BG_TOP[2]*(1-t) + BG_BOT[2]*t)
        d.line([(0,y),(W,y)], fill=(r,g,b))

    # Grass stripes
    sw = 68
    for i in range(0, W+sw, sw*2):
        d.rectangle([i, 0, i+sw, H], fill=(13, 42, 23))

    lw, lc = 3, WHITE
    mx, my = 55, 55
    pw, ph = W-2*mx, H-2*my
    mid_y  = my + ph//2
    cx, cy_c = W//2, H//2

    d.rectangle([mx,my,mx+pw,my+ph], outline=lc, width=lw)
    d.line([(mx,mid_y),(mx+pw,mid_y)], fill=lc, width=lw)
    cr = 95
    d.ellipse([cx-cr,cy_c-cr,cx+cr,cy_c+cr], outline=lc, width=lw)
    d.ellipse([cx-5,cy_c-5,cx+5,cy_c+5], fill=lc)

    pb_w, pb_h = int(pw*.56), int(ph*.17)
    pb_x = mx+(pw-pb_w)//2
    d.rectangle([pb_x,my,pb_x+pb_w,my+pb_h], outline=lc, width=lw)
    d.rectangle([pb_x,my+ph-pb_h,pb_x+pb_w,my+ph], outline=lc, width=lw)

    sb_w, sb_h = int(pw*.24), int(ph*.075)
    sb_x = mx+(pw-sb_w)//2
    d.rectangle([sb_x,my,sb_x+sb_w,my+sb_h], outline=lc, width=lw)
    d.rectangle([sb_x,my+ph-sb_h,sb_x+sb_w,my+ph], outline=lc, width=lw)

    ar = 68
    d.arc([cx-ar,my+pb_h-ar,cx+ar,my+pb_h+ar], 30, 150, fill=lc, width=lw)
    d.arc([cx-ar,my+ph-pb_h-ar,cx+ar,my+ph-pb_h+ar], 210, 330, fill=lc, width=lw)

    c2 = 22
    d.arc([mx-c2,my-c2,mx+c2,my+c2], 0, 90, fill=lc, width=lw)
    d.arc([mx+pw-c2,my-c2,mx+pw+c2,my+c2], 90, 180, fill=lc, width=lw)
    d.arc([mx-c2,my+ph-c2,mx+c2,my+ph+c2], 270, 360, fill=lc, width=lw)
    d.arc([mx+pw-c2,my+ph-c2,mx+pw+c2,my+ph+c2], 180, 270, fill=lc, width=lw)

    def dot(x, y, col):
        r = 12
        d.ellipse([x-r,y-r,x+r,y+r], fill=col, outline=WHITE, width=2)

    for x,y in [(W//2,my+35),(W//2-150,mid_y-130),(W//2,mid_y-150),
                (W//2+150,mid_y-130),(W//2-210,mid_y-55),(W//2+210,mid_y-55),
                (W//2,mid_y-75),(W//2-95,my+pb_h+18),(W//2+95,my+pb_h+18)]:
        dot(x,y,(220,175,40))
    for x,y in [(W//2,my+ph-35),(W//2-150,mid_y+130),(W//2,mid_y+150),
                (W//2+150,mid_y+130),(W//2-210,mid_y+55),(W//2+210,mid_y+55),
                (W//2,mid_y+75),(W//2-95,my+ph-pb_h-18),(W//2+95,my+ph-pb_h-18)]:
        dot(x,y,(80,140,255))

    bg = bg.filter(ImageFilter.GaussianBlur(radius=14))
    return bg

# ── Betano logo (real PNG) ────────────────────────────────────────────────────
_betano_logo_cache = None

def get_betano_logo():
    global _betano_logo_cache
    if _betano_logo_cache is None:
        path = os.path.join(FONT_DIR, 'betano_logo.png')
        if os.path.exists(path):
            _betano_logo_cache = Image.open(path).convert("RGBA")
    return _betano_logo_cache

def draw_betano_logo(img, x, y, w=130, h=38):
    """Paste the real Betano logo onto the image"""
    logo = get_betano_logo()
    if logo:
        aspect = logo.width / logo.height
        target_w = int(h * aspect)
        target_h = h
        # If too wide, constrain by width
        if target_w > w:
            target_w = w
            target_h = int(w / aspect)
        resized = logo.resize((target_w, target_h), Image.LANCZOS)
        # Center vertically within the badge area
        paste_y = y + (h - target_h) // 2
        paste_x = x + (w - target_w) // 2
        img.paste(resized, (paste_x, paste_y), resized)

# ── Canvas generator ──────────────────────────────────────────────────────────
def generate_canvas(slips, image_index=0, total_images=1):
    W, H = 1080, 1080

    bg  = make_pitch_bg(W, H)
    ov  = Image.new("RGBA", (W,H), (8, 26, 14, 220))
    img = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Vignette
    vig = Image.new("RGBA", (W,H), (0,0,0,0))
    vd  = ImageDraw.Draw(vig)
    for i in range(100):
        alpha = int(140 * (i/100)**2)
        vd.rectangle([i,i,W-i,H-i], outline=(0,0,0,alpha), width=1)
    img  = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Gold top bar
    draw.rectangle([0,0,W,8], fill=GOLD)

    # ── LOGO centered ────────────────────────────────────────────────────────
    logo_path = os.path.join(FONT_DIR, 'logo_white.png')
    logo_bottom = 20
    if os.path.exists(logo_path):
        logo   = Image.open(logo_path).convert("RGBA")
        logo_h = 80
        logo_w = int(logo_h * logo.width / logo.height)
        logo   = logo.resize((logo_w, logo_h), Image.LANCZOS)
        lx     = (W - logo_w) // 2          # always perfectly centered
        img.paste(logo, (lx, 16), logo)
        logo_bottom = 16 + logo_h
        draw = ImageDraw.Draw(img)

    # Gold separator
    sep_y = logo_bottom + 6
    draw.rectangle([80, sep_y, W-80, sep_y+1], fill=GOLD_DIM)

    # ── "TODAY'S CARD" — BIG headline ────────────────────────────────────────
    header_y   = sep_y + 10
    f_headline = F('BB', 52)          # much bigger — this IS the headline
    n          = len(slips)
    hl_text    = "TODAY'S CARD"
    if total_images > 1:
        hl_text = f"TODAY'S CARD  ·  PART {image_index+1}/{total_images}"

    bb = draw.textbbox((0,0), hl_text, font=f_headline)
    tw = bb[2]-bb[0]
    draw.text(((W-tw)//2, header_y), hl_text, font=f_headline, fill=GOLD)

    # Slip count — clear and readable
    f_slip_count = F('OB', 24)
    sc_text = f"{n} SLIP{'S' if n>1 else ''}  ·  TODAY'S SELECTIONS"
    bb2 = draw.textbbox((0,0), sc_text, font=f_slip_count)
    tw2 = bb2[2]-bb2[0]
    draw.text(((W-tw2)//2, header_y+58), sc_text, font=f_slip_count, fill=GREY)

    # ── CARDS ─────────────────────────────────────────────────────────────────
    PATREON_H  = 120
    patreon_y  = H - PATREON_H - 6
    TOP        = header_y + 96
    BOTTOM     = PATREON_H + 14
    MARGIN     = 30
    GAP        = 14

    avail_h = H - TOP - BOTTOM
    avail_w = W - 2*MARGIN

    cols = 1 if n <= 2 else 2
    rows = math.ceil(n/cols)
    cw   = (avail_w - (cols-1)*GAP) // cols
    ch   = (avail_h - (rows-1)*GAP) // rows
    ch   = min(ch, 300)
    scale = min(1.0, ch / 300.0)

    total_ch = rows*ch + (rows-1)*GAP
    sy = TOP + (avail_h - total_ch) // 2

    for i, slip in enumerate(slips):
        row = i // cols
        col = i % cols

        if cols==2 and n%2==1 and i==n-1:
            cx = MARGIN + avail_w//2 - cw//2
        else:
            cx = MARGIN + col*(cw+GAP)
        cy = sy + row*(ch+GAP)

        # Shadow
        draw.rounded_rectangle([cx+6,cy+6,cx+cw+6,cy+ch+6],
                                radius=18, fill=(3,10,6))

        # Card body
        draw.rounded_rectangle([cx,cy,cx+cw,cy+ch], radius=18, fill=CARD_BG)

        # Subtle inner gradient (darker bottom)
        for yi in range(ch//2, ch, 3):
            alpha = int(60 * (yi-ch//2) / (ch//2))
            overlay_strip = Image.new("RGBA",(cw,3),(0,0,0,alpha))
            img.paste(overlay_strip, (cx, cy+yi), overlay_strip)

        draw = ImageDraw.Draw(img)

        # Card border — glowing green
        draw.rounded_rectangle([cx,cy,cx+cw,cy+ch], radius=18,
                                outline=(20,90,42), width=5)
        draw.rounded_rectangle([cx+2,cy+2,cx+cw-2,cy+ch-2], radius=16,
                                outline=CARD_BORDER, width=2)

        # Gold top stripe
        draw.rounded_rectangle([cx+4,cy+4,cx+cw-4,cy+10],
                                radius=4, fill=GOLD)

        # ── SLIP NUMBER (top-left, clear)
        f_slipnum = F('OB', 15)
        draw.text((cx+18, cy+18), f"SLIP {i+1}", font=f_slipnum, fill=GREY)

        # ── BETANO LOGO (top-right) — real logo
        draw_betano_logo(img, cx+cw-148, cy+12, w=134, h=40)
        draw = ImageDraw.Draw(img)

        # ── BET TYPE — big, white, very readable
        f_btype = F('BB', max(22, int(34 * scale)))
        bt = str(slip.get('bet_type','COMBO')).upper()
        if len(bt) > 20: bt = bt[:20]+'…'
        bb3 = draw.textbbox((0,0), bt, font=f_btype)
        tw3 = bb3[2]-bb3[0]
        btype_y = cy + max(36, int(56 * scale))
        # Text shadow for depth
        draw.text((cx+(cw-tw3)//2+2, btype_y+2), bt, font=f_btype,
                  fill=(0,0,0))
        draw.text((cx+(cw-tw3)//2, btype_y), bt, font=f_btype, fill=WHITE)

        # ── TOTAL ODDS SECTION — hero element
        f_odds_lbl = F('OB', max(14, int(18 * scale)))

        odds_lbl_y = cy + max(60, int(98 * scale))
        # Label with background pill for contrast
        lbl = "TOTAL ODDS"
        lbl_bb = draw.textbbox((0,0), lbl, font=f_odds_lbl)
        lbl_w  = lbl_bb[2]-lbl_bb[0]
        lbl_h  = lbl_bb[3]-lbl_bb[1]
        lbl_x  = cx + 18
        # Pill behind label
        draw.rounded_rectangle([lbl_x-6, odds_lbl_y-4,
                                 lbl_x+lbl_w+6, odds_lbl_y+lbl_h+4],
                                radius=6, fill=(0,0,0,0))
        draw.text((lbl_x, odds_lbl_y), lbl, font=f_odds_lbl, fill=GREY)

        # Odds value — gold, massive, glowing
        odds_raw = str(slip.get('odds','—'))
        odds_y = odds_lbl_y + max(16, int(24 * scale))
        by = cy + ch - 40
        max_h_for_odds = max(20, by - odds_y - 6)

        # Split integer and decimal for clear rendering (decimal always visible)
        if '.' in odds_raw:
            odds_int_str, odds_dec_frac = odds_raw.split('.', 1)
            odds_dec_str = '.' + odds_dec_frac
        else:
            odds_int_str = odds_raw
            odds_dec_str = ''

        # ── Auto-fit: shrink font until odds fit (width AND height)
        max_odds_width = cw - 36   # 18px margin each side
        odds_font_size = 80
        while odds_font_size > 22:
            f_int  = F('BB', odds_font_size)
            f_dec  = F('BB', max(18, odds_font_size - 20))
            int_bb = draw.textbbox((0, 0), odds_int_str, font=f_int)
            int_w  = int_bb[2] - int_bb[0]
            int_h  = int_bb[3] - int_bb[1]
            if odds_dec_str:
                dec_bb = draw.textbbox((0, 0), odds_dec_str, font=f_dec)
                dec_w  = dec_bb[2] - dec_bb[0]
            else:
                dec_w = 0
            if int_w + dec_w + (2 if odds_dec_str else 0) <= max_odds_width and int_h <= max_h_for_odds:
                break
            odds_font_size -= 4

        f_int = F('BB', odds_font_size)
        f_dec = F('BB', max(22, odds_font_size - 20))

        # Measure widths for layout
        int_bb2 = draw.textbbox((0, 0), odds_int_str, font=f_int)
        int_w2  = int_bb2[2] - int_bb2[0]
        int_h2  = int_bb2[3] - int_bb2[1]

        # Draw integer part — glow + shadow + main
        for go in [(3,3,40),(2,2,70),(1,1,100)]:
            gimg = Image.new("RGBA",(W,H),(0,0,0,0))
            gd   = ImageDraw.Draw(gimg)
            gd.text((cx+18+go[0], odds_y+go[1]), odds_int_str,
                    font=f_int, fill=(212,175,55,go[2]))
            img  = Image.alpha_composite(img.convert("RGBA"), gimg).convert("RGB")
            draw = ImageDraw.Draw(img)
        draw.text((cx+20, odds_y+3), odds_int_str, font=f_int, fill=(0,0,0))
        draw.text((cx+18, odds_y),   odds_int_str, font=f_int, fill=GOLD)

        # Draw decimal part — vertically aligned to bottom of integer
        if odds_dec_str:
            dec_x = cx + 18 + int_w2 + 2
            # Align decimal baseline to integer baseline
            dec_bb2 = draw.textbbox((0, 0), odds_dec_str, font=f_dec)
            dec_h2  = dec_bb2[3] - dec_bb2[1]
            dec_y   = odds_y + int_h2 - dec_h2   # baseline-align
            for go in [(2,2,40),(1,1,70)]:
                gimg = Image.new("RGBA",(W,H),(0,0,0,0))
                gd   = ImageDraw.Draw(gimg)
                gd.text((dec_x+go[0], dec_y+go[1]), odds_dec_str,
                        font=f_dec, fill=(212,175,55,go[2]))
                img  = Image.alpha_composite(img.convert("RGBA"), gimg).convert("RGB")
                draw = ImageDraw.Draw(img)
            draw.text((dec_x+2, dec_y+2), odds_dec_str, font=f_dec, fill=(0,0,0))
            draw.text((dec_x,   dec_y),   odds_dec_str, font=f_dec, fill=GOLD)

        # ── BOTTOM INFO ROW — clear, readable ────────────────────────────────
        by = cy + ch - 40

        # Background strip for bottom info
        draw.rounded_rectangle([cx+4, by-8, cx+cw-4, cy+ch-8],
                                radius=10, fill=(8, 28, 14))

        f_legs  = F('OB', 17)    # bigger and bold
        f_stake = F('BB', 20)    # bigger and bold

        legs = slip.get('legs','')
        if legs:
            # Green dot + text
            draw.ellipse([cx+16, by+2, cx+28, by+14], fill=ACCENT_GREEN)
            draw.text((cx+34, by-1), f"{legs} SELECTIONS",
                      font=f_legs, fill=WHITE)

        stake_str = f"STAKE  {slip.get('stake','5%')}"
        sbb = draw.textbbox((0,0), stake_str, font=f_stake)
        sw2 = sbb[2]-sbb[0]
        draw.text((cx+cw-sw2-18, by-2), stake_str, font=f_stake, fill=GOLD)

    # ── PATREON BAR ────────────────────────────────────────────────────────────
    # Dark background with subtle gradient
    for py in range(patreon_y, H-6):
        t = (py - patreon_y) / (H - 6 - patreon_y)
        rc = int(6 + 4*t)
        gc = int(16 + 8*t)
        bc = int(10 + 4*t)
        draw.line([(0, py), (W, py)], fill=(rc, gc, bc))

    # Gold top separator
    draw.rectangle([0, patreon_y, W, patreon_y+3], fill=GOLD)

    # Patreon symbol logo — large and prominent
    pat_logo_path = os.path.join(FONT_DIR, 'patreon_logo.png')
    pat_logo_h = 80
    pat_pad = 30
    pat_y2 = patreon_y + (PATREON_H - pat_logo_h) // 2
    pat_logo_w_actual = pat_pad  # fallback
    if os.path.exists(pat_logo_path):
        pat_logo = Image.open(pat_logo_path).convert("RGBA")
        aspect = pat_logo.width / pat_logo.height
        pat_logo_w_actual = int(pat_logo_h * aspect)
        pat_logo_resized = pat_logo.resize((pat_logo_w_actual, pat_logo_h), Image.LANCZOS)
        img.paste(pat_logo_resized, (pat_pad, pat_y2), pat_logo_resized)
        draw = ImageDraw.Draw(img)

    # Vertical gold divider after logo
    div_x = pat_pad + pat_logo_w_actual + 22
    draw.rectangle([div_x, patreon_y+18, div_x+2, H-18], fill=GOLD_DIM)

    # CTA text block
    tx = div_x + 22
    mid_y3 = patreon_y + PATREON_H//2

    # Line 1 — big bold hook
    draw.text((tx, mid_y3-34), "Full Slips + Bankroll & Risk Management + Masterclass — only £10/month",
              font=F('BB', 24), fill=WHITE)
    # Line 2 — social proof + link
    draw.text((tx, mid_y3+2), "Join 500+ smart bettors on Patreon",
              font=F('OB', 18), fill=GOLD)
    # Line 3 — URL
    draw.text((tx, mid_y3+26), "patreon.com/Matchdaymentors",
              font=F('OR', 16), fill=GREY)

    # Gold bottom bar
    draw.rectangle([0, H-6, W, H], fill=GOLD)

    return img


def generate_images(slips_data):
    # Always generate a single image with all slips
    return [generate_canvas(slips_data, 0, 1)]


# ── Story generator (1080×1920 — Instagram & Facebook Stories) ───────────────
def generate_story(slips, image_index=0, total_images=1):
    """Generate 1080x1920 story format for Instagram/Facebook Stories."""
    W, H = 1080, 1920

    bg  = make_pitch_bg(W, H)
    ov  = Image.new("RGBA", (W, H), (8, 26, 14, 220))
    img = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Vignette
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd  = ImageDraw.Draw(vig)
    for i in range(100):
        alpha = int(140 * (i/100)**2)
        vd.rectangle([i, i, W-i, H-i], outline=(0, 0, 0, alpha), width=1)
    img  = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Gold top bar
    draw.rectangle([0, 0, W, 10], fill=GOLD)

    # ── Logo ─────────────────────────────────────────────────────────────────
    logo_path = os.path.join(FONT_DIR, 'logo_white.png')
    logo_bottom = 30
    if os.path.exists(logo_path):
        logo   = Image.open(logo_path).convert("RGBA")
        logo_h = 110
        logo_w = int(logo_h * logo.width / logo.height)
        logo   = logo.resize((logo_w, logo_h), Image.LANCZOS)
        lx     = (W - logo_w) // 2
        img.paste(logo, (lx, 20), logo)
        logo_bottom = 20 + logo_h
        draw = ImageDraw.Draw(img)

    # Gold separator
    sep_y = logo_bottom + 12
    draw.rectangle([60, sep_y, W-60, sep_y+2], fill=GOLD_DIM)

    # ── Headline ──────────────────────────────────────────────────────────────
    header_y   = sep_y + 18
    f_headline = F('BB', 68)
    n          = len(slips)
    hl_text    = "TODAY'S CARD"
    if total_images > 1:
        hl_text = f"TODAY'S CARD  ·  {image_index+1}/{total_images}"
    bb = draw.textbbox((0, 0), hl_text, font=f_headline)
    draw.text(((W-(bb[2]-bb[0]))//2, header_y), hl_text, font=f_headline, fill=GOLD)

    f_count = F('OB', 28)
    sc_text = f"{n} SLIP{'S' if n > 1 else ''}  ·  TODAY'S SELECTIONS"
    bb2 = draw.textbbox((0, 0), sc_text, font=f_count)
    draw.text(((W-(bb2[2]-bb2[0]))//2, header_y+80), sc_text, font=f_count, fill=GREY)

    # ── Cards (single column, stacked) ────────────────────────────────────────
    CTA_H     = 220
    TOP       = header_y + 140
    BOT_MARG  = CTA_H + 20
    MARGIN    = 36
    GAP       = 18

    avail_h   = H - TOP - BOT_MARG
    cw        = W - 2 * MARGIN
    ch        = min((avail_h - (n-1)*GAP) // max(n, 1), 360)
    story_scale = min(1.0, ch / 360.0)
    total_h   = n*ch + (n-1)*GAP
    sy        = TOP + (avail_h - total_h) // 2

    for i, slip in enumerate(slips):
        cx = MARGIN
        cy = sy + i*(ch+GAP)

        # Shadow
        draw.rounded_rectangle([cx+6, cy+6, cx+cw+6, cy+ch+6], radius=20, fill=(3,10,6))
        # Card body
        draw.rounded_rectangle([cx, cy, cx+cw, cy+ch], radius=20, fill=CARD_BG)

        # Gradient
        for yi in range(ch//2, ch, 3):
            alpha = int(60*(yi-ch//2)/(ch//2))
            strip = Image.new("RGBA", (cw, 3), (0,0,0,alpha))
            img.paste(strip, (cx, cy+yi), strip)
        draw = ImageDraw.Draw(img)

        # Border
        draw.rounded_rectangle([cx,cy,cx+cw,cy+ch], radius=20, outline=(20,90,42), width=5)
        draw.rounded_rectangle([cx+2,cy+2,cx+cw-2,cy+ch-2], radius=18, outline=CARD_BORDER, width=2)
        # Gold stripe
        draw.rounded_rectangle([cx+4,cy+4,cx+cw-4,cy+12], radius=4, fill=GOLD)

        # Slip number
        draw.text((cx+20, cy+20), f"SLIP {i+1}", font=F('OB', 17), fill=GREY)

        # Betano logo
        draw_betano_logo(img, cx+cw-160, cy+14, w=144, h=44)
        draw = ImageDraw.Draw(img)

        # Bet type
        f_btype = F('BB', max(24, int(38 * story_scale)))
        bt = str(slip.get('bet_type','COMBO')).upper()
        if len(bt) > 20: bt = bt[:20]+'…'
        bb3 = draw.textbbox((0,0), bt, font=f_btype)
        tw3 = bb3[2]-bb3[0]
        sbtype_y = cy + max(40, int(62 * story_scale))
        draw.text((cx+(cw-tw3)//2+2, sbtype_y+2), bt, font=f_btype, fill=(0,0,0))
        draw.text((cx+(cw-tw3)//2,   sbtype_y),   bt, font=f_btype, fill=WHITE)

        # ── Odds (same auto-fit + split rendering) ──────────────────────────
        odds_raw = str(slip.get('odds','—'))
        odds_y = cy + max(70, int(110 * story_scale))

        if '.' in odds_raw:
            odds_int_str, odds_dec_frac = odds_raw.split('.', 1)
            odds_dec_str = '.' + odds_dec_frac
        else:
            odds_int_str = odds_raw
            odds_dec_str = ''

        story_by = cy + ch - 48
        story_max_h = max(20, story_by - odds_y - 6)
        max_odds_width = cw - 36
        odds_font_size = 88
        while odds_font_size > 22:
            f_int = F('BB', odds_font_size)
            f_dec = F('BB', max(18, odds_font_size - 20))
            int_bb = draw.textbbox((0,0), odds_int_str, font=f_int)
            int_w  = int_bb[2]-int_bb[0]
            int_h  = int_bb[3]-int_bb[1]
            dec_w  = 0
            if odds_dec_str:
                dec_bb = draw.textbbox((0,0), odds_dec_str, font=f_dec)
                dec_w  = dec_bb[2]-dec_bb[0]
            if int_w + dec_w + (2 if odds_dec_str else 0) <= max_odds_width and int_h <= story_max_h:
                break
            odds_font_size -= 4

        f_int = F('BB', odds_font_size)
        f_dec = F('BB', max(22, odds_font_size - 20))
        int_bb2 = draw.textbbox((0,0), odds_int_str, font=f_int)
        int_w2  = int_bb2[2]-int_bb2[0]
        int_h2  = int_bb2[3]-int_bb2[1]

        for go in [(3,3,40),(2,2,70),(1,1,100)]:
            gimg = Image.new("RGBA",(W,H),(0,0,0,0))
            gd   = ImageDraw.Draw(gimg)
            gd.text((cx+18+go[0], odds_y+go[1]), odds_int_str, font=f_int, fill=(212,175,55,go[2]))
            img  = Image.alpha_composite(img.convert("RGBA"), gimg).convert("RGB")
            draw = ImageDraw.Draw(img)
        draw.text((cx+20, odds_y+3), odds_int_str, font=f_int, fill=(0,0,0))
        draw.text((cx+18, odds_y),   odds_int_str, font=f_int, fill=GOLD)

        if odds_dec_str:
            dec_x  = cx + 18 + int_w2 + 2
            dec_bb2= draw.textbbox((0,0), odds_dec_str, font=f_dec)
            dec_h2 = dec_bb2[3]-dec_bb2[1]
            dec_y  = odds_y + int_h2 - dec_h2
            for go in [(2,2,40),(1,1,70)]:
                gimg = Image.new("RGBA",(W,H),(0,0,0,0))
                gd   = ImageDraw.Draw(gimg)
                gd.text((dec_x+go[0], dec_y+go[1]), odds_dec_str, font=f_dec, fill=(212,175,55,go[2]))
                img  = Image.alpha_composite(img.convert("RGBA"), gimg).convert("RGB")
                draw = ImageDraw.Draw(img)
            draw.text((dec_x+2, dec_y+2), odds_dec_str, font=f_dec, fill=(0,0,0))
            draw.text((dec_x,   dec_y),   odds_dec_str, font=f_dec, fill=GOLD)

        # Bottom info row
        by = cy + ch - 48
        draw.rounded_rectangle([cx+4, by-8, cx+cw-4, cy+ch-8], radius=12, fill=(8,28,14))

        legs = slip.get('legs','')
        if legs:
            draw.ellipse([cx+18, by+3, cx+32, by+17], fill=ACCENT_GREEN)
            draw.text((cx+40, by), f"{legs} SELECTIONS", font=F('OB', 19), fill=WHITE)

        stake_str = f"STAKE  {slip.get('stake','5%')}"
        sbb = draw.textbbox((0,0), stake_str, font=F('BB', 22))
        draw.text((cx+cw-(sbb[2]-sbb[0])-20, by-1), stake_str, font=F('BB', 22), fill=GOLD)

    # ── CTA section (bottom) ─────────────────────────────────────────────────
    cta_y = H - CTA_H - 10

    # Dark BG gradient
    for py in range(cta_y, H-10):
        t  = (py-cta_y) / max(H-10-cta_y, 1)
        rc = int(6+4*t); gc = int(16+8*t); bc = int(10+4*t)
        draw.line([(0,py),(W,py)], fill=(rc,gc,bc))

    draw.rectangle([0, cta_y, W, cta_y+3], fill=GOLD)

    # Gold CTA button
    MARGIN_BTN = 50
    btn_y = cta_y + 22
    btn_h = 78
    draw.rounded_rectangle([MARGIN_BTN, btn_y, W-MARGIN_BTN, btn_y+btn_h],
                            radius=39, fill=GOLD)
    f_btn = F('BB', 28)
    btn_text = "SEE FULL ANALYSIS ON PATREON"
    btn_bb   = draw.textbbox((0,0), btn_text, font=f_btn)
    btn_tw   = btn_bb[2]-btn_bb[0]
    btn_th   = btn_bb[3]-btn_bb[1]
    draw.text(((W-btn_tw)//2, btn_y+(btn_h-btn_th)//2), btn_text, font=f_btn, fill=(10,34,18))

    # URL
    url_text = "patreon.com/Matchdaymentors"
    url_bb   = draw.textbbox((0,0), url_text, font=F('OR',22))
    draw.text(((W-(url_bb[2]-url_bb[0]))//2, btn_y+btn_h+14), url_text, font=F('OR',22), fill=GREY)

    # Social proof line
    mem_text = "Join 500+ smart bettors  ·  Only £10/month"
    mem_bb   = draw.textbbox((0,0), mem_text, font=F('OB',24))
    draw.text(((W-(mem_bb[2]-mem_bb[0]))//2, btn_y+btn_h+46), mem_text, font=F('OB',24), fill=GOLD)

    # Gold bottom bar
    draw.rectangle([0, H-10, W, H], fill=GOLD)

    return img


def generate_story_images(slips_data):
    """Generate story format (1080x1920) for all slips in one image."""
    return [generate_story(slips_data, 0, 1)]



# ── Custom card generator (branded MM post/story cards) ────────────────────

def _wrap_text_custom(text, font, draw, max_width):
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [""]


def generate_custom_card(title, subtitle=""):
    """Generate a 1080x1080 branded MM post card for custom/promo content."""
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    # Dark gradient background
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0]*(1-t) + BG_BOT[0]*t)
        gv = int(BG_TOP[1]*(1-t) + BG_BOT[1]*t)
        b = int(BG_TOP[2]*(1-t) + BG_BOT[2]*t)
        draw.line([(0, y), (W, y)], fill=(r, gv, b))
    # Vignette
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for i in range(80):
        alpha = int(160 * (i/80)**2)
        vd.rectangle([i, i, W-i, H-i], outline=(0, 0, 0, alpha), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")
    draw = ImageDraw.Draw(img)
    # Green accent bars
    draw.rectangle([0, 0, W, 8], fill=ACCENT_GREEN)
    draw.rectangle([0, H-8, W, H], fill=ACCENT_GREEN)
    # Logo
    logo_path = os.path.join(FONT_DIR, 'logo_white.png')
    logo_bottom = 30
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_h = 80
        logo_w = int(logo_h * logo.width / logo.height)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        img.paste(logo, ((W - logo_w) // 2, 20), logo)
        logo_bottom = 20 + logo_h
        draw = ImageDraw.Draw(img)
    else:
        f_brand = F('BB', 44)
        brand_text = "MATCHDAY MENTORS"
        bw = draw.textlength(brand_text, font=f_brand)
        draw.text(((W-bw)//2+2, 42), brand_text, font=f_brand, fill=(0, 0, 0))
        draw.text(((W-bw)//2, 40), brand_text, font=f_brand, fill=WHITE)
        logo_bottom = 100
    # Separator
    sep_y = logo_bottom + 10
    draw.rectangle([(W-400)//2, sep_y, (W+400)//2, sep_y+2], fill=GOLD_DIM)
    # Title auto-fit
    title_start_y = sep_y + 30
    available_h = H - title_start_y - 200
    title_size = 88
    while title_size > 28:
        f_title = F('BB', title_size)
        lines = _wrap_text_custom(title, f_title, draw, W - 120)
        if len(lines) * (title_size + 14) <= available_h:
            break
        title_size -= 4
    f_title = F('BB', title_size)
    lines = _wrap_text_custom(title, f_title, draw, W - 120)
    line_h = title_size + 14
    total_title_h = len(lines) * line_h
    title_y = title_start_y + (available_h - total_title_h) // 2
    for line in lines:
        tw = draw.textlength(line, font=f_title)
        draw.text(((W-tw)//2+3, title_y+3), line, font=f_title, fill=(0, 0, 0))
        draw.text(((W-tw)//2, title_y), line, font=f_title, fill=WHITE)
        title_y += line_h
    # Subtitle
    if subtitle:
        f_sub = F('OB', 34)
        sw = draw.textlength(subtitle, font=f_sub)
        draw.text(((W-sw)//2, title_y+20), subtitle, font=f_sub, fill=GREY)
    # Handle
    f_handle = F('OB', 28)
    handle = "@MatchdayMentors"
    hw = draw.textlength(handle, font=f_handle)
    draw.text(((W-hw)//2, H-55), handle, font=f_handle, fill=ACCENT_GREEN)
    return img


def generate_custom_story(title, subtitle=""):
    """Generate a 1080x1920 branded MM story card for custom/promo content."""
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    # Dark gradient background
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0]*(1-t) + BG_BOT[0]*t)
        gv = int(BG_TOP[1]*(1-t) + BG_BOT[1]*t)
        b = int(BG_TOP[2]*(1-t) + BG_BOT[2]*t)
        draw.line([(0, y), (W, y)], fill=(r, gv, b))
    # Vignette
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for i in range(100):
        alpha = int(160 * (i/100)**2)
        vd.rectangle([i, i, W-i, H-i], outline=(0, 0, 0, alpha), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")
    draw = ImageDraw.Draw(img)
    # Green accent bars
    draw.rectangle([0, 0, W, 10], fill=ACCENT_GREEN)
    draw.rectangle([0, H-10, W, H], fill=ACCENT_GREEN)
    # Logo
    logo_path = os.path.join(FONT_DIR, 'logo_white.png')
    logo_bottom = 50
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_h = 110
        logo_w = int(logo_h * logo.width / logo.height)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        img.paste(logo, ((W - logo_w) // 2, 40), logo)
        logo_bottom = 40 + logo_h
        draw = ImageDraw.Draw(img)
    else:
        f_brand = F('BB', 52)
        brand_text = "MATCHDAY MENTORS"
        bw = draw.textlength(brand_text, font=f_brand)
        draw.text(((W-bw)//2+2, 122), brand_text, font=f_brand, fill=(0, 0, 0))
        draw.text(((W-bw)//2, 120), brand_text, font=f_brand, fill=WHITE)
        logo_bottom = 190
    # Separator
    sep_y = logo_bottom + 20
    draw.rectangle([(W-500)//2, sep_y, (W+500)//2, sep_y+2], fill=GOLD_DIM)
    # Title auto-fit
    title_start_y = sep_y + 50
    available_h = H - title_start_y - 350
    title_size = 100
    while title_size > 32:
        f_title = F('BB', title_size)
        lines = _wrap_text_custom(title, f_title, draw, W - 120)
        if len(lines) * (title_size + 18) <= available_h:
            break
        title_size -= 4
    f_title = F('BB', title_size)
    lines = _wrap_text_custom(title, f_title, draw, W - 120)
    line_h = title_size + 18
    total_title_h = len(lines) * line_h
    title_y = title_start_y + (available_h - total_title_h) // 2
    for line in lines:
        tw = draw.textlength(line, font=f_title)
        draw.text(((W-tw)//2+3, title_y+3), line, font=f_title, fill=(0, 0, 0))
        draw.text(((W-tw)//2, title_y), line, font=f_title, fill=WHITE)
        title_y += line_h
    # Subtitle
    if subtitle:
        f_sub = F('OB', 40)
        sub_lines = _wrap_text_custom(subtitle, f_sub, draw, W - 140)
        sub_y = title_y + 30
        for sl in sub_lines:
            sw = draw.textlength(sl, font=f_sub)
            draw.text(((W-sw)//2, sub_y), sl, font=f_sub, fill=GREY)
            sub_y += 54
    # Handle
    f_handle = F('OB', 34)
    handle = "@MatchdayMentors"
    hw = draw.textlength(handle, font=f_handle)
    draw.text(((W-hw)//2, H-80), handle, font=f_handle, fill=ACCENT_GREEN)
    return img


# ── Match result card ──────────────────────────────────────────────────────

def _fetch_logo(url, size):
    """Download a logo from a URL, return RGBA PIL image or None."""
    try:
        resp = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            logo = Image.open(BytesIO(resp.content)).convert("RGBA")
            logo = logo.resize(size, Image.LANCZOS)
            return logo
    except Exception:
        pass
    return None


def _paste_team_block(img, draw, cx, cy, logo, team_name, circle_r, font_size=36):
    """Draw a circular logo + team name centred at (cx, cy)."""
    circ_size = circle_r * 2
    circle_bg = Image.new("RGBA", (circ_size + 8, circ_size + 8), (0, 0, 0, 0))
    cd = ImageDraw.Draw(circle_bg)
    cd.ellipse([2, 2, circ_size + 5, circ_size + 5], fill=(255, 255, 255, 245))
    img.paste(circle_bg, (cx - circle_r - 4, cy - circle_r - 4), circle_bg)
    if logo:
        max_logo = int(circle_r * 1.55)
        lw, lh = logo.size
        scale = min(max_logo / lw, max_logo / lh)
        ns = (int(lw * scale), int(lh * scale))
        logo_s = logo.resize(ns, Image.LANCZOS)
        img.paste(logo_s, (cx - ns[0] // 2, cy - ns[1] // 2), logo_s)
    draw = ImageDraw.Draw(img)
    f_name = F('BB', font_size)
    words = team_name.upper().split()
    lines = [' '.join(words)] if len(words) <= 2 else [' '.join(words[:2]), ' '.join(words[2:])]
    ny = cy + circle_r + 18
    for ln in lines:
        lw_px = draw.textlength(ln, font=f_name)
        draw.text((cx - int(lw_px) // 2, ny), ln, font=f_name, fill=(255, 255, 255))
        ny += font_size + 8
    return draw


def generate_match_card(home_team, away_team, home_score, away_score,
                        home_logo_url="", away_logo_url="",
                        title="MATCH RESULT", subtitle="", label="PREMIER LEAGUE"):
    """Generate a 1080x1080 match result card with team logos and score."""
    W, H = 1080, 1080

    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] * (1 - t) + BG_BOT[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOT[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOT[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    draw.rectangle([0, 0, W, 10], fill=ACCENT_GREEN)
    draw.rectangle([0, H - 10, W, H], fill=ACCENT_GREEN)

    f_label = F('OB', 26)
    lbl = label.upper()
    lw = int(draw.textlength(lbl, font=f_label))
    draw.text(((W - lw) // 2, 22), lbl, font=f_label, fill=GREY)
    dy = 36
    for dx in [(W - lw) // 2 - 22, (W + lw) // 2 + 10]:
        draw.ellipse([dx, dy - 5, dx + 12, dy + 5], fill=ACCENT_GREEN)

    LOGO_SIZE = (200, 200)
    home_logo_img = _fetch_logo(home_logo_url, LOGO_SIZE) if home_logo_url else None
    away_logo_img = _fetch_logo(away_logo_url, LOGO_SIZE) if away_logo_url else None

    img = img.convert("RGBA")
    CIRCLE_R = 120
    LOGO_CY = 340
    draw = _paste_team_block(img, draw, 210, LOGO_CY, home_logo_img, home_team, CIRCLE_R, 36)
    draw = _paste_team_block(img, draw, W - 210, LOGO_CY, away_logo_img, away_team, CIRCLE_R, 36)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    f_score = F('BB', 180)
    f_dash  = F('BB', 100)
    hs = str(home_score)
    as_ = str(away_score)
    dash = "-"
    hs_w  = int(draw.textlength(hs,   font=f_score))
    as_w  = int(draw.textlength(as_,  font=f_score))
    dsh_w = int(draw.textlength(dash, font=f_dash))
    gap   = 20
    total_w = hs_w + gap + dsh_w + gap + as_w
    sx = (W - total_w) // 2
    score_y = 195
    h_col = GOLD if int(home_score) > int(away_score) else WHITE
    a_col = GOLD if int(away_score) > int(home_score) else WHITE
    draw.text((sx, score_y), hs, font=f_score, fill=h_col)
    draw.text((sx + hs_w + gap, score_y + 42), dash, font=f_dash, fill=GOLD_DIM)
    draw.text((sx + hs_w + gap + dsh_w + gap, score_y), as_, font=f_score, fill=a_col)

    div_y = 595
    draw.rectangle([80, div_y, W - 80, div_y + 4], fill=GOLD_DIM)

    available_w = W - 140
    t_size = 80
    while t_size > 28:
        f_t = F('BB', t_size)
        t_lines = _wrap_text_custom(title, f_t, draw, available_w)
        if len(t_lines) <= 3:
            break
        t_size -= 4
    f_t = F('BB', t_size)
    t_lines = _wrap_text_custom(title, f_t, draw, available_w)
    ty = div_y + 26
    for ln in t_lines:
        lw_px = draw.textlength(ln, font=f_t)
        draw.text(((W - int(lw_px)) // 2, ty), ln, font=f_t, fill=WHITE)
        ty += t_size + 12

    if subtitle:
        f_sub = F('OB', 30)
        sub_lines = _wrap_text_custom(subtitle, f_sub, draw, W - 160)
        ty += 6
        for ln in sub_lines:
            lw_px = draw.textlength(ln, font=f_sub)
            draw.text(((W - int(lw_px)) // 2, ty), ln, font=f_sub, fill=(160, 160, 185))
            ty += 44

    f_h = F('OB', 28)
    handle = "@MatchdayMentors"
    hw = draw.textlength(handle, font=f_h)
    draw.text(((W - int(hw)) // 2, H - 54), handle, font=f_h, fill=(160, 160, 185))
    return img


def generate_match_story(home_team, away_team, home_score, away_score,
                         home_logo_url="", away_logo_url="",
                         title="MATCH RESULT", subtitle="", label="PREMIER LEAGUE"):
    """Generate a 1080x1920 match result story card with team logos and score."""
    W, H = 1080, 1920

    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] * (1 - t) + BG_BOT[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOT[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOT[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    draw.rectangle([0, 0, W, 12], fill=ACCENT_GREEN)
    draw.rectangle([0, H - 12, W, H], fill=ACCENT_GREEN)

    f_label = F('OB', 32)
    lbl = label.upper()
    lw = int(draw.textlength(lbl, font=f_label))
    draw.text(((W - lw) // 2, 30), lbl, font=f_label, fill=GREY)
    dy = 48
    for dx in [(W - lw) // 2 - 28, (W + lw) // 2 + 14]:
        draw.ellipse([dx, dy - 6, dx + 14, dy + 6], fill=ACCENT_GREEN)

    LOGO_SIZE = (260, 260)
    home_logo_img = _fetch_logo(home_logo_url, LOGO_SIZE) if home_logo_url else None
    away_logo_img = _fetch_logo(away_logo_url, LOGO_SIZE) if away_logo_url else None

    img = img.convert("RGBA")
    CIRCLE_R = 155
    LOGO_CY = 530
    draw = _paste_team_block(img, draw, 210, LOGO_CY, home_logo_img, home_team, CIRCLE_R, 42)
    draw = _paste_team_block(img, draw, W - 210, LOGO_CY, away_logo_img, away_team, CIRCLE_R, 42)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    f_score = F('BB', 240)
    f_dash  = F('BB', 130)
    hs = str(home_score)
    as_ = str(away_score)
    dash = "-"
    hs_w  = int(draw.textlength(hs,   font=f_score))
    as_w  = int(draw.textlength(as_,  font=f_score))
    dsh_w = int(draw.textlength(dash, font=f_dash))
    gap   = 24
    total_w = hs_w + gap + dsh_w + gap + as_w
    sx = (W - total_w) // 2
    score_y = 290
    h_col = GOLD if int(home_score) > int(away_score) else WHITE
    a_col = GOLD if int(away_score) > int(home_score) else WHITE
    draw.text((sx, score_y), hs, font=f_score, fill=h_col)
    draw.text((sx + hs_w + gap, score_y + 56), dash, font=f_dash, fill=GOLD_DIM)
    draw.text((sx + hs_w + gap + dsh_w + gap, score_y), as_, font=f_score, fill=a_col)

    div_y = 870
    draw.rectangle([80, div_y, W - 80, div_y + 5], fill=GOLD_DIM)

    available_w = W - 140
    t_size = 88
    while t_size > 32:
        f_t = F('BB', t_size)
        t_lines = _wrap_text_custom(title, f_t, draw, available_w)
        if len(t_lines) <= 4:
            break
        t_size -= 4
    f_t = F('BB', t_size)
    t_lines = _wrap_text_custom(title, f_t, draw, available_w)
    ty = div_y + 36
    for ln in t_lines:
        lw_px = draw.textlength(ln, font=f_t)
        draw.text(((W - int(lw_px)) // 2, ty), ln, font=f_t, fill=WHITE)
        ty += t_size + 16

    if subtitle:
        f_sub = F('OB', 38)
        sub_lines = _wrap_text_custom(subtitle, f_sub, draw, W - 160)
        ty += 10
        for ln in sub_lines:
            lw_px = draw.textlength(ln, font=f_sub)
            draw.text(((W - int(lw_px)) // 2, ty), ln, font=f_sub, fill=(160, 160, 185))
            ty += 56

    f_h = F('OB', 36)
    handle = "@MatchdayMentors"
    hw = draw.textlength(handle, font=f_h)
    draw.text(((W - int(hw)) // 2, H - 72), handle, font=f_h, fill=(160, 160, 185))
    return img


if __name__ == '__main__':
    test3 = [
        {"bet_type": "4-Fold", "odds": 2.70, "stake": "5%", "legs": 4},
        {"bet_type": "4-Fold", "odds": 2.97, "stake": "5%", "legs": 4},
        {"bet_type": "3-Fold", "odds": 3.45, "stake": "3%", "legs": 3},
    ]
    for i, img in enumerate(generate_images(test3)):
        p = f"/mnt/user-data/outputs/mm_v4_{i+1}.png"
        img.save(p, quality=95)
        print(f"Saved: {p}")
