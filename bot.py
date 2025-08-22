import os
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = os.getenv("API_TOKEN")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", 5432),
}

TABLES = [
    "rAddressProblem",
    "rApplication",
    "rApplicationAction",
    "rApplicationAnswer",
    "rComments"
]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def get_table_counts():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    result = []
    for t in TABLES:
        cursor.execute(f'SELECT COUNT(*) FROM public."{t}";')
        count = cursor.fetchone()[0]
        result.append(f"{t}: {count}")

    cursor.close()
    conn.close()
    return "\n".join(result)


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📊 Количество записей")
    await message.answer("Привет! Нажми кнопку, чтобы узнать количество записей в таблицах.", reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text == "📊 Количество записей")
async def send_counts(message: types.Message):
    counts = get_table_counts()
    await message.answer(f"📊 Количество записей:\n\n{counts}")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
