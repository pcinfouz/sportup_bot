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
