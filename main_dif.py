import logging
import asyncio
import sys

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, CommandObject

from token_data import TOKEN
from datetime import datetime, date, time, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler


dp = Dispatcher()  # запускает программу

flowers = {}    # {'user_id': {'flower' {'frequency': int, 'watering': datetime} } }
scheduler = AsyncIOScheduler()  # создаём наше расписание


# Функция будет обрабатывать команду /start
@dp.message(CommandStart())
async def command_start_handler(message: types.Message, bot: Bot):
    await bot.send_message(message.chat.id, f"🪴 Привет! Я помогу тебе не забыть полить свои любимые растения 🪴. \n\n"
                                            f"Чтобы добавить растение 🌸 в календарь полива, введите\n"
                                            f"/add (цветок) (через сколько дней поливать)\n\n"
                                            f"Например: Фиалка 2\n\n"
                                            f"Посмотреть график полива: /show")


# Эта функция будет обрабатывать команду /add <цветок> <частота полива>
@dp.message(Command("add"))
async def add_flower(message: types.Message, bot: Bot, command: CommandObject):
    # Проверяем правильно ли пользователь ввёл команду
    try:
        args = command.args.split()
        int(args[-1])
    # Если пользователь не ввёл аргументы
    except AttributeError:
        await message.answer(
            "Ошибка: не переданы аргументы"
        )
        return
    # Если пользователь не ввёл (ввёл неправильно) частоту полива
    except ValueError:
        await message.answer(
            "Ошибка: неправильно переданы аргументы\n"
            "Пример: Алоэ 3"
        )
        return

    flower, frequency = command.args.split()[:-1], int(command.args.split()[-1])
    flower = ' '.join(flower)   # на случай, если название цветка из нескольких слов
    watering = datetime.now() + timedelta(days=frequency)   # следующая дата полива
    if message.from_user.id not in flowers.keys():  # проверяем есть ли пользователь в базе, если нет, добавляем
        flowers[message.from_user.id] = {}
    flowers[message.from_user.id][flower] = {'frequency': frequency, 'watering': watering}

    # Делаем кнопку для подтверждения полива
    kb = [[types.KeyboardButton(text=f'Полит цветок {flower}')]]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    # Добавляем в расписание дату первого полива
    scheduler.add_job(bot.send_message, 'date', run_date=watering,
                      kwargs={'chat_id': message.from_user.id,
                              'text': f"Напоминаю полить 🌧️ {flower}",
                              'reply_markup': keyboard})

    await message.answer(f"Следующий полив 💧: {datetime.strftime(watering, '%A %H:%M')}")
    return


# Функция перезаписывает даты полива, если цветок полили
@dp.message(F.text.contains("Полит"))
async def watered(message: types.Message, bot: Bot):
    flower = ' '.join(message.text.split()[2:])     # забираем название цветка из сообщения о поливе
    frequency = flowers[message.from_user.id][flower]['frequency']  # берём из расписания частоту полива
    watering = datetime.now() + timedelta(days=frequency)   # устанавливаем следующую дату полива
    flowers[message.from_user.id][flower]['watering'] = watering

    # Делаем кнопку для подтверждения следующего полива
    kb = [[types.KeyboardButton(text=f'Полит цветок {flower}')]]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    # Добавляем в расписание дату следующего полива
    scheduler.add_job(bot.send_message, 'date', run_date=watering,
                      kwargs={'chat_id': message.from_user.id,
                              'text': f"Напоминаю полить 🌧️ {flower}",
                              'reply_markup': keyboard})
    await message.answer(f"Следующий полив 💧: {datetime.strftime(watering, '%A %H:%M')}")


# Функция выводит график полива
@dp.message(Command("show"))
async def show_flowers(message: types.Message):
    if message.from_user.id not in flowers.keys():
        await message.answer('График полива пуст')
        return

    user = message.from_user.id
    rezult = ''

    for flower in flowers[user].items():
        rezult += f"{flower[0]} - {datetime.strftime(flower[1]['watering'], '%A %H:%M')}\n"
    await message.answer(rezult)


async def main() -> None:
    scheduler.start()

    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout
    )
    asyncio.run(main())