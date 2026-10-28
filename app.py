"""
SportUp Telegram bot
Ishga tushirish:
    pip install aiogram
    python app.py
Rasmlar: app.py yonida  images/  papka oching.
Render (Web Service): bot PORT'da kichik server ochadi, shuning uchun deploy muvaffaqiyatli bo'ladi.
"""
import asyncio
import json
import os
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web


def _load_env(path=".env"):
    """.env fayldan BOT_TOKEN ni o'qiydi (qo'shimcha kutubxona kerak emas)."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


_load_env()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")  # .env yoki Render Environment: BOT_TOKEN=123:ABC...
# Rasm yuklash huquqi: ADMIN_ID=123456789  (bir nechta bo'lsa vergul bilan)
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_ID", "").replace(" ", "").split(",") if x.isdigit()}
ADMIN_USERNAME = "berdaliyew"          # buyurtma uchun yoziladigan akkaunt
MENU_IMAGE = "images/menu.jpg"         # /start dan keyin chiqadigan rasm (ixtiyoriy)
USERS_FILE = "users.json"              # til tanlovi saqlanadi

# Aloqa raqamlari
PHONES = ["+998 95 630 80 00", "+998 77 625 33 09", "+998 95 365 06 07"]
PHONES_TXT = "\n".join(f"📞 {p}" for p in PHONES)

# Lokatsiya: kodga yozish shart emas, Render'da Environment'ga qo'shing:
#   LOCATION_LAT=41.311081   LOCATION_LON=69.240562   ADDRESS=Toshkent, ... (manzil matni)
# Yoki shu yerning o'ziga raqamlarni yozing.
def _float(name):
    try:
        return float(os.getenv(name, "").replace(",", "."))
    except ValueError:
        return None


LOCATION_LAT = _float("LOCATION_LAT")
LOCATION_LON = _float("LOCATION_LON")
ADDRESS = os.getenv("ADDRESS", "").strip()

# Rasmi yo'q mahsulotlarda kategoriya rasmi chiqadi (images/cat_<kategoriya>.jpg).
FALLBACK_PHOTO = None

WELCOME_IMAGE = "images/welcome.jpg"

# /start -> til -> shu sahifalar ("Oldinga" / "Orqaga" tugmalari bilan) -> menyu
INFO = {
    "uz": [
        (
            "Assalomu alaykum! 👋\n\n"
            "🏆 SportUp do'koniga xush kelibsiz!\n\n"
            "Eng yangi sport kollektsiyalari bizda.\n"
            "Sifatli sport kiyimlari va jihozlari — hammasi bir joyda."
        ),
        (
            "💎 Nega aynan biz?\n\n"
            "✅ Premium sifatli mahsulotlar\n"
            "💯 Halollik foydadan ustun\n"
            "🎁 Har bir buyurtmaga bonus\n"
            "🚚 O'zbekiston bo'ylab yetkazib beramiz"
        ),
        (
            "🛒 Qanday buyurtma beriladi?\n\n"
            "1️⃣ Menyudan kerakli bo'limni tanlang\n"
            "2️⃣ Modelni tanlab, rasm va narxni ko'ring\n"
            "3️⃣ «Buyurtma berish» tugmasini bosing\n\n"
            f"📞 Savollar uchun: @{ADMIN_USERNAME}\n{PHONES_TXT}"
        ),
    ],
    "ru": [
        (
            "Здравствуйте! 👋\n\n"
            "🏆 Добро пожаловать в магазин SportUp!\n\n"
            "Самые новые спортивные коллекции у нас.\n"
            "Качественная спортивная одежда и инвентарь — всё в одном месте."
        ),
        (
            "💎 Почему именно мы?\n\n"
            "✅ Товары премиум качества\n"
            "💯 Честность важнее выгоды\n"
            "🎁 Бонус к каждому заказу\n"
            "🚚 Доставка по всему Узбекистану"
        ),
        (
            "🛒 Как сделать заказ?\n\n"
            "1️⃣ Выберите нужный раздел в меню\n"
            "2️⃣ Выберите модель, посмотрите фото и цену\n"
            "3️⃣ Нажмите «Заказать»\n\n"
            f"📞 По вопросам: @{ADMIN_USERNAME}\n{PHONES_TXT}"
        ),
    ],
}

# ----------------------------------------------------------------------------
# MATNLAR
# ----------------------------------------------------------------------------
T = {
    "choose_lang": {"uz": "Tilni tanlang / Выберите язык", "ru": "Tilni tanlang / Выберите язык"},
    "choose_cat": {"uz": "🏟 Kategoriyani tanlang:", "ru": "🏟 Выберите категорию:"},
    "choose_prod": {"uz": "Modelni tanlang:", "ru": "Выберите модель:"},
    "soon": {"uz": "⏳ Tez kunda!", "ru": "⏳ Скоро!"},
    "back": {"uz": "⬅️ Orqaga", "ru": "⬅️ Назад"},
    "prev": {"uz": "◀️ Orqaga", "ru": "◀️ Назад"},
    "next": {"uz": "Oldinga ▶️", "ru": "Вперёд ▶️"},
    "order": {"uz": "🛒 Buyurtma berish", "ru": "🛒 Заказать"},
    "lang": {"uz": "🌐 Til", "ru": "🌐 Язык"},
    "size": {"uz": "Razmer", "ru": "Размер"},
    "quality": {"uz": "Premium sifatda", "ru": "Премиум качество"},
    "price": {"uz": "Narx", "ru": "Цена"},
    "bonus": {"uz": "Bonusi bilan", "ru": "С бонусом"},
    "som": {"uz": "so'm", "ru": "сум"},
    "negotiable": {"uz": "kelishiladi", "ru": "договорная"},
    "contact": {"uz": "📞 Aloqa", "ru": "📞 Контакты"},
    "location": {"uz": "📍 Lokatsiya", "ru": "📍 Локация"},
    "write": {"uz": "✍️ Yozish", "ru": "✍️ Написать"},
    "contact_text": {"uz": "Buyurtma va savollar uchun aloqaga chiqing:",
                     "ru": "Для заказов и вопросов свяжитесь с нами:"},
}

# ----------------------------------------------------------------------------
# KATEGORIYALAR  ("new" — Yangiliklar, mahsulotlardan o'zi yig'iladi)
# ----------------------------------------------------------------------------
CATEGORIES = {
    "new":     {"uz": "🆕 Yangiliklar",           "ru": "🆕 Новинки"},
    "boots":   {"uz": "👟 Butsilar",              "ru": "👟 Бутсы"},
    "shin":    {"uz": "🛡 Sarakanoshkalar",       "ru": "🛡 Щитки"},
    "kits":    {"uz": "👕 Formalar",              "ru": "👕 Форма"},
    "protein": {"uz": "💪 Protein formalar",      "ru": "💪 Протеин / форма"},
    "balls":   {"uz": "⚽ Toplar",                "ru": "⚽ Мячи"},
    "shoes":   {"uz": "👟 Krasovkalar",           "ru": "👟 Кроссовки"},
    "socks":   {"uz": "🧦 Polgetralar",           "ru": "🧦 Гетры"},
    "dumbbell":{"uz": "🏋️ Gantellar",            "ru": "🏋️ Гантели"},
    "swim":    {"uz": "🏊 Suzish uchun mahsulotlar", "ru": "🏊 Товары для плавания"},
}

# ----------------------------------------------------------------------------
# MAHSULOTLAR  (shu yerga qo'shaverasiz)
# Rasm: images/<nomi_slug>.jpg  (to'liq ro'yxat: rasm_nomlari.txt)
# ----------------------------------------------------------------------------
def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# "Yangiliklar" bo'limiga tushadigan mahsulotlar (nomi bo'yicha). Xohlaganingizni qo'shing/olib tashlang.
NEW_NAMES = {
    "Nike Phantom GX 2 Elite", "Adidas F50 Elite Laceless", "Puma Future 8 Ultimate",
    "Adidas Trionda Pro", "Real Madrid Home", "Barcelona Home",
    "O'zbekiston terma jamoasi", "Adidas Samba",
}


def P(name, emoji, desc_uz, desc_ru, price=350000, sizes="39-44"):
    """Mahsulot yasaydi. price=None bo'lsa 'Narx: kelishiladi' deb chiqadi."""
    return {"name": name, "title": name, "emoji": emoji, "sizes": sizes, "price": price,
            "desc": {"uz": desc_uz, "ru": desc_ru}, "photo": f"images/{_slug(name)}.jpg",
            "new": name in NEW_NAMES}


def _mk(items, emoji, sizes, price=None):
    return [P(n, emoji, du, dr, price, sizes) for n, du, dr in items]


CATALOG = {
    "boots": [
        # Rasmi bor mahsulot (to'liq yozuv):
        {"name": "F50 Shoes (Green:Black)", "title": "F50", "emoji": "💚", "sizes": "39-44",
         "price": 350000, "photo": "images/f50_green.jpg"},
        P("Nike Mercurial Superfly 10 / 11 Elite", "🔥", "Tezlik va ajoyib ushlanish.", "Скорость и отличное сцепление.", 350000),
        P("Nike Mercurial Vapor 16 / 17 Elite", "🔥", "Past yoqali klassik tezkor butsa.", "Классическая скоростная модель с низким верхом.", 350000),
        P("Nike Phantom 6 Elite", "🔥", "To'pni nazorat qilish va aniq zarba uchun.", "Для контроля мяча и точного удара.", 350000),
        P("Nike Phantom GX 2 Elite", "🔥", "Aniq zarba va to'pni nazorat qilish uchun.", "Для точного удара и контроля мяча.", 350000),
        P("Nike Tiempo Maestro / Legend 10 Elite", "🔥", "Yumshoq material, qulaylik va himoya.", "Мягкий материал, комфорт и защита.", 350000),
        P("Nike Premier III", "🔥", "Hamyonbop va sifatli klassik charm model.", "Доступная классическая кожаная модель.", 350000),
        P("Adidas Predator Elite / FT", "⚡", "Zarba aniqligi va to'pni ushlash uchun.", "Для точности удара и контроля мяча.", 350000),
        P("Adidas F50 Hyperfast / Elite", "⚡", "Ultra-yengil tezkor butsa.", "Сверхлёгкая скоростная бутса.", 350000),
        P("Adidas F50 Elite Laceless", "⚡", "Bog'ichsiz, ultra-yengil tezkor butsa.", "Бесшнурковая сверхлёгкая скоростная бутса.", 350000),
        P("Adidas Copa Pure 4 / Icon 2", "⚡", "Yumshoq charm va maksimal qulaylik.", "Мягкая кожа и максимальный комфорт.", 350000),
        P("Adidas F50 Messi Elite", "⚡", "Messi uslubidagi maxsus seriya.", "Специальная серия в стиле Месси.", 350000),
        P("Adidas Copa Mundial", "⚡", "Modadan ketmaydigan haqiqiy klassika.", "Настоящая классика, не выходящая из моды.", 350000),
        P("Puma Ultra Nitro 7 / Ultimate", "🐆", "Juda yengil va tezkor butsa.", "Очень лёгкая и скоростная бутса.", 350000),
        P("Puma Future 9 Ultimate", "🐆", "Maydonda erkin harakat va kreativ o'yin uchun.", "Свобода движений и креативная игра.", 350000),
        P("Puma Future 8 Ultimate", "🐆", "Erkin harakat va moslashuvchan tuzilma.", "Свобода движений и адаптивная конструкция.", 350000),
        P("Puma King Ultimate", "🐆", "Zamonaviy sintetik charm, yuqori komfort.", "Современная синтетическая кожа, высокий комфорт.", 350000),
        P("Mizuno Morelia Neo V Beta Japan", "🎌", "Premium yapon charmi, yengil va chidamli.", "Премиальная японская кожа, лёгкая и прочная.", 350000),
        P("Mizuno Morelia II Japan", "🎌", "Klassika va tabiiy to'p sezish hissi.", "Классика и естественное чувство мяча.", 350000),
        P("Mizuno Alpha III Japan", "🎌", "Tezkor o'yinchilar uchun yapon texnologiyasi.", "Японская технология для скоростных игроков.", 350000),
    ],
    "shin": _mk([
        ("Nike Mercurial Lite", "Yengil va qulay himoya.", "Лёгкая и удобная защита."),
        ("Nike Charge", "Ishonchli himoya, qulay mahkamlanadi.", "Надёжная защита, удобная фиксация."),
        ("Nike J Guard-CE", "Mustahkam qobiq va yengil vazn.", "Прочная оболочка и лёгкий вес."),
        ("Nike Protegga Flex", "Egiluvchan material, qulay o'tiradi.", "Гибкий материал, удобная посадка."),
        ("Adidas Tiro League", "Kundalik mashg'ulotlar uchun.", "Для ежедневных тренировок."),
        ("Adidas Predator League", "O'yin uchun yengil himoya.", "Лёгкая защита для игры."),
        ("Adidas X League", "Tezkor o'yinchilar uchun yupqa himoya.", "Тонкая защита для скоростных игроков."),
        ("Adidas Tiro Match", "Mashg'ulot va o'yin uchun universal.", "Универсальные для тренировок и игры."),
        ("Puma Ultra Flex", "Egiluvchan va qulay sarakanoshka.", "Гибкие и удобные щитки."),
        ("Puma Ultra Light", "Juda yengil, maydonda sezilmaydi.", "Очень лёгкие, на поле не чувствуются."),
    ], "🛡", "S / M / L"),
    "kits": _mk([
        ("Real Madrid Home", "Oq klassik klub formasi.", "Классическая белая клубная форма."),
        ("Barcelona Home", "Ko'k-anor rangli klub formasi.", "Клубная форма в сине-гранатовых цветах."),
        ("Manchester City Home", "Havorang klub formasi.", "Клубная форма небесно-голубого цвета."),
        ("Manchester United Home", "Qizil klassik klub formasi.", "Классическая красная клубная форма."),
        ("Liverpool Home", "Qizil rangli klub formasi.", "Красная клубная форма."),
        ("PSG Home", "To'q ko'k klub formasi.", "Тёмно-синяя клубная форма."),
        ("Bayern Munich Home", "Qizil klub formasi.", "Красная клубная форма."),
        ("Juventus Home", "Qora-oq chiziqli klub formasi.", "Клубная форма в чёрно-белую полоску."),
        ("Argentina Home", "Oq-ko'k chiziqli terma jamoa formasi.", "Форма сборной в бело-голубую полоску."),
        ("O'zbekiston terma jamoasi", "Milliy terma jamoa formasi.", "Форма национальной сборной."),
    ], "👕", "S-XXL"),
    "protein": _mk([
        ("Nike Dri-FIT Trening", "Namlikni tez chiqaradigan mashg'ulot to'plami.", "Тренировочный комплект, быстро отводит влагу."),
        ("Nike Tech Fleece", "Issiq va zamonaviy kundalik kostyum.", "Тёплый современный повседневный костюм."),
        ("Nike Academy Kostyum", "Jamoaviy mashg'ulotlar uchun.", "Для командных тренировок."),
        ("Nike Pro Kompressiya", "Mushaklarni qo'llab-quvvatlovchi kiyim.", "Компрессионная одежда, поддерживает мышцы."),
        ("Adidas Tiro Trening", "Futbol mashg'ulotlari uchun klassik to'plam.", "Классический комплект для футбольных тренировок."),
        ("Adidas Essentials Kostyum", "Qulay kundalik sport kostyumi.", "Удобный повседневный спортивный костюм."),
        ("Adidas Techfit Kompressiya", "Elastik, tanaga yopishadigan kiyim.", "Эластичная облегающая одежда."),
        ("Puma Team Trening", "Yengil va qulay mashg'ulot to'plami.", "Лёгкий и удобный тренировочный комплект."),
        ("Puma Essentials Kostyum", "Har kuni kiyish uchun qulay.", "Удобный на каждый день."),
        ("Under Armour Trening", "Nafas oladigan material, intensiv mashq uchun.", "Дышащий материал для интенсивных тренировок."),
    ], "💪", "S-XXL"),
    "balls": _mk([
        ("Adidas Trionda Pro", "Trionda dizaynidagi o'yin to'pi.", "Игровой мяч в дизайне Trionda."),
        ("Adidas Champions League Pro", "Chempionlar ligasi dizaynidagi to'p.", "Мяч в дизайне Лиги чемпионов."),
        ("Adidas Al Rihla Pro", "Mashhur o'yin to'pi dizayni.", "Дизайн известного игрового мяча."),
        ("Adidas Tiro Club", "Mashg'ulot uchun chidamli to'p.", "Прочный мяч для тренировок."),
        ("Nike Flight", "Aniq parvoz va barqaror aylanish.", "Точный полёт и стабильное вращение."),
        ("Nike Strike", "O'yin va mashg'ulot uchun.", "Для игры и тренировок."),
        ("Nike Pitch", "Hamyonbop va chidamli to'p.", "Доступный и прочный мяч."),
        ("Puma Orbita", "Zamonaviy dizayn, yaxshi nazorat.", "Современный дизайн, хороший контроль."),
        ("Select Brillant Super", "Professional darajadagi to'p.", "Мяч профессионального уровня."),
        ("Mikasa Futsal", "Zal futboli (futsal) uchun to'p.", "Мяч для зального футбола (футзал)."),
    ], "⚽", "4 / 5"),
    "shoes": _mk([
        ("Nike Air Max 90", "Klassik dizayn, yumshoq taglik.", "Классический дизайн, мягкая подошва."),
        ("Nike Air Force 1", "Har doim modada bo'lgan klassika.", "Классика, всегда в моде."),
        ("Nike Air Max 270", "Katta Air taglik, ajoyib qulaylik.", "Большая Air-подошва, отличный комфорт."),
        ("Nike Dunk Low", "Ko'cha uslubidagi mashhur model.", "Популярная модель в уличном стиле."),
        ("Adidas Samba", "Zamonaviy klassik krasovka.", "Современная классика."),
        ("Adidas Gazelle", "Yengil va uslubli kundalik model.", "Лёгкая и стильная повседневная модель."),
        ("Adidas Superstar", "Mashhur klassik model.", "Знаменитая классика."),
        ("Puma Suede Classic", "Zamsha material, retro uslub.", "Замша, ретро-стиль."),
        ("New Balance 550", "Retro basketbol uslubi.", "Ретро-стиль баскетбольных кроссовок."),
        ("New Balance 574", "Kundalik kiyish uchun juda qulay.", "Очень удобные на каждый день."),
    ], "👟", "39-44"),
    "socks": _mk([
        ("Nike Matchfit", "O'yin uchun zich o'tiradigan getra.", "Игровые гетры с плотной посадкой."),
        ("Nike Academy", "Mashg'ulot uchun chidamli getra.", "Прочные гетры для тренировок."),
        ("Nike Squad", "Jamoa uchun qulay getra.", "Удобные командные гетры."),
        ("Nike Strike Getra", "Yengil va nafas oladigan getra.", "Лёгкие дышащие гетры."),
        ("Adidas Milano 23", "Klassik jamoaviy getra.", "Классические командные гетры."),
        ("Adidas Santos 18", "Mustahkam va yumshoq getra.", "Прочные и мягкие гетры."),
        ("Adidas Adi Sock 23", "Qulay mahkamlanadigan getra.", "Гетры с удобной фиксацией."),
        ("Adidas Copa Zone", "Yostiqchali, qulay getra.", "Гетры с амортизацией."),
        ("Puma Team Liga", "O'yin uchun yengil getra.", "Лёгкие игровые гетры."),
        ("Puma Liga Core", "Hamyonbop kundalik getra.", "Доступные повседневные гетры."),
    ], "🧦", "Universal"),
    "dumbbell": [P(f"Gantel {n} kg", "🏋️", "Mashq uchun sport gantel.", "Спортивная гантель для тренировок.", None, f"{n} kg")
                 for n in (2, 4, 6, 8, 10, 12, 16, 20)]
                + [P("Yig'ma gantel 20 kg", "🏋️", "Og'irligi o'zgartiriladigan gantel to'plami.", "Наборная гантель с регулируемым весом.", None, "20 kg"),
                   P("Yig'ma gantel 30 kg", "🏋️", "Og'irligi o'zgartiriladigan gantel to'plami.", "Наборная гантель с регулируемым весом.", None, "30 kg")],
    "swim": _mk([
        ("Arena Cobra Ultra ko'zoynak", "Musobaqa uslubidagi suzish ko'zoynagi.", "Очки для плавания в соревновательном стиле."),
        ("Speedo Biofuse ko'zoynak", "Qulay o'tiradigan suzish ko'zoynagi.", "Удобные очки для плавания."),
        ("Speedo Silikon shapka", "Silikon suzish shapkasi.", "Силиконовая шапочка для плавания."),
        ("Arena Silikon shapka", "Chidamli silikon shapka.", "Прочная силиконовая шапочка."),
        ("Speedo Jammer", "Erkaklar uchun suzish shortisi.", "Плавки-джаммеры для мужчин."),
        ("Arena Jammer", "Musobaqa uchun suzish shortisi.", "Плавки-джаммеры для соревнований."),
        ("Speedo Ayollar kupalnigi", "Ayollar uchun suzish kupalnigi.", "Женский купальник для плавания."),
        ("Burun qisqich va quloq tiqin", "Suzishda qulaylik uchun to'plam.", "Набор для комфортного плавания."),
        ("Speedo Suzish shippagi", "Basseyn uchun sirpanmaydigan shippak.", "Нескользящие тапочки для бассейна."),
        ("Arena Suzish sumkasi", "Suzish buyumlari uchun sumka.", "Сумка для вещей для плавания."),
    ], "🏊", "Universal"),
}
# Yangiliklar: yuqoridagi mahsulotlardan "new" belgisi borlarini yig'adi
CATALOG["new"] = [p for items in list(CATALOG.values()) for p in items if p.get("new")]


# ----------------------------------------------------------------------------
# MATN USLUBI (Telegramda CSS yo'q, shuning uchun maxsus Unicode harflar ishlatamiz)
# STYLE:  "bold"  -> 𝗤𝗮𝗹𝗶𝗻  |  "smallcaps" -> ǫᴀʟɪɴ  |  "plain" -> oddiy
# ----------------------------------------------------------------------------
STYLE = "bold"

_SC = dict(zip("abcdefghijklmnopqrstuvwxyz", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"))


def _bold(ch: str) -> str:
    if "A" <= ch <= "Z":
        return chr(0x1D5D4 + ord(ch) - ord("A"))
    if "a" <= ch <= "z":
        return chr(0x1D5EE + ord(ch) - ord("a"))
    if "0" <= ch <= "9":
        return chr(0x1D7EC + ord(ch) - ord("0"))
    return ch


def fancy(text: str) -> str:
    if STYLE == "bold":
        return "".join(_bold(c) for c in text)
    if STYLE == "smallcaps":
        return "".join(_SC.get(c.lower(), c) for c in text)
    return text


# ----------------------------------------------------------------------------
# FOYDALANUVCHI TILI
# ----------------------------------------------------------------------------
def load_users() -> dict:
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


USERS = load_users()


def get_lang(uid: int) -> str:
    return USERS.get(str(uid), "uz")


def set_lang(uid: int, lang: str):
    USERS[str(uid)] = lang
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(USERS, f)
    except OSError:
        pass


# ----------------------------------------------------------------------------
# KLAVIATURALAR
# ----------------------------------------------------------------------------
def lang_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇺🇿 O'zbekcha", callback_data="lang:uz")
    b.button(text="🇷🇺 Русский", callback_data="lang:ru")
    b.adjust(2)
    return b.as_markup()


def menu_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, names in CATEGORIES.items():
        b.button(text=names[lang], callback_data=f"cat:{key}")
    b.adjust(2)
    b.row(InlineKeyboardButton(text=T["contact"][lang], callback_data="contact"),
          InlineKeyboardButton(text=T["location"][lang], callback_data="loc"))
    b.row(InlineKeyboardButton(text=T["lang"][lang], callback_data="chlang"))
    return b.as_markup()


def products_kb(cat: str, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, p in enumerate(CATALOG.get(cat, [])):
        b.button(text=p["name"], callback_data=f"prod:{cat}:{i}")
    b.adjust(1)
    b.row(InlineKeyboardButton(text=T["back"][lang], callback_data="menu"))
    return b.as_markup()


def product_kb(cat: str, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=T["order"][lang], url=f"https://t.me/{ADMIN_USERNAME}"))
    b.row(InlineKeyboardButton(text=T["back"][lang], callback_data=f"cat:{cat}"))
    return b.as_markup()


def info_kb(page: int, lang: str) -> InlineKeyboardMarkup:
    last = len(INFO[lang]) - 1
    back_cb = "chlang" if page == 0 else f"info:{page - 1}"
    next_cb = "menu" if page == last else f"info:{page + 1}"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=T["prev"][lang], callback_data=back_cb),
        InlineKeyboardButton(text=T["next"][lang], callback_data=next_cb),
    ]])


def back_kb(lang: str, extra=None) -> InlineKeyboardMarkup:
    rows = []
    if extra:
        rows.append(extra)
    rows.append([InlineKeyboardButton(text=T["back"][lang], callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cat_image(cat: str) -> str:
    return f"images/cat_{cat}.jpg"


# ----------------------------------------------------------------------------
# YORDAMCHI: eski xabarni o'chirib, yangisini yuborish (rasm <-> matn almashishi uchun)
# ----------------------------------------------------------------------------
async def show(call: CallbackQuery, text: str, kb, photo: str | None = None):
    try:
        await call.message.delete()
    except Exception:
        pass
    if photo and os.path.exists(photo):
        await call.message.answer_photo(FSInputFile(photo), caption=text, reply_markup=kb)
    else:
        await call.message.answer(text, reply_markup=kb)


# ----------------------------------------------------------------------------
# HANDLERLAR
# ----------------------------------------------------------------------------
dp = Dispatcher()


@dp.message(CommandStart())
async def start(msg: Message):
    await msg.answer(T["choose_lang"]["uz"], reply_markup=lang_kb())


@dp.callback_query(F.data == "chlang")
async def change_lang(call: CallbackQuery):
    await show(call, T["choose_lang"]["uz"], lang_kb())
    await call.answer()


@dp.callback_query(F.data.startswith("lang:"))
async def pick_lang(call: CallbackQuery):
    lang = call.data.split(":")[1]
    set_lang(call.from_user.id, lang)
    await show(call, INFO[lang][0], info_kb(0, lang), WELCOME_IMAGE)
    await call.answer()


@dp.callback_query(F.data.startswith("info:"))
async def info_page(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    page = int(call.data.split(":")[1])
    await show(call, INFO[lang][page], info_kb(page, lang), WELCOME_IMAGE)
    await call.answer()


@dp.callback_query(F.data == "menu")
async def to_menu(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    await show(call, T["choose_cat"][lang], menu_kb(lang), MENU_IMAGE)
    await call.answer()


@dp.callback_query(F.data == "contact")
async def contact(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    text = f"{T['contact'][lang]}\n\n{T['contact_text'][lang]}\n\n{PHONES_TXT}\n💬 @{ADMIN_USERNAME}"
    write = [InlineKeyboardButton(text=T["write"][lang], url=f"https://t.me/{ADMIN_USERNAME}")]
    await show(call, text, back_kb(lang, write))
    await call.answer()


@dp.callback_query(F.data == "loc")
async def location(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    if LOCATION_LAT is None or LOCATION_LON is None:
        text = f"{T['location'][lang]}\n\n{T['soon'][lang]}\n\n{PHONES_TXT}"
        await show(call, text, back_kb(lang))
        await call.answer()
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer_location(LOCATION_LAT, LOCATION_LON)
    text = T["location"][lang] + (f"\n\n{ADDRESS}" if ADDRESS else "") + f"\n\n{PHONES_TXT}"
    await call.message.answer(text, reply_markup=back_kb(lang))
    await call.answer()


@dp.callback_query(F.data.startswith("cat:"))
async def open_cat(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    cat = call.data.split(":")[1]
    title = CATEGORIES[cat][lang]
    if not CATALOG.get(cat):
        await show(call, f"{title}\n\n{T['soon'][lang]}", back_kb(lang), cat_image(cat))
    else:
        await show(call, f"{title}\n\n{T['choose_prod'][lang]}", products_kb(cat, lang), cat_image(cat))
    await call.answer()


@dp.callback_query(F.data.startswith("prod:"))
async def open_product(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    _, cat, idx = call.data.split(":")
    p = CATALOG[cat][int(idx)]
    e = p.get("emoji", "🔥")
    title = p.get("title", p["name"])
    if p.get("price"):
        price_txt = fancy(f"{p['price']:,}".replace(",", "."))
    else:
        price_txt = fancy(T["negotiable"][lang])
    desc = p.get("desc", {}).get(lang)
    lines = [f"{e}{fancy(title)}{e}"]
    if desc:
        lines.append(desc)
    lines += [
        f"{fancy(T['size'][lang])}: {fancy(p['sizes'])}",
        fancy(T["quality"][lang]),
        f"{fancy(T['price'][lang])}💸:{price_txt}",
        fancy(T["bonus"][lang]),
        f"@{ADMIN_USERNAME}",
        PHONES_TXT,
    ]
    text = "\n".join(lines)
    photo = p.get("photo")
    if not photo or not os.path.exists(photo):
        photo = FALLBACK_PHOTO or cat_image(cat)
    await show(call, text, product_kb(cat, lang), photo)
    await call.answer()


# ----------------------------------------------------------------------------
# ADMIN: rasm yuklash (botning o'ziga rasm yuboring, izohga mahsulot nomini yozing)
# ----------------------------------------------------------------------------
@dp.message(Command("id"))
async def my_id(msg: Message):
    await msg.answer(f"Sizning ID: {msg.from_user.id}\nADMIN_ID={msg.from_user.id}")


def _all_products():
    for cat, items in CATALOG.items():
        if cat == "new":      # Yangiliklar — boshqa bo'limlardan takrorlanadi
            continue
        for p in items:
            yield cat, p


@dp.message(Command("rasmlar"))
async def missing_photos(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    lines = [f"• {p['name']}" for _, p in _all_products()
             if not p.get("photo") or not os.path.exists(p["photo"])]
    if not lines:
        await msg.answer("Hamma mahsulotda rasm bor ✅")
        return
    await msg.answer(f"Rasmi yo'q mahsulotlar: {len(lines)} ta\nRasm yuborib, izohiga mahsulot nomini yozing.")
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > 3500:
            await msg.answer(chunk)
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await msg.answer(chunk)


@dp.message(F.photo)
async def save_photo(msg: Message, bot: Bot):
    if msg.from_user.id not in ADMIN_IDS:
        return
    caption = (msg.caption or "").strip()
    if not caption:
        await msg.answer("Rasm izohiga mahsulot nomini yozing, masalan: Nike Phantom 6 Elite\n(/rasmlar — rasmi yo'qlar ro'yxati)")
        return
    key = _slug(caption)
    target = None
    for cat, p in _all_products():
        if key in (_slug(p["name"]), os.path.splitext(os.path.basename(p.get("photo", "")))[0]):
            target = p
            break
    if not target:
        await msg.answer("Bunday mahsulot topilmadi. Nomini aynan ro'yxatdagidek yozing (/rasmlar).")
        return
    os.makedirs("images", exist_ok=True)
    file = await bot.get_file(msg.photo[-1].file_id)
    await bot.download_file(file.file_path, destination=target["photo"])
    await msg.answer(f"✅ Saqlandi: {target['name']}")


# ----------------------------------------------------------------------------
# Render (Web Service) uchun: PORT'da kichik server. UptimeRobot shu manzilni
# har 5 daqiqada ochib tursa, bot uxlab qolmaydi.
# ----------------------------------------------------------------------------
async def _health(_request):
    return web.Response(text="SportUp bot ishlayapti ✅")


async def start_web():
    port = os.getenv("PORT")
    if not port:
        return
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(port)).start()
    print(f"Web server ishga tushdi: port {port}")


async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi! .env faylga yoki Render Environment'ga BOT_TOKEN=... yozing.")
    await start_web()
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
