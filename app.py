from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os
import urllib.request

app = Flask(__name__)

FONT_PATH = os.path.join(os.path.dirname(__file__), "font.ttf")

def ensure_font():
    if not os.path.exists(FONT_PATH) or os.path.getsize(FONT_PATH) < 1000:
        url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf"
        try:
            urllib.request.urlretrieve(url, FONT_PATH)
        except:
            pass

ensure_font()

BG        = (13, 13, 26)
PANEL     = (22, 18, 46)
BORDER    = (58, 45, 110)
TEXT_MAIN = (232, 224, 255)
TEXT_MUTE = (168, 159, 216)
TEXT_DIM  = (106, 96, 168)

ZONE_STYLE = {
    "강의실":    {"bg": (30, 26, 74),  "border": (74, 63, 160),  "icon": "강의실", "x": 0.08, "y": 0.35},
    "카페테리아": {"bg": (26, 46, 26),  "border": (46, 110, 46),  "icon": "카페",   "x": 0.38, "y": 0.28},
    "편의점":    {"bg": (46, 26, 26),  "border": (126, 48, 48),  "icon": "편의점", "x": 0.68, "y": 0.35},
    "기숙사":    {"bg": (26, 26, 46),  "border": (58, 58, 126),  "icon": "기숙사", "x": 0.18, "y": 0.65},
    "공원":      {"bg": (26, 46, 30),  "border": (46, 110, 62),  "icon": "공원",   "x": 0.58, "y": 0.65},
}

ZONE_ALIAS = {
    "lecture": "강의실",
    "cafe":    "카페테리아",
    "store":   "편의점",
    "dorm":    "기숙사",
    "park":    "공원",
}

HEROINE_COLOR = {
    "강하율": (232, 86, 74),
    "이서연": (106, 90, 205),
    "최유나": (192, 84, 122),
}

# 2배 스케일로 고화질 렌더링
SCALE = 2

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size * SCALE)
    except:
        return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(
        [x1*SCALE, y1*SCALE, x2*SCALE, y2*SCALE],
        radius=radius*SCALE, fill=fill, outline=outline, width=max(1, width*SCALE)
    )

def draw_bar(draw, x, y, w, h, value, maxval, color):
    draw_rounded_rect(draw, [x, y, x+w, y+h], 3, (34, 32, 64))
    fill_w = int(w * (value / maxval))
    if fill_w > 0:
        draw_rounded_rect(draw, [x, y, x+fill_w, y+h], 3, color)

def draw_pin(draw, px, py, name, color, offset_x=0):
    r = 14
    cx = (px + offset_x) * SCALE
    cy = (py - 35) * SCALE
    draw.ellipse([cx-r*SCALE, cy-r*SCALE, cx+r*SCALE, cy+r*SCALE],
                 fill=color, outline=(255, 255, 255), width=2*SCALE)
    draw.text((cx, cy), name[0], font=get_font(12), fill=(255, 255, 255), anchor="mm")
    draw.polygon([
        (cx - 5*SCALE, cy + r*SCALE - 2*SCALE),
        (cx + 5*SCALE, cy + r*SCALE - 2*SCALE),
        (cx, cy + r*SCALE + 10*SCALE)
    ], fill=color)
    nw = (len(name) * 8 + 10) * SCALE
    ny = cy + r*SCALE + 12*SCALE
    draw.rounded_rectangle([cx-nw//2, ny, cx+nw//2, ny+14*SCALE],
                            radius=3*SCALE, fill=color)
    draw.text((cx, ny + 7*SCALE), name, font=get_font(9), fill=(255, 255, 255), anchor="mm")

@app.route("/api/campus_status")
def campus_status():
    loc   = request.args.get("loc", "중앙 광장")
    t     = request.args.get("t", "03월 02일 09:30")
    p_raw = request.args.get("p", "강하율.20.60.카페테리아,이서연.20.60.강의실,최유나.20.60.편의점")

    heroines = []
    for h in p_raw.split(","):
        parts = h.split(".")
        if len(parts) >= 4:
            zone = ZONE_ALIAS.get(parts[3], parts[3])
            heroines.append({
                "name":  parts[0],
                "like":  int(parts[1]),
                "guard": int(parts[2]),
                "zone":  zone,
            })

    # 논리적 크기 (표시 크기)
    W, H = 640, 430

    # 실제 렌더링 크기 (2배)
    img  = Image.new("RGB", (W*SCALE, H*SCALE), BG)
    draw = ImageDraw.Draw(img)

    f8  = get_font(8)
    f10 = get_font(10)
    f11 = get_font(11)
    f12 = get_font(12)
    f14 = get_font(14)

    # 상단 바
    draw_rounded_rect(draw, [12, 10, W-12, 44], 8, PANEL, BORDER, 1)
    draw.text((22*SCALE, 27*SCALE), t, font=f12, fill=TEXT_MUTE, anchor="lm")
    draw.text(((W-22)*SCALE, 27*SCALE), f"@ {loc}", font=f12, fill=TEXT_MAIN, anchor="rm")

    # 지도 영역
    MAP_X, MAP_Y = 12, 52
    MAP_W, MAP_H = W - 24, 218
    draw_rounded_rect(draw, [MAP_X, MAP_Y, MAP_X+MAP_W, MAP_Y+MAP_H], 10, (17, 16, 42), BORDER, 1)
    draw.text(((MAP_X+10)*SCALE, (MAP_Y+9)*SCALE), "캠퍼스 지도", font=f10, fill=TEXT_DIM)

    # 도로
    road_y = MAP_Y + int(MAP_H * 0.56)
    draw.rectangle([MAP_X*SCALE, road_y*SCALE, (MAP_X+MAP_W)*SCALE, (road_y+6)*SCALE], fill=(26, 24, 56))
    for vx in [0.32, 0.54, 0.76]:
        vx_px = MAP_X + int(MAP_W * vx)
        draw.rectangle([vx_px*SCALE, (MAP_Y+20)*SCALE, (vx_px+4)*SCALE, (MAP_Y+MAP_H)*SCALE], fill=(26, 24, 56))

    # 장소
    ZW, ZH = int(MAP_W * 0.17), int(MAP_H * 0.27)
    zone_positions = {}
    for zname, zs in ZONE_STYLE.items():
        zx = MAP_X + int(MAP_W * zs["x"])
        zy = MAP_Y + int(MAP_H * zs["y"])
        draw_rounded_rect(draw, [zx, zy, zx+ZW, zy+ZH], 6, zs["bg"], zs["border"], 1)
        draw.text(((zx+ZW//2)*SCALE, (zy+ZH//2-4)*SCALE), zs["icon"], font=f11, fill=TEXT_MUTE, anchor="mm")
        draw.text(((zx+ZW//2)*SCALE, (zy+ZH-9)*SCALE), zname, font=f8, fill=TEXT_DIM, anchor="mm")
        zone_positions[zname] = (zx + ZW//2, zy + 6)

    # 히로인 핀
    zone_count = {}
    for h in heroines:
        zone_count[h["zone"]] = zone_count.get(h["zone"], 0) + 1

    zone_drawn = {}
    for h in heroines:
        zone  = h["zone"]
        color = HEROINE_COLOR.get(h["name"], (150, 150, 200))
        if zone in zone_positions:
            px, py = zone_positions[zone]
            total  = zone_count[zone]
            idx    = zone_drawn.get(zone, 0)
            offset = 0 if total == 1 else (-20 + idx*40 if total == 2 else -28 + idx*28)
            draw_pin(draw, px, py, h["name"], color, offset)
            zone_drawn[zone] = idx + 1

    # 수치
    STAT_Y = MAP_Y + MAP_H + 10
    STAT_H = 90
    col_w  = (W - 24 - 16) // 3

    for i, h in enumerate(heroines[:3]):
        sx    = 12 + i * (col_w + 8)
        color = HEROINE_COLOR.get(h["name"], (150, 150, 200))
        draw_rounded_rect(draw, [sx, STAT_Y, sx+col_w, STAT_Y+STAT_H], 8, PANEL, BORDER, 1)
        draw.text(((sx+10)*SCALE, (STAT_Y+12)*SCALE), h["name"], font=f11, fill=color)
        draw.text(((sx+10)*SCALE, (STAT_Y+30)*SCALE), "호감도", font=f8, fill=TEXT_DIM)
        draw_bar(draw, sx+10, STAT_Y+41, col_w-20, 6, h["like"], 200, color)
        draw.text(((sx+col_w-10)*SCALE, (STAT_Y+41)*SCALE), f"{h['like']}/200", font=f8, fill=TEXT_MUTE, anchor="ra")
        draw.text(((sx+10)*SCALE, (STAT_Y+55)*SCALE), "경계도", font=f8, fill=TEXT_DIM)
        draw_bar(draw, sx+10, STAT_Y+66, col_w-20, 6, h["guard"], 100, (85, 85, 85))
        draw.text(((sx+col_w-10)*SCALE, (STAT_Y+66)*SCALE), f"{h['guard']}%", font=f8, fill=TEXT_MUTE, anchor="ra")

    # 이동 선택
    MOVE_Y = STAT_Y + STAT_H + 8
    draw.text((14*SCALE, MOVE_Y*SCALE), "이동 선택", font=f8, fill=TEXT_DIM)
    MOVE_Y += 14
    zones_list = list(ZONE_STYLE.keys())
    btn_w = (W - 24 - 16) // len(zones_list)
    for i, zname in enumerate(zones_list):
        bx = 12 + i * (btn_w + 4)
        draw_rounded_rect(draw, [bx, MOVE_Y, bx+btn_w, MOVE_Y+22], 5, (26, 22, 64), BORDER, 1)
        draw.text(((bx+btn_w//2)*SCALE, (MOVE_Y+11)*SCALE), zname, font=f9 if False else get_font(9), fill=TEXT_MUTE, anchor="mm")

    # 최종 출력 (원래 크기로 다운샘플)
    img = img.resize((W, H), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
