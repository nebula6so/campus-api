from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io, os

app = Flask(__name__)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
STATIC    = os.path.join(BASE_DIR, "static")

FONT_FALLBACKS = [
    os.path.join(BASE_DIR, "font.ttf"),
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
]

def find_font():
    for p in FONT_FALLBACKS:
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            return p
    return None

FONT = find_font()

_fcache = {}
def get_font(size):
    if size not in _fcache:
        try: _fcache[size] = ImageFont.truetype(FONT, size)
        except: _fcache[size] = ImageFont.load_default()
    return _fcache[size]

# 시작시 이미지 로드 (캐싱)
MAP_IMG = Image.open(os.path.join(STATIC, "bg_map.png")).convert("RGBA")
MW, MH  = MAP_IMG.size

PIN_IMGS = {}
for name in ["세라", "세라핀", "드레아", "아리엘"]:
    path = os.path.join(STATIC, f"pin_{name}.png")
    if os.path.exists(path):
        PIN_IMGS[name] = Image.open(path).convert("RGBA")

ZONE_ALIAS = {
    "lecture":"강의실","cafe":"카페테리아",
    "dorm":"기숙사","park":"공원",
    "training":"훈련장","room":"나의 방",
}

ZONE_CONFIG = {
    "강의실":    {"x": 0.30, "y": 0.25},
    "카페테리아": {"x": 0.55, "y": 0.25},
    "기숙사":    {"x": 0.78, "y": 0.30},
    "공원":      {"x": 0.24, "y": 0.60},
    "훈련장":    {"x": 0.55, "y": 0.65},
    "나의 방":   {"x": 0.80, "y": 0.70},
}

HEROINE_COLORS = {
    "세라":   (255, 180, 120),
    "세라핀": (140, 160, 220),
    "드레아": (200, 120, 180),
    "아리엘": (120, 210, 170),
}
HEROINE_ROLES = {
    "세라":"성직자","세라핀":"기사",
    "드레아":"드래곤","아리엘":"엘프",
}

BORDER = (120, 90, 180, 255)
T_MAIN = (240, 230, 255, 255)
T_MUTE = (180, 165, 220, 255)
T_DIM  = (120, 105, 170, 255)
PIN_SIZE = 50

def drr(draw, xy, r, fill, outline=None, width=1):
    x1,y1,x2,y2=xy
    draw.rounded_rectangle([x1,y1,x2,y2],radius=r,fill=fill,outline=outline,width=width)

def draw_bar(draw,x,y,w,h,value,maxval,color):
    drr(draw,[x,y,x+w,y+h],3,(40,35,65,255))
    fw=int(w*(value/maxval))
    if fw>0: drr(draw,[x,y,x+fw,y+h],3,color)

def draw_pin(canvas, px, py, name, color):
    if name in PIN_IMGS:
        pin = PIN_IMGS[name].resize((PIN_SIZE, PIN_SIZE), Image.LANCZOS)
        canvas.paste(pin, (px - PIN_SIZE//2, py - PIN_SIZE), pin)
    else:
        draw = ImageDraw.Draw(canvas)
        r = 20
        draw.ellipse([px-r,py-r*2,px+r,py],fill=color,outline=(255,255,255,255),width=2)
        draw.text((px,py-r),name[0],font=get_font(16),fill=(255,255,255,255),anchor="mm")
        draw.polygon([(px-5,py-2),(px+5,py-2),(px,py+8)],fill=color)

@app.route("/api/campus_status")
def campus_status():
    loc   = request.args.get("loc", "아카데미")
    t     = request.args.get("t", "○월 ○일 ○○:00")
    p_raw = request.args.get("p", "세라.20.60.강의실,세라핀.20.60.훈련장,드레아.20.60.공원,아리엘.20.60.카페테리아")

    heroines = []
    for h in p_raw.split(","):
        parts = h.split(".")
        if len(parts) >= 4:
            zone = ZONE_ALIAS.get(parts[3], parts[3])
            try:
                heroines.append({
                    "name":  parts[0],
                    "like":  int(parts[1]),
                    "guard": int(parts[2]),
                    "zone":  zone,
                })
            except:
                pass

    HEADER_H = 50
    STAT_H   = 110
    TOTAL_H  = HEADER_H + MH + STAT_H

    canvas = Image.new("RGBA", (MW, TOTAL_H), (15, 12, 30, 255))
    draw   = ImageDraw.Draw(canvas)

    # 헤더
    drr(draw,[0,0,MW,HEADER_H],0,(15,12,30,230),BORDER,1)
    draw.text((20,HEADER_H//2),t,font=get_font(18),fill=T_MUTE,anchor="lm")
    draw.text((MW-20,HEADER_H//2),f"@ {loc}",font=get_font(18),fill=T_MAIN,anchor="rm")

    # 맵
    canvas.paste(MAP_IMG,(0,HEADER_H),MAP_IMG)

    # 라벨
    for zname, cfg in ZONE_CONFIG.items():
        zx = int(MW * cfg["x"])
        zy = HEADER_H + int(MH * cfg["y"])
        tw = len(zname)*11 + 14
        drr(draw,[zx-tw//2,zy-13,zx+tw//2,zy+13],8,(20,15,40,200),BORDER,1)
        draw.text((zx,zy),zname,font=get_font(15),fill=T_MAIN,anchor="mm")

    # 핀
    zone_count = {}
    for h in heroines: zone_count[h["zone"]] = zone_count.get(h["zone"],0)+1
    zone_drawn = {}
    for h in heroines:
        zone  = h["zone"]
        color = (*HEROINE_COLORS.get(h["name"],(150,150,200)),255)
        if zone in ZONE_CONFIG:
            cfg   = ZONE_CONFIG[zone]
            zx    = int(MW * cfg["x"])
            zy    = HEADER_H + int(MH * cfg["y"])
            total = zone_count[zone]
            idx   = zone_drawn.get(zone, 0)
            offset = 0 if total==1 else (-25+idx*50 if total==2 else -30+idx*30)
            draw_pin(canvas, zx+offset, zy-20, h["name"], color)
            zone_drawn[zone] = idx+1

    draw = ImageDraw.Draw(canvas)

    # 상태창
    STAT_Y = HEADER_H + MH
    col_w  = MW // 4
    all_heroines = [
        {"name":"세라",   "like":20,"guard":60},
        {"name":"세라핀", "like":20,"guard":60},
        {"name":"드레아", "like":20,"guard":60},
        {"name":"아리엘", "like":20,"guard":60},
    ]
    for h in heroines:
        for ah in all_heroines:
            if ah["name"] == h["name"]:
                ah["like"]  = h["like"]
                ah["guard"] = h["guard"]

    for i, h in enumerate(all_heroines):
        sx    = i * col_w
        color = (*HEROINE_COLORS.get(h["name"],(150,150,200)),255)
        role  = HEROINE_ROLES.get(h["name"],"")
        drr(draw,[sx+4,STAT_Y+4,sx+col_w-4,STAT_Y+STAT_H-4],10,(22,18,46,220),(*color[:3],180),1)
        draw.text((sx+col_w//2,STAT_Y+18),h["name"],font=get_font(16),fill=color,anchor="mm")
        draw.text((sx+col_w//2,STAT_Y+34),f"[{role}]",font=get_font(11),fill=T_DIM,anchor="mm")
        draw.text((sx+10,STAT_Y+50),"호감도",font=get_font(12),fill=T_DIM)
        draw_bar(draw,sx+10,STAT_Y+64,col_w-20,7,h["like"],200,color)
        draw.text((sx+col_w-10,STAT_Y+64),f"{h['like']}/200",font=get_font(10),fill=T_MUTE,anchor="ra")
        draw.text((sx+10,STAT_Y+78),"경계도",font=get_font(12),fill=T_DIM)
        draw_bar(draw,sx+10,STAT_Y+92,col_w-20,7,h["guard"],100,(100,100,140,255))
        draw.text((sx+col_w-10,STAT_Y+92),f"{h['guard']}%",font=get_font(10),fill=T_MUTE,anchor="ra")

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
