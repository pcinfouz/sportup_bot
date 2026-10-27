"""
SportUp Telegram bot
Ishga tushirish:
    pip install aiogram
    python bot.py
Rasmlar: bot.py yonida  images/  papka oching.
"""
import asyncio
import json
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
BOT_TOKEN = os.getenv("BOT_TOKEN", "")  # .env faylda: BOT_TOKEN=123:ABC...
# Rasm yuklash huquqi: .env ga  ADMIN_ID=123456789  deb yozing (bir nechta bo'lsa vergul bilan)
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_ID", "").replace(" ", "").split(",") if x.isdigit()}
ADMIN_USERNAME = "berdaliyew"          # buyurtma uchun yoziladigan akkaunt
MENU_IMAGE = "images/menu.jpg"         # /start dan keyin chiqadigan rasm (ixtiyoriy)
USERS_FILE = "users.json"              # til tanlovi saqlanadi

# Rasmi yo'q mahsulotlarda kategoriya rasmi chiqadi (images/cat_<kategoriya>.jpg).
# Hamma joyga bitta umumiy rasm qo'ymoqchi bo'lsangiz, masalan: "images/f50_green.jpg"
FALLBACK_PHOTO = None

WELCOME_IMAGE = "images/welcome.jpg"

# /start -> til -> shu sahifalar ("Oldinga" / "Orqaga" tugmalari bilan) -> menyu
# Matnlarni o'zingiz tahrirlang.
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
            f"📞 Savollar uchun: @{ADMIN_USERNAME}"
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
            f"📞 По вопросам: @{ADMIN_USERNAME}"
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
}

# ----------------------------------------------------------------------------
# KATEGORIYALAR
# ----------------------------------------------------------------------------
CATEGORIES = {
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
# photo: images/ papkadagi fayl nomi (bo'lmasa rasmsiz chiqadi)
# ----------------------------------------------------------------------------
import re


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def P(name, emoji, desc_uz, desc_ru, price=350000, sizes="39-44"):
    """Mahsulot yasaydi. Rasm: images/<nomi_slug>.jpg  (rasm_nomlari.txt ga qarang).
    price=None bo'lsa 'Narx: kelishiladi' deb chiqadi."""
    return {"name": name, "title": name, "emoji": emoji, "sizes": sizes, "price": price,
            "desc": {"uz": desc_uz, "ru": desc_ru}, "photo": f"images/{_slug(name)}.jpg"}


CATALOG = {
    "boots": [
        # Rasmi bor mahsulot (to'liq yozuv):
        {"name": "F50 Shoes (Green:Black)", "title": "F50", "emoji": "💚", "sizes": "39-44",
         "price": 350000, "photo": "images/f50_green.jpg"},
        P("Nike Mercurial Superfly 10 / 11 Elite", "🔥", "Tezlik va ajoyib ushlanish.", "Скорость и отличное сцепление.", 350000),
        P("Nike Mercurial Vapor 16 / 17 Elite", "🔥", "Past yoqali klassik tezkor butsa.", "Классическая скоростная модель с низким верхом.", 350000),
        P("Nike Phantom 6 Elite", "🔥", "To'pni nazorat qilish va aniq zarba uchun.", "Для контроля мяча и точного удара.", 350000),
        P("Nike Tiempo Maestro / Legend 10 Elite", "🔥", "Yumshoq material, qulaylik va himoya.", "Мягкий материал, комфорт и защита.", 350000),
        P("Nike Premier III", "🔥", "Hamyonbop va sifatli klassik charm model.", "Доступная классическая кожаная модель.", 350000),
        P("Adidas Predator Elite / FT", "⚡", "Zarba aniqligi va to'pni ushlash uchun.", "Для точности удара и контроля мяча.", 350000),
        P("Adidas F50 Hyperfast / Elite", "⚡", "Ultra-yengil tezkor butsa.", "Сверхлёгкая скоростная бутса.", 350000),
        P("Adidas Copa Pure 4 / Icon 2", "⚡", "Yumshoq charm va maksimal qulaylik.", "Мягкая кожа и максимальный комфорт.", 350000),
        P("Adidas F50 Messi Elite", "⚡", "Messi uslubidagi maxsus seriya.", "Специальная серия в стиле Месси.", 350000),
        P("Adidas Copa Mundial", "⚡", "Modadan ketmaydigan haqiqiy klassika.", "Настоящая классика, не выходящая из моды.", 350000),
        P("Puma Ultra Nitro 7 / Ultimate", "🐆", "Juda yengil va tezkor butsa.", "Очень лёгкая и скоростная бутса.", 350000),
        P("Puma Future 9 Ultimate", "🐆", "Maydonda erkin harakat va kreativ o'yin uchun.", "Свобода движений и креативная игра.", 350000),
        P("Puma King Ultimate", "🐆", "Zamonaviy sintetik charm, yuqori komfort.", "Современная синтетическая кожа, высокий комфорт.", 350000),
        P("Mizuno Morelia Neo V Beta Japan", "🎌", "Premium yapon charmi, yengil va chidamli.", "Премиальная японская кожа, лёгкая и прочная.", 350000),
        P("Mizuno Morelia II Japan", "🎌", "Klassika va tabiiy to'p sezish hissi.", "Классика и естественное чувство мяча.", 350000),
        P("Mizuno Alpha III Japan", "🎌", "Tezkor o'yinchilar uchun yapon texnologiyasi.", "Японская технология для скоростных игроков.", 350000),
    ],
    "shin": [
        P("Nike Mercurial Lite", "🔥", "Yengil va qulay himoya.", "Лёгкая и удобная защита.", None),
        P("Nike Charge", "🔥", "Ishonchli himoya, qulay mahkamlanadi.", "Надёжная защита, удобная фиксация.", None),
        P("Adidas Tiro League", "⚡", "Kundalik mashg'ulotlar uchun.", "Для ежедневных тренировок.", None),
        P("Adidas Predator League", "⚡", "O'yin uchun yengil himoya.", "Лёгкая защита для игры.", None),
        P("Puma Ultra Flex", "🐆", "Egiluvchan va qulay sarakanoshka.", "Гибкие и удобные щитки.", None),
    ],
    "kits": [],
    "protein": [],
    "balls": [],
    "shoes": [],
    "socks": [],
    "dumbbell": [],
    "swim": [],
}


# ----------------------------------------------------------------------------
# MATN USLUBI (Telegramda CSS yo'q, shuning uchun maxsus Unicode harflar ishlatamiz)
# STYLE:  "bold"  -> 𝗤𝗮𝗹𝗶𝗻  |  "smallcaps" -> ǫᴀʟɪɴ  |  "plain" -> oddiy
# Faqat lotin harflari o'zgaradi; rus harflari va emoji o'zgarishsiz qoladi.
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
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(USERS, f)


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


@dp.callback_query(F.data.startswith("cat:"))
async def open_cat(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    cat = call.data.split(":")[1]
    title = CATEGORIES[cat][lang]
    if not CATALOG.get(cat):
        back = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=T["back"][lang], callback_data="menu")]])
        await show(call, f"{title}\n\n{T['soon'][lang]}", back, cat_image(cat))
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
    await msg.answer(f"Sizning ID: {msg.from_user.id}\n.env fayliga yozing:\nADMIN_ID={msg.from_user.id}")


def _all_products():
    for cat, items in CATALOG.items():
        for p in items:
            yield cat, p


@dp.message(Command("rasmlar"))
async def missing_photos(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    lines = []
    for cat, p in _all_products():
        ph = p.get("photo")
        if not ph or not os.path.exists(ph):
            lines.append(f"• {p['name']}")
    text = "Rasmi yo'q mahsulotlar:\n" + "\n".join(lines) if lines else "Hamma mahsulotda rasm bor ✅"
    await msg.answer(text + "\n\nRasm yuborib, izohiga mahsulot nomini yozing.")


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


async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi! .env faylga BOT_TOKEN=... yozing.")
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
