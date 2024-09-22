import asyncio
import config
import os
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ContentType, LabeledPrice, PreCheckoutQuery
import logging
from aiogram.types import FSInputFile



# Код для логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_playment.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

bot = Bot(token=config.token)
dp = Dispatcher()

@dp.message(Command('start'))
async def start(message: types.Message):
    await message.reply("Добро пожаловать! Используйте /choose чтобы выбрать категорию или /random чтобы получить случайную инструкцию.")

@dp.message(Command('choose'))
async def choose_category(message: types.Message):
    categories = get_categories()
    
    if not categories:
        await message.reply("Категории не найдены.")
        return
    
    
    category_buttons = [types.KeyboardButton(text=cat) for cat in categories]
    
   
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[ [button] for button in category_buttons ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.reply("Выберите категорию:", reply_markup=keyboard)

@dp.message(Command('random'))
async def random_instruction(message: types.Message):
    await message.reply("Пожалуйста, заплатите, чтобы получить случайную инструкцию.")
    
    
    await bot.send_invoice(
        message.chat.id,
        title="Случайная инструкция",
        description="Оплата за получение случайной инструкции.",
        payload="invoice_payload_random",
        provider_token=config.PAYMENTS_PROVIDER_TOKEN,
        start_parameter="test-payment",
        currency="RUB",
        prices=[LabeledPrice(label="Instruction", amount=9900)]  # 99.00 RUB
    )

@dp.message(lambda msg: msg.text in get_categories())
async def category_chosen(message: types.Message):
    category = message.text
    await message.reply(f"Вы выбрали категорию '{category}'. Пожалуйста, заплатите, чтобы получить инструкцию.")
    
    
    await bot.send_invoice(
        message.chat.id,
        title=f"Инструкция по оплате - {category}",
        description=f"Оплата за получение инструкции из категории  '{category}'",
        payload=f"invoice_payload_{category}",
        provider_token=config.PAYMENTS_PROVIDER_TOKEN,
        start_parameter="test-payment",
        currency="RUB",
        prices=[LabeledPrice(label="Instruction", amount=9900)]  # 99.00 RUB
    )

@dp.pre_checkout_query(lambda query: True)
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)


class SuccessfulPaymentFilter:
    async def __call__(self, message: Message):
        return message.content_type == ContentType.SUCCESSFUL_PAYMENT

successful_payment_filter = SuccessfulPaymentFilter()

@dp.message(successful_payment_filter)
async def handle_payment(message: Message):
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload
    
   
    if payload == "invoice_payload_random":
        category = get_random_category()
    else:
        category = payload.split('_')[2]
    
    await message.reply(f"Оплата получена: {payment_info.total_amount / 100} RUB")
    
    
    instruction_file = get_random_instruction(category)
    
    if instruction_file:
        try:
           
            input_file = FSInputFile(instruction_file)
            await bot.send_document(message.chat.id, input_file)
            await message.reply("Вот ваша инструкция")
        except Exception as e:
            logger.error(f"Ошибка отправки инструкции: {e}")
            await message.reply("Извините, при получении инструкции произошла ошибка.")
    else:
        await message.reply("К сожалению, при получении инструкции произошла ошибка.")

def get_categories():
    try:
        return [d for d in os.listdir(config.INSTRUCTIONS_FOLDER) if os.path.isdir(os.path.join(config.INSTRUCTIONS_FOLDER, d))]
    except Exception as e:
        logger.error(f"Ошибка получения категорий: {e}")
        return []

def get_random_instruction(category):
    try:
        folder_path = os.path.join(config.INSTRUCTIONS_FOLDER, category)
        
        
        files = os.listdir(folder_path)
        if not files:
            return None
        
        
        file = random.choice(files)
        return os.path.join(folder_path, file)
    except Exception as e:
        logger.error(f"Ошибка получения инструкции: {e}")
        return None

def get_random_category():
    try:
        categories = get_categories()
        if not categories:
            return None
        return random.choice(categories)
    except Exception as e:
        logger.error(f"Ошибка получения случайной категории: {e}")
        return None

# Запуск бота
async def main():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    print("Bot started")
    asyncio.run(main())
