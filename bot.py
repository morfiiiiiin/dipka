import logging
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
    raise RuntimeError("This code requires aiogram version 3.x. Please install aiogram 3.20.0 or compatible.")

# Инициализация
BOT_TOKEN = os.getenv("BOT_TOKEN", "7808847944:AAFTrarhuICx5MrIndS4yu4CvfVEUVhGg5w")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://dipka.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)  # Подключение роутера к диспетчеру

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация модели Hugging Face
sentiment_analyzer = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# Курс валют: 1 USD = 100 RUB
USD_TO_RUB = 100

# Рекомендации с подробными описаниями и фотографиями (URL заглушки)
APPLIANCE_RECOMMENDATIONS = {
    "refrigerator": {
        "Samsung": {
            "description": (
                "Samsung CoolFrost 300L (59 900 ₽, энергоэффективный, No Frost) — современный холодильник с технологией No Frost, предотвращающей образование льда. Объем 300 литров идеален для семьи из 3-4 человек. Оснащен инверторным компрессором для тихой работы (уровень шума 38 дБ) и экономии энергии (класс A++). Подходит для хранения свежих продуктов благодаря зоне свежести.\n"
                "Samsung EcoTwin 350L (69 900 ₽, двойной компрессор) — модель с увеличенным объемом и двумя независимыми компрессорами для холодильной и морозильной камер. Имеет цифровой дисплей и функцию быстрого замораживания. Идеально для больших семей или тех, кто делает запасы продуктов."
            ),
            "photo_url": "https://example.com/samsung_refrigerator.jpg"
        },
        "LG": {
            "description": (
                "LG SmartFridge 400L (79 900 ₽, с Wi-Fi, инверторный компрессор) — умный холодильник с возможностью управления через смартфон. Объем 400 литров подходит для больших семей. Технология DoorCooling+ обеспечивает равномерное охлаждение. Энергопотребление класса A+++, уровень шума 36 дБ. Отличный выбор для тех, кто ценит технологии и комфорт.\n"
                "LG FrostGuard 450L (89 900 ₽, антибактериальное покрытие) — модель с увеличенным объемом и специальным покрытием, предотвращающим рост бактерий. Имеет функцию быстрого охлаждения и зону свежести для овощей и фруктов. Подходит для хранения большого количества продуктов."
            ),
            "photo_url": "https://example.com/lg_refrigerator.jpg"
        },
        "Bosch": {
            "description": (
                "Bosch VitaFresh 320L (64 900 ₽, технология VitaFresh, энергосбережение) — холодильник с системой VitaFresh, которая сохраняет свежесть продуктов до 3 раз дольше. Объем 320 литров, класс энергопотребления A++. Подходит для семей среднего размера, ценящих качество и долговечность.\n"
                "Bosch MultiAir 350L (74 900 ₽, система MultiAirFlow) — модель с равномерным распределением холодного воздуха, что предотвращает перепады температуры. Имеет сенсорное управление и низкий уровень шума (37 дБ). Идеально для хранения деликатных продуктов."
            ),
            "photo_url": "https://example.com/bosch_refrigerator.jpg"
        },
        "Haier": {
            "description": (
                "Haier FreshZone 280L (54 900 ₽, зона свежести, No Frost) — компактный холодильник с технологией No Frost и зоной свежести для длительного хранения овощей и фруктов. Класс энергопотребления A+, уровень шума 39 дБ. Подходит для небольших семей или квартир.\n"
                "Haier SmartCool 330L (69 900 ₽, умное управление) — модель с функцией управления температурой через приложение. Обеспечивает точное охлаждение и экономию энергии (класс A++). Идеально для тех, кто ищет современные решения по доступной цене."
            ),
            "photo_url": "https://example.com/haier_refrigerator.jpg"
        },
        "Whirlpool": {
            "description": (
                "Whirlpool 6th Sense 340L (67 900 ₽, технология 6th Sense) — холодильник с интеллектуальной системой контроля температуры, которая адаптируется к содержимому. Объем 340 литров, класс A++. Подходит для семей, ценящих надежность и стабильность.\n"
                "Whirlpool Supreme 400L (84 900 ₽, No Frost, зона свежести) — модель с увеличенным объемом и технологией No Frost. Имеет антибактериальный фильтр и низкий уровень шума (38 дБ). Отличный выбор для больших семей."
            ),
            "photo_url": "https://example.com/whirlpool_refrigerator.jpg"
        }
    },
    "washing_machine": {
        "Bosch": {
            "description": (
                "Bosch EcoWash 7kg (49 900 ₽, тихая работа, инверторный двигатель) — стиральная машина с загрузкой 7 кг и уровнем шума до 70 дБ при отжиме. Технология EcoSilence Drive обеспечивает долговечность и тишину. Программы для деликатных тканей и экономии воды. Подходит для небольших семей.\n"
                "Bosch Serie 8 9kg (79 900 ₽, 1400 об/мин, ActiveWater Plus) — модель с увеличенной загрузкой и высокой скоростью отжима. Имеет функцию дозагрузки и автоматическое определение веса белья. Идеально для больших семей или частой стирки."
            ),
            "photo_url": "https://example.com/bosch_washing_machine.jpg"
        },
        "AEG": {
            "description": (
                "AEG L9FEC966R 8kg (79 900 ₽, ProSense, 1600 об/мин) — стиральная машина с технологией ProSense, которая оптимизирует время стирки и расход воды. Высокая скорость отжима и низкий уровень шума (73 дБ). Подходит для тех, кто ценит качество стирки.\n"
                "AEG L6FBG842 7kg (59 900 ₽, защита от протечек, 1200 об/мин) — компактная модель с системой AquaControl для защиты от протечек. Программы для шерсти и деликатных тканей. Идеально для небольших квартир."
            ),
            "photo_url": "https://example.com/aeg_washing_machine.jpg"
        },
        "Miele": {
            "description": (
                "Miele WEG665 8kg (99 900 ₽, TwinDos, 1600 об/мин) — премиальная стиральная машина с системой автоматического дозирования моющего средства TwinDos. Высокая скорость отжима и программы для аллергиков. Подходит для тех, кто ищет лучшее качество.\n"
                "Miele WSF863 7kg (84 900 ₽, PowerWash, антиаллергенная стирка) — модель с технологией PowerWash для глубокой очистки. Имеет низкий уровень шума (72 дБ) и высокую энергоэффективность (A+++). Идеально для семей с детьми."
            ),
            "photo_url": "https://example.com/miele_washing_machine.jpg"
        },
        "Samsung": {
            "description": (
                "Samsung AddWash 9kg (84 900 ₽, добавление белья, 1400 об/мин) — стиральная машина с функцией AddWash, позволяющей добавлять белье во время стирки. Имеет инверторный двигатель и умное управление через приложение. Подходит для больших семей.\n"
                "Samsung QuickDrive 8kg (74 900 ₽, ускоренная стирка) — модель с технологией QuickDrive, сокращающей время стирки на 50%. Класс энергопотребления A+++, уровень шума 73 дБ. Отличный выбор для занятых людей."
            ),
            "photo_url": "https://example.com/samsung_washing_machine.jpg"
        },
        "Haier": {
            "description": (
                "Haier HW70 7kg (49 900 ₽, инверторный двигатель, 1200 об/мин) — компактная стиральная машина с тихой работой (уровень шума 70 дБ) и высокой энергоэффективностью (A+++). Программы для деликатных тканей и быстрой стирки. Подходит для небольших семей.\n"
                "Haier SuperDrum 9kg (69 900 ₽, 1400 об/мин, паровая стирка) — модель с функцией паровой стирки для удаления аллергенов и запахов. Имеет сенсорное управление и низкий уровень шума (71 дБ). Идеально для аллергиков."
            ),
            "photo_url": "https://example.com/haier_washing_machine.jpg"
        },
        "Whirlpool": {
            "description": (
                "Whirlpool FreshCare 7kg (54 900 ₽, технология FreshCare+, 1200 об/мин) — стиральная машина с функцией поддержания свежести белья после стирки. Энергоэффективность A+++, уровень шума 72 дБ. Подходит для тех, кто часто забывает вынимать белье.\n"
                "Whirlpool SupremeCare 9kg (79 900 ₽, 1400 об/мин, 6th Sense) — модель с интеллектуальной системой 6th Sense, оптимизирующей расход воды и энергии. Имеет программы для деликатных тканей и низкий уровень шума (70 дБ). Отличный выбор для больших семей."
            ),
            "photo_url": "https://example.com/whirlpool_washing_machine.jpg"
        }
    },
    "microwave": {
        "Panasonic": {
            "description": (
                "Panasonic QuickHeat 25L (14 900 ₽, 1000W, компактный) — микроволновая печь с эффективной мощностью 1000 Вт и компактными размерами. Имеет автоматические программы для разогрева и разморозки. Подходит для небольших кухонь.\n"
                "Panasonic Inverter 32L (19 900 ₽, инверторная технология) — модель с инверторной технологией для равномерного нагрева. Объем 32 литра, сенсорное управление. Идеально для семей, готовящих сложные блюда."
            ),
            "photo_url": "https://example.com/panasonic_microwave.jpg"
        },
        "Toshiba": {
            "description": (
                "Toshiba MultiCook 30L (19 900 ₽, с грилем, легкая очистка) — микроволновка с функцией гриля и объемом 30 литров. Имеет покрытие EasyClean для легкой очистки. Подходит для любителей запеченных блюд.\n"
                "Toshiba SmartCook 28L (17 900 ₽, сенсорное управление) — модель с сенсорным управлением и автоматическими программами. Мощность 900 Вт, уровень шума минимальный. Отличный выбор для современных кухонь."
            ),
            "photo_url": "https://example.com/toshiba_microwave.jpg"
        },
        "Sharp": {
            "description": (
                "Sharp AutoMenu 20L (12 900 ₽, автоматические программы) — компактная микроволновка с мощностью 800 Вт и простым управлением. Подходит для разогрева и разморозки в небольших семьях.\n"
                "Sharp GrillMaster 26L (16 900 ₽, мощный гриль) — модель с грилем мощностью 1000 Вт и объемом 26 литров. Имеет функцию комбинированного приготовления. Идеально для тех, кто любит готовить разнообразно."
            ),
            "photo_url": "https://example.com/sharp_microwave.jpg"
        },
        "Haier": {
            "description": (
                "Haier Compact 20L (11 900 ₽, 700W, компактный) — микроволновка с минималистичным дизайном и мощностью 700 Вт. Подходит для маленьких кухонь и базовых задач (разогрев, разморозка).\n"
                "Haier GrillPro 25L (15 900 ₽, гриль, 900W) — модель с функцией гриля и сенсорным управлением. Объем 25 литров, легкая очистка. Отличный выбор для тех, кто ищет бюджетный гриль."
            ),
            "photo_url": "https://example.com/haier_microwave.jpg"
        },
        "Whirlpool": {
            "description": (
                "Whirlpool JetCook 25L (14 900 ₽, 900W, компактный) — микроволновка с функцией быстрого разогрева и автоматическими программами. Подходит для небольших семей.\n"
                "Whirlpool Max 30L (19 900 ₽, гриль, пароварка) — модель с функцией гриля и пароварки. Объем 30 литров, мощность 900 Вт. Идеально для здорового питания."
            ),
            "photo_url": "https://example.com/whirlpool_microwave.jpg"
        }
    },
    "vacuum_cleaner": {
        "Dyson": {
            "description": (
                "Dyson V15 Detect Absolute (79 900 ₽, лазерное обнаружение пыли, 240AW) — беспроводной пылесос с лазерной подсветкой для обнаружения мелкой пыли. Мощность всасывания 240 Вт, время работы до 60 минут. Подходит для аллергиков и владельцев домашних животных.\n"
                "Dyson V11 Animal (71 900 ₽, 185AW, до 60 мин) — модель с высокой эффективностью и оптимизированными насадками для уборки шерсти."
            ),
            "photo_url": "https://example.com/dyson_vacuum_cleaner.jpg"
        },
        "Philips": {
            "description": (
                "Philips Series 800L XC8347 (49 900 ₽, PowerCyclone 10, 190AW) — беспроводной пылесос с технологией PowerCyclone 10 для мощного всасывания. Имеет насадки для всех поверхностей. Подходит для больших домов.\n"
                "Philips Aqua Plus (39 900 ₽, влажная уборка) — модель с функцией влажной уборки и мощностью 180 Вт. Идеально для семей с детьми и аллергиков."
            ),
            "photo_url": "https://example.com/philips_vacuum_cleaner.jpg"
        },
        "Bosch": {
            "description": (
                "Bosch Series 8 (39 900 ₽, 25.2V, до 40 мин) — беспроводной пылесос с высокой мощностью и универсальными насадками. Подходит для уборки ковров и твердых полов.\n"
                "Bosch Unlimited (34 900 ₽, до 60 мин, AllFloor) — модель с высокой энергоэффективностью и компактным дизайном."
            ),
            "photo_url": "https://example.com/bosch_vacuum_cleaner.jpg"
        },
        "Haier": {
            "description": (
                "Haier Cyclone 350H (29 900 ₽, 180W, до 40 мин) — бюджетный беспроводной пылесос с хорошей мощностью всасывания. Подходит для небольших квартир.\n"
                "Haier AquaClean (39 900 ₽, влажная уборка) — модель с функцией влажной уборки и HEPA-фильтром."
            ),
            "photo_url": "https://example.com/haier_vacuum_cleaner.jpg"
        },
        "Whirlpool": {
            "description": (
                "Whirlpool Cordless 150W (27 900 ₽, до 45 мин) — компактный пылесос с легким весом и хорошей маневренностью. Подходит для небольших помещений.\n"
                "Whirlpool PowerClean 300W (44 900 ₽, до 50 мин, фильтр) — модель с высокой мощностью и фильтрацией."
            ),
            "photo_url": "https://example.com/whirlpool_vacuum_cleaner.jpg"
        }
    }
}

STORE_INFO = (
    "ℹ Информация:\n"
    "Часы работы: 00:00-24:00\n"
    "Адрес: г. Москва, ул. Примерная, 3\n"
    "Контакты: +7 (918) 123-45-67"
)

# FSM для обработки запросов к боту
class BotQuery(StatesGroup):
    waiting_for_query = State()

# Временная заглушка для ответов бота
FALLBACK_USER = {
    "холодильник": (
        "Рекомендую Samsung CoolFrost 300L (59 900 ₽, No Frost) — идеально для семьи из 3-4 человек, с тихой работой и зоной свежести.\n"
        "Или LG SmartCook 400L (64 900 ₽, с Wi-Fi) — для тех, кто любит умные технологии.\n"
        "Какой бюджет и функции вам важны?"
    ),
    "микроволновка": (
        "Панасоник QuickHeat 25L (14 900 ₽, компактная) — для небольших кухонь.\n"
        "Или Toshiba MultiCook 15L (19 900 ₽, с грилем) — для запекания.\n"
        "Нужен ли гриль или сенсорное управление?"
    )
}

# Функция для ответов бота с Hugging Face
async def get_user_response(query: str) -> str:
    try:
        query_lower = query.lower()
        result = sentiment_analyzer(query)[0]
        score = result['score']
        label = result['label']
        for appliance, response in FALLBACK_USER.items():
            if appliance in query_lower:
                print(f"Matched appliance: {appliance} for query: {query}")
                return f"{response} (Настроение: {label}, Confidence: {score:.2f})"
        print(f"No appliance matched for query: {query}")
        return f"Уточните, что вы ищете (например, холодильник, микроволновка), и я помогу с выбором!\n(Настроение: {label}, Confidence: {score:.2f})"
    except Exception as e:
        print(f"Error in Hugging Face: {str(e)}")
        return f"Error: {str(e)}"

# Клавиатуры
def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ Рекомендации", callback_data="recommend_menu")],
        [InlineKeyboardButton(text="❓ Спросить у бота", callback_data="ask_bot")],
        [InlineKeyboardButton(text="📍 Инфо", callback_data="info")]
    ])

def get_recommend_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❄ Холодильники", callback_data="recommend_refrigerator")],
        [InlineKeyboardButton(text="🧼 Стиральные машины", callback_data="recommend_washing_machine")],
        [InlineKeyboardButton(text="🔥 Микроволновки", callback_data="recommend_microwave")],
        [InlineKeyboardButton(text="🧹 Пылесосы", callback_data="recommend_vacuum_cleaner")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_start")]
    ])

def get_brand_keyboard(appliance: str):
    brands = APPLIANCE_RECOMMENDATIONS.get(appliance, {})
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🏷 {brand}", callback_data=f"brand:{appliance}:{brand}")]
        for brand in brands.keys()
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_recommend")])
    return keyboard

# Обработчики
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    print(f"User {message.from_user.id} started the bot")
    await message.reply(
        "Добро пожаловать в бот-консультант по бытовой технике! 🏠\n"
        "Я помогу выбрать технику или дам совет через умную систему рекомендаций.\n"
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
            print(f"Invalid appliance: {appliance}")
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
                print(f"Invalid appliance or brand: {appliance}, {brand}")
                await callback_query.message.edit_text("Ошибка: данные не найдены.", reply_markup=get_recommend_keyboard())
                return

            recommendation = APPLIANCE_RECOMMENDATIONS[appliance][brand]["description"]
            photo_url = APPLIANCE_RECOMMENDATIONS[appliance][brand]["photo_url"]
            await callback_query.message.delete()
            await callback_query.message.answer_photo(
                photo=photo_url,
                caption=f"Рекомендации для {brand} ({appliance.replace('_', ' ').title()}):\n{recommendation}",
                reply_markup=get_brand_keyboard(appliance)
            )
        except ValueError as e:
            print(f"Error parsing brand callback: {e}")
            await callback_query.message.edit_text("Ошибка обработки запроса.", reply_markup=get_recommend_keyboard())
        except Exception as e:
            print(f"Error sending photo: {e}")
            await callback_query.message.edit_text("Ошибка при отправке изображения.", reply_markup=get_brand_keyboard(appliance))

    elif data == "ask_bot":
        await callback_query.message.edit_text("Напишите свой вопрос о технике:")
        await state.set_state(BotQuery.waiting_for_query)

    elif data == "info":
        await callback_query.message.edit_text(STORE_INFO, reply_markup=get_start_keyboard())

    elif data == "back_to_start":
        await send_welcome(callback_query.message)

    elif data == "back_to_recommend":
        await callback_query.message.edit_text("Выберите категорию техники:", reply_markup=get_recommend_keyboard())

@router.message(BotQuery.waiting_for_query)
async def handle_bot_query(message: types.Message, state: FSMContext):
    if not message.text or len(message.text) > 500 or len(message.text.strip()) < 3:
        print(f"Invalid bot query from user {message.from_user.id}: {message.text}")
        await message.reply("Введите осмысленный вопрос (от 3 символов, до 500 символов).", reply_markup=get_start_keyboard())
        return
    print(f"User {message.from_user.id} asked: {message.text}")
    bot_response = await get_user_response(message.text)
    await message.reply(bot_response, reply_markup=get_start_keyboard())
    await state.clear()

# Webhook настройка
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    print(f"Webhook установлен на {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    print("Webhook удален")

# Роутинг и запуск
if __name__ == '__main__':
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    app = aiohttp.web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    aiohttp.web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
