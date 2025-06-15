import os
import aiohttp
import aiogram
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from transformers import pipeline

# Проверка версии aiogram
print(f"Using aiogram version: {aiogram.__version__}")
if not aiogram.__version__.startswith("3"):
    raise RuntimeError("This code requires aiogram 3.20.0 or compatible.")

# Инициализация
BOT_TOKEN = os.getenv("BOT_TOKEN", "7808847944:AAFTrarhuICx5MrIndS4yu4CvfVEUVhGg5w")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://dipka.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Инициализация модели Hugging Face (легкая модель)
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased")

# Курс валют: 1 USD = 100 RUB
USD_TO_RUB = 100

# Рекомендации с подробными описаниями и фотографиями (URL заглушки)
APPLIANCE_RECOMMENDATIONS = {
    "refrigerator": {
        "Samsung": {
            "description": (
                "Samsung CoolFrost 300L (59 900 ₽, No Frost) — холодильник с технологией No Frost, объем 300 литров для семьи из 3-4 человек. Инверторный компрессор, класс A++, шум 38 дБ, зона свежести.\n"
                "Samsung EcoTwin 350L (69 900 ₽) — 350 литров, два компрессора, цифровой дисплей, быстрое замораживание."
            ),
            "photo_url": "https://example.com/samsung_refrigerator.jpg"
        },
        "LG": {
            "description": (
                "LG SmartFridge 400L (79 900 ₽, Wi-Fi) — умный холодильник с управлением через смартфон, 400 литров, DoorCooling+, класс A+++, шум 36 дБ.\n"
                "LG FrostGuard 450L (89 900 ₽) — 450 литров, антибактериальное покрытие, быстрое охлаждение, зона свежести."
            ),
            "photo_url": "https://example.com/lg_refrigerator.jpg"
        },
        "Bosch": {
            "description": (
                "Bosch VitaFresh 320L (64 900 ₽) — система VitaFresh, 320 литров, класс A++, сохраняет свежесть продуктов.\n"
                "Bosch MultiAir 350L (74 900 ₽) — MultiAirFlow, сенсорное управление, шум 37 дБ."
            ),
            "photo_url": "https://example.com/bosch_refrigerator.jpg"
        },
        "Haier": {
            "description": (
                "Haier FreshZone 280L (54 900 ₽, No Frost) — компактный, зона свежести, класс A+, шум 39 дБ.\n"
                "Haier SmartCool 330L (69 900 ₽) — управление через приложение, класс A++."
            ),
            "photo_url": "https://example.com/haier_refrigerator.jpg"
        },
        "Whirlpool": {
            "description": (
                "Whirlpool 6th Sense 340L (67 900 ₽) — контроль температуры, 340 литров, класс A++.\n"
                "Whirlpool Supreme 400L (84 900 ₽, No Frost) — 400 литров, антибактериальный фильтр, шум 38 дБ."
            ),
            "photo_url": "https://example.com/whirlpool_refrigerator.jpg"
        }
    },
    "washing_machine": {
        "Bosch": {
            "description": (
                "Bosch EcoWash 7kg (49 900 ₽) — 7 кг, EcoSilence Drive, шум 70 дБ, экономия воды.\n"
                "Bosch Serie 8 9kg (79 900 ₽) — 9 кг, 1400 об/мин, дозагрузка, ActiveWater Plus."
            ),
            "photo_url": "https://example.com/bosch_washing_machine.jpg"
        },
        "AEG": {
            "description": (
                "AEG L9FEC966R 8kg (79 900 ₽) — ProSense, 1600 об/мин, шум 73 дБ.\n"
                "AEG L6FBG842 7kg (59 900 ₽) — AquaControl, 1200 об/мин, для деликатных тканей."
            ),
            "photo_url": "https://example.com/aeg_washing_machine.jpg"
        },
        "Miele": {
            "description": (
                "Miele WEG665 8kg (99 900 ₽) — TwinDos, 1600 об/мин, для аллергиков.\n"
                "Miele WSF863 7kg (84 900 ₽) — PowerWash, A+++, шум 72 дБ."
            ),
            "photo_url": "https://example.com/miele_washing_machine.jpg"
        },
        "Samsung": {
            "description": (
                "Samsung AddWash 9kg (84 900 ₽) — AddWash, 1400 об/мин, умное управление.\n"
                "Samsung QuickDrive 8kg (74 900 ₽) — QuickDrive, A+++, шум 73 дБ."
            ),
            "photo_url": "https://example.com/samsung_washing_machine.jpg"
        },
        "Haier": {
            "description": (
                "Haier HW70 7kg (49 900 ₽) — 1200 об/мин, A+++, шум 70 дБ.\n"
                "Haier SuperDrum 9kg (69 900 ₽) — 1400 об/мин, паровая стирка, шум 71 дБ."
            ),
            "photo_url": "https://example.com/haier_washing_machine.jpg"
        },
        "Whirlpool": {
            "description": (
                "Whirlpool FreshCare 7kg (54 900 ₽) — FreshCare+, 1200 об/мин, A+++, шум 72 дБ.\n"
                "Whirlpool SupremeCare 9kg (79 900 ₽) — 6th Sense, 1400 об/мин, шум 70 дБ."
            ),
            "photo_url": "https://example.com/whirlpool_washing_machine.jpg"
        }
    },
    "microwave": {
        "Panasonic": {
            "description": (
                "Panasonic QuickHeat 25L (14 900 ₽, 1000W) — компактная, авто-программы.\n"
                "Panasonic Inverter 32L (19 900 ₽) — инверторная, сенсорное управление."
            ),
            "photo_url": "https://example.com/panasonic_microwave.jpg"
        },
        "Toshiba": {
            "description": (
                "Toshiba MultiCook 30L (19 900 ₽) — гриль, EasyClean.\n"
                "Toshiba SmartCook 28L (17 900 ₽) — сенсорное управление, 900W."
            ),
            "photo_url": "https://example.com/toshiba_microwave.jpg"
        },
        "Sharp": {
            "description": (
                "Sharp AutoMenu 20L (12 900 ₽, 800W) — компактная, простое управление.\n"
                "Sharp GrillMaster 26L (16 900 ₽) — гриль 1000W, комбинированное приготовление."
            ),
            "photo_url": "https://example.com/sharp_microwave.jpg"
        },
        "Haier": {
            "description": (
                "Haier Compact 20L (11 900 ₽, 700W) — минималистичный дизайн.\n"
                "Haier GrillPro 25L (15 900 ₽) — гриль, 900W, сенсорное управление."
            ),
            "photo_url": "https://example.com/haier_microwave.jpg"
        },
        "Whirlpool": {
            "description": (
                "Whirlpool JetChef 25L (14 900 ₽, 900W) — быстрый разогрев.\n"
                "Whirlpool Max 30L (19 900 ₽) — гриль, пароварка, 900W."
            ),
            "photo_url": "https://example.com/whirlpool_microwave.jpg"
        }
    },
    "vacuum_cleaner": {
        "Dyson": {
            "description": (
                "Dyson V15 Detect (79 900 ₽, 240AW) — лазерная подсветка, до 60 мин.\n"
                "Dyson V11 Animal (64 900 ₽, 185AW) — для уборки шерсти, до 60 мин."
            ),
            "photo_url": "https://example.com/dyson_vacuum_cleaner.jpg"
        },
        "Philips": {
            "description": (
                "Philips Series 8000 (49 900 ₽) — PowerCyclone 10, до 60 мин.\n"
                "Philips Aqua Plus (39 900 ₽) — влажная уборка, 180W."
            ),
            "photo_url": "https://example.com/philips_vacuum_cleaner.jpg"
        },
        "Bosch": {
            "description": (
                "Bosch Serie 8 (39 900 ₽, 25.2V) — до 45 мин, универсальные насадки.\n"
                "Bosch Unlimited (34 900 ₽) — до 60 мин, компактный."
            ),
            "photo_url": "https://example.com/bosch_vacuum_cleaner.jpg"
        },
        "Haier": {
            "description": (
                "Haier Cyclone (29 900 ₽, 180W) — до 40 мин, бюджетный.\n"
                "Haier AquaClean (39 900 ₽) — влажная уборка, HEPA-фильтр."
            ),
            "photo_url": "https://example.com/haier_vacuum_cleaner.jpg"
        },
        "Whirlpool": {
            "description": (
                "Whirlpool Cordless (27 900 ₽, 150W) — до 35 мин, легкий.\n"
                "Whirlpool PowerClean (44 900 ₽, 200W) — до 50 мин, HEPA-фильтр."
            ),
            "photo_url": "https://example.com/whirlpool_vacuum_cleaner.jpg"
        }
    }
}

STORE_INFO = (
    "ℹ️ Информация:\n"
    "Часы работы: 00:00-24:00\n"
    "Адрес: г. Москва, ул. Кирова, 4\n"
    "Контакты: +7 (918) 488-60-36, support@konsultantbot.ru"
)

# FSM для обработки запросов
class BotQuery(StatesGroup):
    waiting_for_query = State()

# Заглушка для ответов
FALLBACK_RESPONSES = {
    "холодильник": (
        "Samsung CoolFrost 300L (59 900 ₽, No Frost) — для семьи из 3-4 человек.\n"
        "LG SmartFridge 400L (79 900 ₽, Wi-Fi) — умные технологии.\n"
        "Какой бюджет?"
    ),
    "стиральная машина": (
        "Bosch EcoWash 7kg (49 900 ₽) — тихая, надежная.\n"
        "Samsung AddWash 9kg (84 900 ₽) — дозагрузка.\n"
        "Какой объем нужен?"
    ),
    "микроволновка": (
        "Panasonic QuickHeat 25L (14 900 ₽) — компактная.\n"
        "Toshiba MultiCook 30L (19 900 ₽) — гриль.\n"
        "Нужен гриль?"
    ),
    "пылесос": (
        "Dyson V15 (79 900 ₽) — мощный, для аллергиков.\n"
        "Philips Aqua Plus (39 900 ₽) — влажная уборка.\n"
        "Какой тип уборки?"
    )
}

# Функция для ответов с Hugging Face
async def get_bot_response(query: str) -> str:
    try:
        query_lower = query.lower()
        result = sentiment_analyzer(query)[0]
        score = result['score']
        label = result['label']
        for appliance, response in FALLBACK_RESPONSES.items():
            if appliance in query_lower:
                return f"{response} (Sentiment: {label}, Confidence: {score:.2f})"
        return f"Уточните технику (например, холодильник), и я помогу! (Sentiment: {label}, Confidence: {score:.2f})"
    except Exception as e:
        return f"Ошибка: {str(e)}"

# Клавиатуры
def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Рекомендации", callback_data="recommend_menu")],
        [InlineKeyboardButton(text="❓ Спросить у бота", callback_data="ask_bot")],
        [InlineKeyboardButton(text="📍 Инфо", callback_data="info")]
    ])

def get_recommend_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❄️ Холодильники", callback_data="recommend_refrigerator")],
        [InlineKeyboardButton(text="🧼 Стиральные машины", callback_data="recommend_washing_machine")],
        [InlineKeyboardButton(text="🔥 Микроволновки", callback_data="recommend_microwave")],
        [InlineKeyboardButton(text="🧹 Пылесосы", callback_data="recommend_vacuum_cleaner")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")]
    ])

def get_brand_keyboard(appliance: str):
    brands = APPLIANCE_RECOMMENDATIONS.get(appliance, {})
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🏷️ {brand}", callback_data=f"brand:{appliance}:{brand}")]
        for brand in brands.keys()
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_recommend")])
    return keyboard

# Обработчики
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply(
        "Добро пожаловать в бот-консультант по бытовой технике! 🏠\n"
        "Я помогу выбрать технику.\n"
        "Выберите опцию:",
        reply_markup=get_start_keyboard()
    )

@router.callback_query(lambda c: c.data)
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data

    if data == "recommend_menu":
        await callback_query.message.edit_text("Выберите категорию техники:", reply_markup=get_recommend_keyboard())

    elif data.startswith("recommend_"):
        appliance = data.replace("recommend_", "")
        if appliance not in APPLIANCE_RECOMMENDATIONS:
            await callback_query.message.edit_text("Ошибка: категория не найдена.", reply_markup=get_recommend_keyboard())
            return
        await callback_query.message.edit_text(
            f"Выберите бренд для {appliance.replace('_', ' ').title()}:",
            reply_markup=get_brand_keyboard(appliance)
        )

    elif data.startswith("brand:"):
        try:
            _, appliance, brand = data.split(":", 2)
            if appliance not in APPLIANCE_RECOMMENDATIONS or brand not in APPLIANCE_RECOMMENDATIONS[appliance]:
                await callback_query.message.edit_text("Ошибка: данные не найдены.", reply_markup=get_recommend_keyboard())
                return
            recommendation = APPLIANCE_RECOMMENDATIONS[appliance][brand]["description"]
            await callback_query.message.edit_text(
                f"Рекомендации для {brand} ({appliance.replace('_', ' ').title()}):\n{recommendation}",
                reply_markup=get_brand_keyboard(appliance)
            )
        except Exception:
            await callback_query.message.edit_text("Ошибка обработки.", reply_markup=get_recommend_keyboard())

    elif data == "ask_bot":
        await callback_query.message.edit_text("Напишите вопрос о технике:")
        await state.set_state(BotQuery.waiting_for_query)

    elif data == "info":
        await callback_query.message.edit_text(STORE_INFO, reply_markup=get_start_keyboard())

    elif data == "back_to_start":
        await send_welcome(callback_query.message)

    elif data == "back_to_recommend":
        await callback_query.message.edit_text("Выберите категорию техники:", reply_markup=get_recommend_keyboard())

@router.message(BotQuery.waiting_for_query)
async def handle_bot_query(message: types.Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 3:
        await message.reply("Введите вопрос от 3 символов.", reply_markup=get_start_keyboard())
        return
    bot_response = await get_bot_response(message.text)
    await message.reply(bot_response, reply_markup=get_start_keyboard())
    await state.clear()

# Webhook настройка
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    print(f"Webhook set to {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    print("Webhook removed")

# Запуск
if __name__ == '__main__':
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    app = aiohttp.web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    aiohttp.web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
