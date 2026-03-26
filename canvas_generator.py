from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import math, os, requests, base64
from io import BytesIO

# в”Ђв”Ђ Palette в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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

# в”Ђв”Ђ Country flag data
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

# в”Ђв”Ђ Pitch background в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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

# в”Ђв”Ђ Betano logo (real PNG) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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

# в”Ђв”Ђ Canvas generator в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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

    # в”Ђв”Ђ LOGO centered в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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

    # в”Ђв”Ђ "TODAY'S CARD" вЂ” BIG headline в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    header_y   = sep_y + 10
    f_headline = F('BB', 52)          # much bigger вЂ” this IS the headline
    n          = len(slips)
    hl_text    = "TODAY'S CARD"
    if total_images > 1:
        hl_text = f"TODAY'S CARD  В·  PART {image_index+1}/{total_images}"

    bb = draw.textbbox((0,0), hl_text, font=f_headline)
    tw = bb[2]-bb[0]
    draw.text(((W-tw)//2, header_y), hl_text, font=f_headline, fill=GOLD)

    # Slip count вЂ” clear and readable
    f_slip_count = F('OB', 24)
    sc_text = f"{n} SLIP{'S' if n>1 else ''}  В·  TODAY'S SELECTIONS"
    bb2 = draw.textbbox((0,0), sc_text, font=f_slip_count)
    tw2 = bb2[2]-bb2[0]
    draw.text(((W-tw2)//2, header_y+58), sc_text, font=f_slip_count, fill=GREY)

    # в”Ђв”Ђ CARDS в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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

        # Card border вЂ” glowing green
        draw.rounded_rectangle([cx,cy,cx+cw,cy+ch], radius=18,
                                outline=(20,90,42), width=5)
        draw.rounded_rectangle([cx+2,cy+2,cx+cw-2,cy+ch-2], radius=16,
                                outline=CARD_BORDER, width=2)

        # Gold top stripe
        draw.rounded_rectangle([cx+4,cy+4,cx+cw-4,cy+10],
                                radius=4, fill=GOLD)

        # в”Ђв”Ђ SLIP NUMBER (top-left, clear)
        f_slipnum = F('OB', 15)
        draw.text((cx+18, cy+18), f"SLIP {i+1}", font=f_slipnum, fill=GREY)

        # в”Ђв”Ђ BETANO LOGO (top-right) вЂ” real logo
        draw_betano_logo(img, cx+cw-148, cy+12, w=134, h=40)
        draw = ImageDraw.Draw(img)

        # в”Ђв”Ђ BET TYPE вЂ” big, white, very readable
        f_btype = F('BB', max(22, int(34 * scale)))
        bt = str(slip.get('bet_type','COMBO')).upper()
        if len(bt) > 20: bt = bt[:20]+'вЂ¦'
        bb3 = draw.textbbox((0,0), bt, font=f_btype)
        tw3 = bb3[2]-bb3[0]
        btype_y = cy + max(36, int(56 * scale))
        # Text shadow for depth
        draw.text((cx+(cw-tw3)//2+2, btype_y+2), bt, font=f_btype,
                  fill=(0,0,0))
        draw.text((cx+(cw-tw3)//2, btype_y), bt, font=f_btype, fill=WHITE)

        # в”Ђв”Ђ TOTAL ODDS SECTION вЂ” hero element
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

        # Odds value вЂ” gold, massive, glowing
        odds_raw = str(slip.get('odds','вЂ”'))
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

        # в”Ђв”Ђ Auto-fit: shrink font until odds fit (width AND height)
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

        # Draw integer part вЂ” glow + shadow + main
        for go in [(3,3,40),(2,2,70),(1,1,100)]:
            gimg = Image.new("RGBA",(W,H),(0,0,0,0))
            gd   = ImageDraw.Draw(gimg)
            gd.text((cx+18+go[0], odds_y+go[1]), odds_int_str,
                    font=f_int, fill=(212,175,55,go[2]))
            img  = Image.alpha_composite(img.convert("RGBA"), gimg).convert("RGB")
            draw = ImageDraw.Draw(img)
        draw.text((cx+20, odds_y+3), odds_int_str, font=f_int, fill=(0,0,0))
        draw.text((cx+18, odds_y),   odds_int_str, font=f_int, fill=GOLD)

        # Draw decimal part вЂ” vertically aligned to bottom of integer
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

        # в”Ђв”Ђ BOTTOM INFO ROW вЂ” clear, readable в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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

    # в”Ђв”Ђ PATREON BAR в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    # Dark background with subtle gradient
    for py in range(patreon_y, H-6):
        t = (py - patreon_y) / (H - 6 - patreon_y)
        rc = int(6 + 4*t)
        gc = int(16 + 8*t)
        bc = int(10 + 4*t)
        draw.line([(0, py), (W, py)], fill=(rc, gc, bc))

    # Gold top separator
    draw.rectangle([0, patreon_y, W, patreon_y+3], fill=GOLD)

    # Patreon symbol logo вЂ” large and prominent
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

    # Line 1 вЂ” big bold hook
    draw.text((tx, mid_y3-34), "Full Slips + Bankroll & Risk Management + Masterclass вЂ” only ВЈ10/month",
              font=F('BB', 24), fill=WHITE)
    # Line 2 вЂ” social proof + link
    draw.text((tx, mid_y3+2), "Join 500+ smart bettors on Patreon",
              font=F('OB', 18), fill=GOLD)
    # Line 3 вЂ” URL
    draw.text((tx, mid_y3+26), "patreon.com/Matchdaymentors",
              font=F('OR', 16), fill=GREY)

    # Gold bottom bar
    draw.rectangle([0, H-6, W, H], fill=GOLD)

    return img


def generate_images(slips_data):
    # Always generate a single image with all slips
    return [generate_canvas(slips_data, 0, 1)]


# в”Ђв”Ђ Story generator (1080Г—1920 вЂ” Instagram & Facebook Stories) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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

    # в”Ђв”Ђ Logo в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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

    # в”Ђв”Ђ Headline в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    header_y   = sep_y + 18
    f_headline = F('BB', 68)
    n          = len(slips)
    hl_text    = "TODAY'S CARD"
    if total_images > 1:
        hl_text = f"TODAY'S CARD  В·  {image_index+1}/{total_images}"
    bb = draw.textbbox((0, 0), hl_text, font=f_headline)
    draw.text(((W-(bb[2]-bb[0]))//2, header_y), hl_text, font=f_headline, fill=GOLD)

    f_count = F('OB', 28)
    sc_text = f"{n} SLIP{'S' if n > 1 else ''}  В·  TODAY'S SELECTIONS"
    bb2 = draw.textbbox((0, 0), sc_text, font=f_count)
    draw.text(((W-(bb2[2]-bb2[0]))//2, header_y+80), sc_text, font=f_count, fill=GREY)

    # в”Ђв”Ђ Cards (single column, stacked) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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
        if len(bt) > 20: bt = bt[:20]+'вЂ¦'
        bb3 = draw.textbbox((0,0), bt, font=f_btype)
        tw3 = bb3[2]-bb3[0]
        sbtype_y = cy + max(40, int(62 * story_scale))
        draw.text((cx+(cw-tw3)//2+2, sbtype_y+2), bt, font=f_btype, fill=(0,0,0))
        draw.text((cx+(cw-tw3)//2,   sbtype_y),   bt, font=f_btype, fill=WHITE)

        # в”Ђв”Ђ Odds (same auto-fit + split rendering) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
        odds_raw = str(slip.get('odds','вЂ”'))
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

    # в”Ђв”Ђ CTA section (bottom) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
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
    mem_text = "Join 500+ smart bettors  В·  Only ВЈ10/month"
    mem_bb   = draw.textbbox((0,0), mem_text, font=F('OB',24))
    draw.text(((W-(mem_bb[2]-mem_bb[0]))//2, btn_y+btn_h+46), mem_text, font=F('OB',24), fill=GOLD)

    # Gold bottom bar
    draw.rectangle([0, H-10, W, H], fill=GOLD)

    return img


def generate_story_images(slips_data):
    """Generate story format (1080x1920) for all slips in one image."""
    return [generate_story(slips_data, 0, 1)]



# в”Ђв”Ђ Custom card generator (branded MM post/story cards) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

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


# в”Ђв”Ђ Match result card в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

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


# в”Ђв”Ђ Daily Results infographic (1080Г—1920) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

def _fetch_logo_crisp(url, display_size):
    """
    Fetch a team logo preserving its original aspect ratio, then centre it
    on a transparent display_size Г— display_size RGBA canvas.
    Fetches at 3Г— display resolution then downscales with LANCZOS for crispness.
    """
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code != 200:
            return None
        raw = Image.open(BytesIO(resp.content)).convert("RGBA")
        w, h = raw.size
        # Scale to fill a 3Г— virtual canvas, then fit-scale back to display_size
        fetch_px = display_size * 3
        scale    = min(fetch_px / max(w, 1), fetch_px / max(h, 1))
        nw       = max(int(w * scale), 1)
        nh       = max(int(h * scale), 1)
        big      = raw.resize((nw, nh), Image.LANCZOS)
        # Fit into display_size Г— display_size
        scale2 = min(display_size / nw, display_size / nh)
        fw     = max(int(nw * scale2), 1)
        fh     = max(int(nh * scale2), 1)
        final  = big.resize((fw, fh), Image.LANCZOS)
        # Centre on transparent square canvas
        canvas = Image.new("RGBA", (display_size, display_size), (0, 0, 0, 0))
        canvas.paste(final, ((display_size - fw) // 2, (display_size - fh) // 2), final)
        return canvas
    except Exception:
        return None


def _get_ai_background(W, H):
    """
    Call Nano Banana 2 (Gemini 3.1 Flash Image) to generate a premium dark
    atmospheric football stadium background. Falls back to a programmatic
    dark gradient if the API key is missing or the call fails.
    """
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if api_key:
        try:
            prompt = (
                "Cinematic dark football stadium at night, dramatic moody atmosphere, "
                "deep navy blue and charcoal black tones, distant stadium floodlights "
                "creating soft golden bokeh glow, subtle hint of green pitch at the "
                "very bottom edge, luxury premium sports brand aesthetic, ultra dark "
                "background, no text, no people, no logos, photorealistic 4K cinematic"
            )
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-3.1-flash-image-preview:generateContent?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
                },
                timeout=90
            )
            if resp.status_code == 200:
                data  = resp.json()
                parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
                for part in parts:
                    if 'inlineData' in part:
                        img_bytes = base64.b64decode(part['inlineData']['data'])
                        bg = Image.open(BytesIO(img_bytes)).convert('RGB')
                        return bg.resize((W, H), Image.LANCZOS)
            print(f"AI background: HTTP {resp.status_code}")
        except Exception as e:
            print(f"AI background failed: {e}")

    # Fallback: rich dark charcoal-navy gradient
    bg = Image.new("RGB", (W, H))
    d  = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        r = int(8  + 4  * t)
        g = int(10 + 6  * t)
        b = int(24 + 14 * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    return bg


def _get_ai_background_white(W, H):
    """
    Generate a clean white/light background via Gemini.
    Falls back to a crisp white gradient.
    """
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if api_key:
        try:
            prompt = (
                "Ultra clean minimal white sports infographic background, "
                "very subtle pale grey geometric hexagon grid pattern, "
                "faint football pitch line markings at the very bottom edge, "
                "premium professional design, pure white and very light grey tones, "
                "clean modern sports analytics aesthetic, no text, no logos, no people, 4K"
            )
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-3.1-flash-image-preview:generateContent?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
                },
                timeout=90
            )
            if resp.status_code == 200:
                data = resp.json()
                parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
                for part in parts:
                    if 'inlineData' in part:
                        img_bytes = base64.b64decode(part['inlineData']['data'])
                        bg = Image.open(BytesIO(img_bytes)).convert('RGB')
                        return bg.resize((W, H), Image.LANCZOS)
        except Exception as e:
            print(f"AI white background failed: {e}")
    # Fallback: clean white
    bg = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        r = int(252 - 6 * t); g = int(252 - 6 * t); b = int(255 - 4 * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    return bg


def _make_team_initial(team_name, size, section_color, dark):
    """Circular team-initial fallback logo when no logo URL is available."""
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    if dark:
        bg_col  = tuple(max(0, int(c * 0.18)) for c in section_color)
        rim_col = tuple(max(0, int(c * 0.55)) for c in section_color)
        txt_col = (220, 220, 230)
    else:
        bg_col  = tuple(min(255, int(c * 0.15) + 230) for c in section_color)
        rim_col = tuple(max(0, int(c * 0.60)) for c in section_color)
        txt_col = (40, 40, 60)
    d.ellipse([2, 2, size - 3, size - 3], fill=bg_col, outline=rim_col, width=2)
    initials = (team_name or '?').strip()[:2].upper()
    fs = max(10, size // 4)
    try:
        fnt = F('BB', fs)
        bb  = d.textbbox((0, 0), initials, font=fnt)
        d.text(((size - (bb[2] - bb[0])) // 2, (size - (bb[3] - bb[1])) // 2),
               initials, font=fnt, fill=txt_col)
    except Exception:
        pass
    return canvas


def _render_results_card(sections, date_str, total_won, total_picks, win_pct, dark=True, bg_raw=None):
    """
    Render one results card.
    sections = list of (label, sublabel, picks_list, section_rgb_tuple)
    dark     = True for dark stadium bg, False for white bg
    bg_raw   = pre-generated PIL background image (pass to avoid duplicate Gemini calls)
    Returns a PIL Image.
    """
    W      = 1080
    MARGIN = 32

    # Fixed heights
    TOPBAR_H    = 8
    BOTBAR_H    = 8
    LOGO_PAD_T  = 24
    LOGO_H_img  = 80
    SEP_H       = 14
    HEADLINE_H  = 68
    DATE_H      = 38
    BADGE_H     = 54
    BADGE_PAD_B = 22
    HEADER_H    = LOGO_PAD_T + LOGO_H_img + SEP_H + HEADLINE_H + DATE_H + BADGE_H + BADGE_PAD_B

    SEC_H       = 56    # section-header band height
    ROW_GAP     = 10
    ROW_MIN     = 100
    ROW_MAX     = 124
    PAD_BOT     = 20
    SUMBAR_GAP  = 18
    SUMBAR_H    = 88
    PAT_GAP     = 10
    PAT_H       = 132
    MAX_H       = 1920
    MIN_H       = 1080

    # Total picks on this card
    all_picks = []
    for _, _, pl, _ in sections:
        all_picks.extend(pl)
    n = len(all_picks)
    n_sections = len(sections)

    fixed_px = (TOPBAR_H + HEADER_H + n_sections * SEC_H +
                PAD_BOT + SUMBAR_GAP + SUMBAR_H + PAT_GAP + PAT_H + BOTBAR_H)
    avail    = MAX_H - fixed_px
    ROW_H    = max(ROW_MIN, min(ROW_MAX, (avail - max(0, n - 1) * ROW_GAP) // n)) if n > 0 else ROW_MAX
    total_rows_px = n * ROW_H + max(0, n - 1) * ROW_GAP
    H = max(MIN_H, min(MAX_H, fixed_px + total_rows_px))

    # Row proportions
    top_h = int(ROW_H * 0.62)
    bot_h = ROW_H - top_h - 1
    LS    = max(50, min(72, top_h - 8))   # logo size

    # в”Ђв”Ђ Background в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    if dark:
        if bg_raw is not None:
            bg = bg_raw.resize((W, H), Image.LANCZOS)
        else:
            # Fast gradient fallback — no Gemini call
            bg = Image.new("RGB", (W, H))
            _d = ImageDraw.Draw(bg)
            for _y in range(H):
                _t = _y / H
                _d.line([(0, _y), (W, _y)],
                        fill=(int(8 + 4 * _t), int(10 + 6 * _t), int(24 + 14 * _t)))
        ov  = Image.new("RGBA", (W, H), (4, 6, 14, 200))
        img = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
        # Vignette
        vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd  = ImageDraw.Draw(vig)
        for i in range(80):
            a = int(140 * (i / 80) ** 2)
            vd.rectangle([i, i, W - i, H - i], outline=(0, 0, 0, a), width=1)
        img = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")
    else:
        if bg_raw is not None:
            bg = bg_raw.resize((W, H), Image.LANCZOS)
        else:
            # Fast white gradient fallback — no Gemini call
            bg = Image.new("RGB", (W, H))
            _d = ImageDraw.Draw(bg)
            for _y in range(H):
                _t = _y / H
                _d.line([(0, _y), (W, _y)],
                        fill=(int(252 - 6 * _t), int(252 - 6 * _t), int(255 - 4 * _t)))
        ov  = Image.new("RGBA", (W, H), (255, 255, 255, 30))
        img = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")

    draw = ImageDraw.Draw(img)

    # Colour palette
    if dark:
        TEXT_PRI  = (240, 244, 248)   # primary text
        TEXT_SEC  = (160, 170, 185)   # secondary text
        CARD_BG   = (12, 18, 30)      # row card bg base
        CARD_RIM  = (30, 42, 62)      # row card border
        SCORE_PIL = (255, 255, 255, 120)  # score pill
        SCORE_TXT = (255, 255, 255)
    else:
        TEXT_PRI  = (15, 20, 35)
        TEXT_SEC  = (90, 100, 120)
        CARD_BG   = (255, 255, 255)
        CARD_RIM  = (220, 224, 235)
        SCORE_PIL = (15, 20, 35)
        SCORE_TXT = (255, 255, 255)

    WIN_COL  = (22, 163, 74)
    LOSS_COL = (220, 38, 38)

    # в”Ђв”Ђ Gold top bar в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    draw.rectangle([0, 0, W, TOPBAR_H], fill=GOLD)

    # в”Ђв”Ђ Brand logo в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    yc        = TOPBAR_H + LOGO_PAD_T
    logo_path = os.path.join(FONT_DIR, 'logo_white.png')
    if os.path.exists(logo_path):
        blogo = Image.open(logo_path).convert("RGBA")
        lh    = LOGO_H_img
        lw    = int(lh * blogo.width / blogo.height)
        blogo = blogo.resize((lw, lh), Image.LANCZOS)
        if not dark:
            # Invert to dark logo for white background
            r, g, b_ch, a = blogo.split()
            inv = Image.merge("RGBA", (
                ImageChops.invert(r), ImageChops.invert(g), ImageChops.invert(b_ch), a))
            blogo = inv
        img.paste(blogo, ((W - lw) // 2, yc), blogo)
        draw = ImageDraw.Draw(img)
    yc += LOGO_H_img

    # Separator
    sep_col = GOLD_DIM if dark else (200, 200, 215)
    draw.rectangle([60, yc + 4, W - 60, yc + 6], fill=sep_col)
    yc += SEP_H

    # в”Ђв”Ђ Headline в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    f_hl = F('BB', 56)
    hl   = "DAILY RESULTS"
    hlbb = draw.textbbox((0, 0), hl, font=f_hl)
    hx   = (W - (hlbb[2] - hlbb[0])) // 2
    if dark:
        draw.text((hx + 2, yc + 2), hl, font=f_hl, fill=(0, 0, 0))
    draw.text((hx, yc), hl, font=f_hl, fill=GOLD)
    yc += HEADLINE_H

    # в”Ђв”Ђ Date в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    if date_str:
        f_dt = F('OB', 22)
        ds   = date_str.upper()
        dtbb = draw.textbbox((0, 0), ds, font=f_dt)
        draw.text(((W - (dtbb[2] - dtbb[0])) // 2, yc), ds, font=f_dt, fill=TEXT_SEC)
    yc += DATE_H

    # в”Ђв”Ђ Win-rate badge в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    badge_text = f"{total_won} / {total_picks}  GREEN TODAY  -  {win_pct}%"
    f_badge    = F('BB', 26)
    btbb       = draw.textbbox((0, 0), badge_text, font=f_badge)
    btw        = btbb[2] - btbb[0]
    bth        = btbb[3] - btbb[1]
    badge_w    = btw + 64
    badge_x    = (W - badge_w) // 2
    if dark:
        draw.rounded_rectangle([badge_x, yc, badge_x + badge_w, yc + BADGE_H],
                               radius=14, fill=(10, 34, 18), outline=GOLD, width=2)
        badge_txt_col = GOLD
    else:
        draw.rounded_rectangle([badge_x, yc, badge_x + badge_w, yc + BADGE_H],
                               radius=14, fill=WIN_COL, outline=(12, 120, 55), width=2)
        badge_txt_col = (255, 255, 255)
    draw.text((badge_x + (badge_w - btw) // 2, yc + (BADGE_H - bth) // 2),
              badge_text, font=f_badge, fill=badge_txt_col)
    yc += BADGE_H + BADGE_PAD_B

    # в”Ђв”Ђ Sections в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    cw = W - 2 * MARGIN

    for sec_label, sec_sub, sec_picks, sec_col in sections:
        # Section header band
        sec_r, sec_g, sec_b = sec_col

        if dark:
            # Pre-blended solid tint (dark bg + 15% section colour)
            blend = (max(0, min(255, int(8  + sec_r * 0.15))),
                     max(0, min(255, int(12 + sec_g * 0.15))),
                     max(0, min(255, int(20 + sec_b * 0.15))))
            draw.rectangle([0, yc, W, yc + SEC_H], fill=blend)
            draw.rectangle([0, yc, W, yc + 3], fill=sec_col)               # top rim
            draw.rectangle([0, yc + SEC_H - 3, W, yc + SEC_H], fill=sec_col)  # bottom rim
            lbl_col  = (255, 255, 255)
            sub_col  = (sec_r + (255 - sec_r) // 2, sec_g + (255 - sec_g) // 2, sec_b + (255 - sec_b) // 2)
            cnt_col  = (220, 220, 230)
        else:
            draw.rectangle([0, yc, W, yc + SEC_H], fill=sec_col)
            lbl_col  = (255, 255, 255)
            sub_col  = (220, 230, 220)
            cnt_col  = (255, 255, 255)

        f_sec_lbl = F('BB', 22)
        f_sec_sub = F('OR', 16)
        f_sec_cnt = F('OB', 18)

        # Label on left
        draw.text((MARGIN + 6, yc + (SEC_H - 26) // 2), sec_label, font=f_sec_lbl, fill=lbl_col)
        sub_bb = draw.textbbox((0, 0), sec_sub, font=f_sec_sub)
        draw.text((MARGIN + 6, yc + SEC_H - 18), sec_sub, font=f_sec_sub, fill=sub_col)

        # Count on right
        cnt_txt = f"{len(sec_picks)} PICKS"
        cnt_bb  = draw.textbbox((0, 0), cnt_txt, font=f_sec_cnt)
        draw.text((W - MARGIN - (cnt_bb[2] - cnt_bb[0]) - 6,
                   yc + (SEC_H - (cnt_bb[3] - cnt_bb[1])) // 2),
                  cnt_txt, font=f_sec_cnt, fill=cnt_col)

        yc += SEC_H

        # в”Ђв”Ђ Pick rows в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
        for pick in sec_picks:
            won     = bool(pick.get('won', False))
            win_col = WIN_COL if won else LOSS_COL

            cx = MARGIN
            cy = yc

            if dark:
                row_bg_r = max(0, sec_r // 8)
                row_bg_g = max(0, sec_g // 8)
                row_bg_b = max(0, sec_b // 8)
                r_bg  = (row_bg_r + (8 if won else 12), row_bg_g + (4 if won else 2), row_bg_b + (4 if not won else 2))
                r_rim = tuple(max(0, int(c * 0.4)) for c in win_col)
            else:
                r_bg  = (255, 255, 255)
                r_rim = (210, 215, 225)

            # Shadow
            shadow_col = (5, 8, 14) if dark else (210, 215, 225)
            draw.rounded_rectangle([cx + 3, cy + 3, cx + cw + 3, cy + ROW_H + 3],
                                   radius=10, fill=shadow_col)
            # Card
            draw.rounded_rectangle([cx, cy, cx + cw, cy + ROW_H],
                                   radius=10, fill=r_bg, outline=r_rim, width=1)
            # Left accent bar (section color)
            draw.rounded_rectangle([cx, cy, cx + 7, cy + ROW_H],
                                   radius=10, fill=sec_col)
            # Right win/loss bar
            draw.rounded_rectangle([cx + cw - 7, cy, cx + cw, cy + ROW_H],
                                   radius=10, fill=win_col)

            # в”Ђв”Ђ Logos в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
            logo_margin_l = cx + 7 + 14
            logo_margin_r = cx + cw - 7 - 14 - LS
            logo_y        = cy + (top_h - LS) // 2

            for logo_url, lx, team_name in [
                (str(pick.get('home_logo_url', '')), logo_margin_l, str(pick.get('home_team', ''))),
                (str(pick.get('away_logo_url', '')), logo_margin_r, str(pick.get('away_team', ''))),
            ]:
                logo_img = _fetch_logo_crisp(logo_url, LS) if logo_url.startswith('http') else None
                if logo_img is None:
                    logo_img = _make_team_initial(team_name, LS, sec_col, dark)

                # Glow disc behind logo (white on dark, grey on light)
                pad = 5
                gs  = LS + pad * 2
                glow_col = (255, 255, 255, 40) if dark else (180, 190, 210, 50)
                glow = Image.new("RGBA", (gs, gs), (0, 0, 0, 0))
                ImageDraw.Draw(glow).ellipse([0, 0, gs - 1, gs - 1], fill=glow_col)
                img.paste(glow, (lx - pad, logo_y - pad), glow)
                img.paste(logo_img, (lx, logo_y), logo_img)
                draw = ImageDraw.Draw(img)

            # в”Ђв”Ђ Team names в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
            name_fs = max(13, min(18, int(LS * 0.30)))
            f_nm    = F('OB', name_fs)
            sc_cx   = W // 2
            sc_half = 62

            HN       = str(pick.get('home_team', ''))
            hn_start = logo_margin_l + LS + 10
            hn_max_w = sc_cx - sc_half - hn_start - 4
            while len(HN) > 2 and draw.textlength(HN, font=f_nm) > hn_max_w:
                HN = HN[:-1]
            hn_bb = draw.textbbox((0, 0), HN, font=f_nm)
            draw.text((hn_start, cy + (top_h - (hn_bb[3] - hn_bb[1])) // 2),
                      HN, font=f_nm, fill=TEXT_PRI)

            AN     = str(pick.get('away_team', ''))
            an_end = logo_margin_r - 10
            an_max_w = an_end - (sc_cx + sc_half + 4)
            while len(AN) > 2 and draw.textlength(AN, font=f_nm) > an_max_w:
                AN = AN[:-1]
            an_bb = draw.textbbox((0, 0), AN, font=f_nm)
            draw.text((an_end - (an_bb[2] - an_bb[0]),
                       cy + (top_h - (an_bb[3] - an_bb[1])) // 2),
                      AN, font=f_nm, fill=TEXT_PRI)

            # в”Ђв”Ђ Score в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
            hs       = pick.get('home_score', '')
            as_      = pick.get('away_score', '')
            sc_str   = f"{hs} - {as_}" if hs != '' and as_ != '' else "vs"
            f_sc     = F('BB', max(22, min(32, int(top_h * 0.50))))
            scbb     = draw.textbbox((0, 0), sc_str, font=f_sc)
            sc_w     = scbb[2] - scbb[0]
            sc_x     = (W - sc_w) // 2
            sc_y     = cy + (top_h - (scbb[3] - scbb[1])) // 2
            pill_col = (15, 20, 35) if dark else (40, 44, 60)
            draw.rounded_rectangle([sc_x - 12, sc_y - 5,
                                    sc_x + sc_w + 12, sc_y + (scbb[3] - scbb[1]) + 5],
                                   radius=8, fill=pill_col)
            draw.text((sc_x, sc_y), sc_str, font=f_sc, fill=(255, 255, 255))

            # в”Ђв”Ђ Divider в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
            div_y   = cy + top_h
            div_col = (40, 48, 60) if dark else (210, 215, 225)
            draw.line([(cx + 14, div_y), (cx + cw - 14, div_y)], fill=div_col, width=1)

            # в”Ђв”Ђ Bottom strip в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
            bot_top = div_y + 1
            bot_mid = bot_top + bot_h // 2

            # Market pill
            mkt = str(pick.get('market', '')).upper()
            for k, v in {
                'OVER/UNDER 2.5': 'O/U 2.5', 'OVER/UNDER 3.5': 'O/U 3.5',
                'OVER/UNDER 1.5': 'O/U 1.5', 'OVER/UNDER 4.5': 'O/U 4.5',
                'BOTH TEAMS TO SCORE': 'BTTS', 'BOTH TEAMS SCORE': 'BTTS',
                'TOTAL CARDS': 'CARDS', 'MATCH RESULT': '1X2',
                'DOUBLE CHANCE': 'DBL', 'ASIAN HANDICAP': 'HCP',
            }.items():
                if k in mkt:
                    mkt = v
                    break
            if len(mkt) > 11:
                mkt = mkt[:11]

            f_bot   = F('OB', max(12, min(15, bot_h - 6)))
            f_bot_b = F('BB', max(12, min(15, bot_h - 6)))

            pill_bb = draw.textbbox((0, 0), mkt, font=f_bot)
            pill_w  = (pill_bb[2] - pill_bb[0]) + 16
            pill_h  = min(bot_h - 4, 28)
            pill_x  = cx + 16
            pill_y  = bot_mid - pill_h // 2
            if dark:
                mkt_bg  = tuple(max(0, int(c * 0.20)) for c in sec_col)
                mkt_rim = tuple(max(0, int(c * 0.50)) for c in sec_col)
                mkt_txt = tuple(min(255, int(c * 0.75) + 100) for c in sec_col)
            else:
                mkt_bg  = tuple(min(255, int(c * 0.12) + 235) for c in sec_col)
                mkt_rim = tuple(max(0, int(c * 0.55)) for c in sec_col)
                mkt_txt = tuple(max(0, int(c * 0.65)) for c in sec_col)
            draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
                                   radius=6, fill=mkt_bg, outline=mkt_rim, width=1)
            draw.text((pill_x + 8, pill_y + (pill_h - (pill_bb[3] - pill_bb[1])) // 2),
                      mkt, font=f_bot, fill=mkt_txt)

            # Pick text + odds
            pick_txt = str(pick.get('pick', ''))
            try:    odds_txt = f"@ {float(pick.get('odds', 0)):.2f}"
            except: odds_txt = f"@ {pick.get('odds', '')}"

            px  = pill_x + pill_w + 10
            pb  = draw.textbbox((0, 0), pick_txt, font=f_bot)
            draw.text((px, bot_mid - (pb[3] - pb[1]) // 2),
                      pick_txt, font=f_bot, fill=TEXT_PRI)

            gold_col = GOLD if dark else (160, 110, 0)
            ob  = draw.textbbox((0, 0), odds_txt, font=f_bot_b)
            ox  = px + (pb[2] - pb[0]) + 8
            draw.text((ox, bot_mid - (ob[3] - ob[1]) // 2),
                      odds_txt, font=f_bot_b, fill=gold_col)

            # WIN / LOSS badge
            badge_txt = "WIN" if won else "LOSS"
            wlbb      = draw.textbbox((0, 0), badge_txt, font=f_bot_b)
            wl_w      = (wlbb[2] - wlbb[0]) + 22
            wl_h      = min(bot_h - 4, 28)
            wl_x      = cx + cw - 14 - wl_w
            wl_y      = bot_mid - wl_h // 2
            draw.rounded_rectangle([wl_x, wl_y, wl_x + wl_w, wl_y + wl_h],
                                   radius=6, fill=win_col)
            draw.text((wl_x + 11, wl_y + (wl_h - (wlbb[3] - wlbb[1])) // 2),
                      badge_txt, font=f_bot_b, fill=(255, 255, 255))

            yc += ROW_H + ROW_GAP

        # Small gap after last pick of section (replace ROW_GAP with SEC_GAP)
        yc -= ROW_GAP   # remove last row gap

    yc += PAD_BOT

    # в”Ђв”Ђ Summary bar в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    yc += SUMBAR_GAP
    sum_y = yc
    if dark:
        for gy in range(SUMBAR_H):
            t = gy / SUMBAR_H
            draw.line([(MARGIN, sum_y + gy), (W - MARGIN, sum_y + gy)],
                      fill=(int(14 + 18 * t), int(46 + 38 * t), int(24 + 20 * t)))
        draw.rounded_rectangle([MARGIN, sum_y, W - MARGIN, sum_y + SUMBAR_H],
                               radius=16, outline=GOLD, width=3)
        sum_txt_col = GOLD
    else:
        draw.rounded_rectangle([MARGIN, sum_y, W - MARGIN, sum_y + SUMBAR_H],
                               radius=16, fill=WIN_COL, outline=(12, 120, 55), width=2)
        sum_txt_col = (255, 255, 255)

    sum_text = f"{total_won} / {total_picks}  GREEN TODAY  -  {win_pct}%"
    f_sum    = F('BB', max(30, min(42, SUMBAR_H - 28)))
    sbb      = draw.textbbox((0, 0), sum_text, font=f_sum)
    draw.text(((W - (sbb[2] - sbb[0])) // 2, sum_y + (SUMBAR_H - (sbb[3] - sbb[1])) // 2),
              sum_text, font=f_sum, fill=sum_txt_col)

    yc = sum_y + SUMBAR_H + PAT_GAP

    # в”Ђв”Ђ Patreon footer в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    pat_y = yc
    if dark:
        for py in range(pat_y, H - BOTBAR_H):
            t = (py - pat_y) / max(H - BOTBAR_H - pat_y, 1)
            draw.line([(0, py), (W, py)],
                      fill=(int(6 + 4 * t), int(14 + 8 * t), int(10 + 4 * t)))
        draw.rectangle([0, pat_y, W, pat_y + 3], fill=GOLD)
        pat_line1_col = (240, 244, 248)
        pat_line2_col = GOLD
        pat_line3_col = (140, 150, 165)
    else:
        draw.rectangle([0, pat_y, W, H - BOTBAR_H], fill=(248, 249, 252))
        draw.rectangle([0, pat_y, W, pat_y + 3], fill=(200, 200, 215))
        pat_line1_col = (20, 25, 40)
        pat_line2_col = (140, 100, 0)
        pat_line3_col = (100, 110, 130)

    pat_logo_path = os.path.join(FONT_DIR, 'patreon_logo.png')
    pat_logo_h    = 60
    pat_pad_x     = 30
    pat_mid_y     = pat_y + PAT_H // 2

    line1 = "Full Slips + Bankroll & Risk Mgmt + Masterclass"
    line2 = "Join 500+ smart bettors  -  only ВЈ10/month"
    line3 = "patreon.com/Matchdaymentors"

    if os.path.exists(pat_logo_path):
        pl         = Image.open(pat_logo_path).convert("RGBA")
        asp        = pl.width / pl.height
        pat_logo_w = int(pat_logo_h * asp)
        pl         = pl.resize((pat_logo_w, pat_logo_h), Image.LANCZOS)
        img.paste(pl, (pat_pad_x, pat_mid_y - pat_logo_h // 2), pl)
        draw       = ImageDraw.Draw(img)
        div_x      = pat_pad_x + pat_logo_w + 22
        draw.rectangle([div_x, pat_y + 16, div_x + 2, H - BOTBAR_H - 14], fill=GOLD_DIM)
        tx = div_x + 22
        draw.text((tx, pat_mid_y - 36), line1, font=F('BB', 20), fill=pat_line1_col)
        draw.text((tx, pat_mid_y - 10), line2, font=F('OB', 18), fill=pat_line2_col)
        draw.text((tx, pat_mid_y + 16), line3, font=F('OR', 16), fill=pat_line3_col)
    else:
        for txt, fnt, col, dy in [
            (line1, F('BB', 22), pat_line1_col, -36),
            (line2, F('OB', 19), pat_line2_col, -8),
            (line3, F('OR', 17), pat_line3_col, 20),
        ]:
            bb = draw.textbbox((0, 0), txt, font=fnt)
            draw.text(((W - (bb[2] - bb[0])) // 2, pat_mid_y + dy), txt, font=fnt, fill=col)

    draw.rectangle([0, H - BOTBAR_H, W, H], fill=GOLD)

    return img


def generate_daily_results(picks, date_str="", ai_background=False):
    """
    Generate premium daily results cards for Matchday Mentors.

    ai_background=False (default): uses fast gradient fallback (fits in 30s proxy limit)
    ai_background=True           : calls Gemini for AI backgrounds (slower, ~3 min)

    Returns a list of PIL Images:
      - Card 1 dark  (safe + value picks)
      - Card 2 dark  (system 2.0+ picks, if any)
      - Card 1 white (same picks, white background)
      - Card 2 white (system 2.0+ picks, white bg, if any)
    """
    def _odds(p):
        try:    return float(p.get('odds', 0) or 0)
        except: return 0.0

    safe   = sorted([p for p in picks if _odds(p) < 1.5],            key=_odds)
    value  = sorted([p for p in picks if 1.5 <= _odds(p) < 2.0],     key=_odds)
    system = sorted([p for p in picks if _odds(p) >= 2.0],           key=_odds)

    total_picks = len(picks)
    total_won   = sum(1 for p in picks if p.get('won', False))
    win_pct     = int(total_won / total_picks * 100) if total_picks else 0

    # Section colour palette
    SAFE_COL   = (22, 163, 74)    # green
    VALUE_COL  = (202, 138, 4)    # amber
    SYSTEM_COL = (220, 38, 38)    # red

    # Build card 1 sections (safe + value)
    card1_sections = []
    if safe:  card1_sections.append(('SAFE PICKS',  '< 1.50 ODDS',   safe,   SAFE_COL))
    if value: card1_sections.append(('VALUE PICKS', '1.50 вЂ“ 2.00',   value,  VALUE_COL))

    # Build card 2 sections (system bets)
    card2_sections = []
    if system: card2_sections.append(('SYSTEM BETS', '2.00+ ODDS', system, SYSTEM_COL))

    # If everything is in one tier, just put it all in card 1
    if not card1_sections and card2_sections:
        card1_sections = card2_sections
        card2_sections = []

    results = []

    # Pre-generate backgrounds ONCE (reused across cards)
    if ai_background:
        print("Generating AI dark background (Nano Banana 2)...")
        dark_bg = _get_ai_background(1080, 1920)
        print("Generating AI white background (Nano Banana 2)...")
        white_bg = _get_ai_background_white(1080, 1920)
    else:
        print("Using gradient backgrounds (fast mode)...")
        dark_bg = None   # _render_results_card will use gradient fallback
        white_bg = None

    # Dark versions
    if card1_sections:
        print("Rendering dark card 1 (safe + value)...")
        results.append(_render_results_card(card1_sections, date_str, total_won, total_picks, win_pct, dark=True, bg_raw=dark_bg))
    if card2_sections:
        print("Rendering dark card 2 (system bets)...")
        results.append(_render_results_card(card2_sections, date_str, total_won, total_picks, win_pct, dark=True, bg_raw=dark_bg))

    # White versions
    if card1_sections:
        print("Rendering white card 1 (safe + value)...")
        results.append(_render_results_card(card1_sections, date_str, total_won, total_picks, win_pct, dark=False, bg_raw=white_bg))
    if card2_sections:
        print("Rendering white card 2 (system bets)...")
        results.append(_render_results_card(card2_sections, date_str, total_won, total_picks, win_pct, dark=False, bg_raw=white_bg))

    return results


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
