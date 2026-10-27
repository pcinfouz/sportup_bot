# Rasmlar yasovchi skript (kerak bo'lsa qayta ishlatish mumkin): python make_images.py
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1280, 720
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
os.makedirs("images", exist_ok=True)

ITEMS = {
    "welcome":  ("SportUp",              "Eng yangi sport kollektsiyalari",       "Новые спортивные коллекции",      ((10, 20, 40), (20, 110, 90))),
    "menu":     ("Katalog",              "Kerakli bo'limni tanlang",              "Выберите нужный раздел",          ((20, 24, 48), (60, 50, 140))),
    "boots":    ("Butsilar",             "Futbol butsilari",                      "Футбольные бутсы",                ((6, 50, 30), (30, 160, 80))),
    "shin":     ("Sarakanoshkalar",      "Himoya uchun",                          "Щитки",                           ((60, 20, 20), (200, 70, 50))),
    "kits":     ("Formalar",             "Klub va terma jamoa formalari",         "Футбольная форма",                ((15, 30, 70), (40, 100, 200))),
    "protein":  ("Protein formalar",     "Mashg'ulot kiyimlari",                  "Тренировочная форма",             ((50, 20, 70), (150, 60, 190))),
    "balls":    ("Toplar",               "Futbol toplari",                        "Мячи",                            ((60, 40, 5), (230, 150, 20))),
    "shoes":    ("Krasovkalar",          "Sport krasovkalari",                    "Кроссовки",                       ((20, 20, 20), (110, 110, 120))),
    "socks":    ("Polgetralar",          "Futbol getralari",                      "Гетры",                           ((10, 50, 60), (30, 150, 170))),
    "dumbbell": ("Gantellar",            "Sport zal uchun",                       "Для спортзала",                   ((40, 10, 10), (160, 30, 40))),
    "swim":     ("Suzish mahsulotlari",  "Suzish uchun jihozlar",                 "Товары для плавания",             ((5, 40, 90), (20, 150, 220))),
}

def _bez(p0, p1, p2, p3, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return pts


def _path(start, segs):
    pts = [start]
    cur = start
    for c1, c2, end in segs:
        pts += _bez(cur, c1, c2, end)[1:]
        cur = end
    return pts


def draw_boot(img, cx, cy, size):
    """Dumaloq ichiga butsi belgisi (oq rangda) chizadi."""
    S = 4  # sifat uchun katta o'lchamda chizib, kichraytiramiz
    box = size * S
    layer = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # asl belgi koordinatalari ~ (100..600, 175..500)
    k = box / 520.0
    ox, oy = -94, -72

    def T(pts):
        return [((x + ox) * k, (y + oy) * k) for x, y in pts]

    white = (255, 255, 255, 255)
    # yuqori qism (qanot + tana)
    upper = _path((118, 228), [
        ((112, 185), (190, 175), (268, 205)),
        ((330, 228), (375, 272), (403, 307)),
        ((340, 278), (275, 262), (217, 265)),
        ((330, 275), (500, 345), (590, 435)),
        ((608, 456), (585, 472), (535, 471)),
        ((470, 470), (425, 445), (385, 425)),
        ((290, 385), (205, 335), (150, 302)),
        ((122, 282), (116, 255), (118, 228)),
    ])
    d.polygon(T(upper), fill=white)
    # taglik (yarim oy)
    sole = _path((105, 293), [
        ((160, 322), (290, 392), (385, 426)),
        ((410, 440), (425, 452), (425, 465)),
        ((300, 440), (195, 420), (150, 395)),
        ((112, 370), (96, 330), (105, 293)),
    ])
    d.polygon(T(sole), fill=white)
    # shipovkalar
    for (x, y, r) in [(160, 408, 17), (236, 428, 17), (340, 452, 16), (424, 472, 17), (520, 489, 17)]:
        px, py = (x + ox) * k, (y + oy) * k
        d.ellipse((px - r*k, py - r*k*0.9, px + r*k, py + r*k*1.1), fill=white)
    layer = layer.resize((size, size), Image.LANCZOS)
    img.paste(layer, (int(cx - size / 2), int(cy - size / 2)), layer)


def gradient(c1, c2):
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            t = (x / W * 0.6 + y / H * 0.4)
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return img

def fit(draw, text, path, max_w, start):
    size = start
    while size > 20:
        f = ImageFont.truetype(path, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(path, 20)

for key, (title, sub_uz, sub_ru, (c1, c2)) in ITEMS.items():
    img = gradient(c1, c2).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # bezak: diagonal chiziqlar va doiralar
    for i in range(6):
        x = 700 + i * 120
        d.polygon([(x, 0), (x + 60, 0), (x - 180, H), (x - 240, H)], fill=(255, 255, 255, 16))
    d.ellipse((860, 120, 1260, 520), outline=(255, 255, 255, 60), width=6)
    d.ellipse((930, 190, 1190, 450), outline=(255, 255, 255, 40), width=4)
    d.ellipse((-120, 500, 260, 880), fill=(255, 255, 255, 18))
    img = Image.alpha_composite(img, ov).convert("RGB")
    draw_boot(img, 1060, 322, 250)   # dumaloq markazida butsi
    d = ImageDraw.Draw(img)

    d.text((80, 70), "SPORTUP", font=ImageFont.truetype(B, 44), fill=(255, 255, 255))
    d.rectangle((80, 130, 230, 136), fill=(255, 255, 255))
    ft = fit(d, title, B, 760, 130)
    d.text((80, 270), title, font=ft, fill=(255, 255, 255))
    d.text((84, 270 + ft.size + 30), sub_uz, font=ImageFont.truetype(R, 44), fill=(235, 240, 245))
    d.text((84, 270 + ft.size + 92), sub_ru, font=ImageFont.truetype(R, 36), fill=(200, 210, 220))
    d.text((80, H - 80), "t.me/sportup_uz", font=ImageFont.truetype(R, 32), fill=(220, 230, 235))
    img.save(f"images/{'cat_' + key if key not in ('welcome','menu') else key}.jpg", quality=90)
print("tayyor")
