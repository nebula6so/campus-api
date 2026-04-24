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
    "강의실":    {"bg": (30, 26, 74),  "border": (74, 63, 160), "icon": "🏫", "x": 0.08, "y": 0.35},
    "카페테리아": {"bg": (26, 46, 26),  "border": (46, 110, 46), "icon": "☕", "x": 0.38, "y": 0.30},
    "편의점":    {"bg": (46, 26, 26),  "border": (126, 48, 48), "icon": "🏪", "x": 0.68, "y": 0.35},
    "기숙사":    {"bg": (26, 26, 46),  "border": (58, 58, 126), "icon": "🏠", "x": 0.20, "y": 0.68},
    "공원":      {"bg": (26, 46, 30),  "border": (46, 110, 62), "icon": "🌿", "x": 0.60, "y": 0.68},
}

HEROINE_COLOR = {
    "강하율": (232, 86, 74),
    "이서연": (106, 90, 205),
    "최유나": (192, 84, 122),
}

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

def draw_bar(draw, x, y, w, h, value, maxval, color):
    draw_rounded_rect(draw, [x, y, x+w, y+h], 3, (34, 32, 64))
    fill_w = int(w * (value / maxval))
    if fill_w > 0:
        draw_rounded_rect(draw, [x, y, x+fill_w, y+h], 3, color)

@app.route("/api/campus_status")
def campus_status():
    # 파라미터 파싱
    loc  = request.args.get("loc", "중앙 광장")
    t    = request.args.get("t", "03월 02일 09:30")
    # p=이름.호감도.경계도.위치, 콤마로 구분
    p_raw = request.args.get("p", "강하율.20.60.카페테리아,이서연.20.60.강의실,최유나.20.60.편의점")

    heroines = []
    for h in p_raw.split(","):
        parts = h.split(".")
        if len(parts) >= 4:
            heroines.append({
                "name":  parts[0],
                "like":  int(parts[1]),
                "guard": int(parts[2]),
                "zone":  parts[3],
            })

    W, H = 640, 400
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    f10 = get_font(10)
    f11 = get_font(11)
    f12 = get_font(12)
    f13 = get_font(13)
    f14 = get_font(14)

    # 상단 바
    draw_rounded_rect(draw, [12, 10, W-12, 42], 8, PANEL, BORDER, 1)
    draw.text((22, 20), t, font=f12, fill=TEXT_MUTE)
    loc_text = f"📍 {loc}"
    draw.text((W-22, 20), loc_text, font=f12, fill=TEXT_MAIN, anchor="ra")

    # 지도 영역
    MAP_X, MAP_Y = 12, 50
    MAP_W, MAP_H = W - 24, 210
    draw_rounded_rect(draw, [MAP_X, MAP_Y, MAP_X+MAP_W, MAP_Y+MAP_H], 10, (17, 16, 42), BORDER, 1)

    # 지도 라벨
    draw.text((MAP_X+10, MAP_Y+8), "캠퍼스 지도", font=f10, fill=TEXT_DIM)

    # 도로선
    road_y1 = MAP_Y + int(MAP_H * 0.52)
    road_y2 = MAP_Y + int(MAP_H * 0.58)
    draw.rectangle([MAP_X, road_y1, MAP_X+MAP_W, road_y2], fill=(26, 24, 56))
    for vx in [0.33, 0.55, 0.77]:
        vx_px = MAP_X + int(MAP_W * vx)
        draw.rectangle([vx_px, MAP_Y, vx_px+4, MAP_Y+MAP_H], fill=(26, 24, 56))

    # 장소 그리기
    ZW, ZH = int(MAP_W * 0.16), int(MAP_H * 0.24)
    zone_positions = {}
    for zname, zs in ZONE_STYLE.items():
        zx = MAP_X + int(MAP_W * zs["x"])
        zy = MAP_Y + int(MAP_H * zs["y"])
        draw_rounded_rect(draw, [zx, zy, zx+ZW, zy+ZH], 6, zs["bg"], zs["border"], 1)
        draw.text((zx + ZW//2, zy + ZH//2 - 6), zs["icon"], font=f14, anchor="mm")
        draw.text((zx + ZW//2, zy + ZH - 10), zname, font=get_font(8), fill=TEXT_MUTE, anchor="mm")
        zone_positions[zname] = (zx + ZW//2, zy)

    # 히로인 핀 그리기
    for h in heroines:
        zone = h["zone"]
        color = HEROINE_COLOR.get(h["name"], (150, 150, 200))
        if zone in zone_positions:
            px, py = zone_positions[zone]
            # 핀 원
            r = 12
            draw.ellipse([px-r, py-r*2-6, px+r, py-6], fill=color, outline=(255,255,255), width=1)
            # 이름
            name_short = h["name"][1:]
            draw.text((px, py-r-6), name_short, font=get_font(8), fill=(255,255,255), anchor="mm")
            # 꼬리
            draw.rectangle([px-1, py-6, px+1, py+2], fill=color)

    # 수치 영역
    STAT_Y = MAP_Y + MAP_H + 8
    STAT_H = 90
    col_w  = (W - 24 - 16) // 3

    for i, h in enumerate(heroines[:3]):
        sx = 12 + i * (col_w + 8)
        draw_rounded_rect(draw, [sx, STAT_Y, sx+col_w, STAT_Y+STAT_H], 8, PANEL, BORDER, 1)
        color = HEROINE_COLOR.get(h["name"], (150,150,200))

        # 이름
        draw.text((sx+10, STAT_Y+8), h["name"], font=f11, fill=color)

        # 호감도 바
        draw.text((sx+10, STAT_Y+28), "❤ 호감도", font=f10, fill=TEXT_DIM)
        draw_bar(draw, sx+10, STAT_Y+40, col_w-20, 5, h["like"], 200, color)
        draw.text((sx+col_w-10, STAT_Y+40), f"{h['like']}/200", font=get_font(8), fill=TEXT_MUTE, anchor="ra")

        # 경계도 바
        draw.text((sx+10, STAT_Y+54), "🛡 경계도", font=f10, fill=TEXT_DIM)
        draw_bar(draw, sx+10, STAT_Y+66, col_w-20, 5, h["guard"], 100, (85,85,85))
        draw.text((sx+col_w-10, STAT_Y+66), f"{h['guard']}%", font=get_font(8), fill=TEXT_MUTE, anchor="ra")

    # 이동 선택 라벨
    MOVE_Y = STAT_Y + STAT_H + 8
    draw.text((14, MOVE_Y), "이동 선택", font=f10, fill=TEXT_DIM)
    MOVE_Y += 14
    zones_list = list(ZONE_STYLE.keys())
    btn_w = (W - 24 - 16) // len(zones_list)
    for i, zname in enumerate(zones_list):
        bx = 12 + i * (btn_w + 4)
        draw_rounded_rect(draw, [bx, MOVE_Y, bx+btn_w, MOVE_Y+22], 6, (26, 22, 64), BORDER, 1)
        icon = ZONE_STYLE[zname]["icon"]
        draw.text((bx + btn_w//2, MOVE_Y+11), f"{icon} {zname}", font=get_font(9), fill=TEXT_MUTE, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
