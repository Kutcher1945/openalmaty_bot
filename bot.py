import os
import asyncio
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = os.getenv("API_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")  # id группы, куда шлем уведомления

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

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# хранение предыдущих значений
last_counts = {t: 0 for t in TABLES}


def get_table_counts():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    counts = {}
    for t in TABLES:
        cursor.execute(f'SELECT COUNT(*) FROM public."{t}";')
        counts[t] = cursor.fetchone()[0]

    cursor.close()
    conn.close()
    return counts


async def monitor_tables():
    """Фоновая задача — проверяет новые записи и шлет уведомления"""
    await bot.wait_until_ready()
    global last_counts

    while True:
        try:
            counts = get_table_counts()
            messages = []

            for t in TABLES:
                new_records = counts[t] - last_counts.get(t, 0)
                if new_records > 0:
                    messages.append(
                        f"📂 <b>{t}</b>\n➕ Новых записей: <b>{new_records:,}</b>\n"
                        f"📊 Всего: <b>{counts[t]:,}</b>"
                        .replace(",", " ")
                    )
                # обновляем last_counts
                last_counts[t] = counts[t]

            # если есть новые записи — отправляем сообщение
            if messages:
                text = "<b>🔔 Новые данные в БД!</b>\n\n" + "\n\n".join(messages)
                await bot.send_message(GROUP_CHAT_ID, text)

        except Exception as e:
            print("Ошибка мониторинга:", e)

        await asyncio.sleep(60)  # интервал проверки (60 сек)


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📊 Количество записей")
    await message.answer("Привет! Нажми кнопку, чтобы узнать количество записей в таблицах.", reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text == "📊 Количество записей")
async def send_counts(message: types.Message):
    counts = get_table_counts()
    text = ["<b>📊 Количество записей:</b>\n\n<pre>━━━━━━━━━━━━━━━━━━━━━━━"]
    for t in TABLES:
        text.append(f"📂 {t:<18} → {counts[t]:,}".replace(",", " "))
    text.append("━━━━━━━━━━━━━━━━━━━━━━━</pre>")
    await message.answer("\n".join(text))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(monitor_tables())  # запускаем фоновый мониторинг
    executor.start_polling(dp, skip_updates=True)
