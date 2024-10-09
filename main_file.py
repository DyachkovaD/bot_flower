import logging
import asyncio
import sys

from aiogram import Bot, Dispatcher, types, BaseMiddleware, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, CommandObject
from token_data import TOKEN
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler


dp = Dispatcher()  # запускает программу, к нему цепляются роутеры

flowers = {}
scheduler = AsyncIOScheduler()


@dp.message(CommandStart())
async def command_start_handler(message: types.Message, bot: Bot):
    await bot.send_message(message.chat.id, f"🪴 Привет! Я помогу тебе не забыть полить свои любимые растения 🪴. \n\n"
                                            f"Чтобы добавить растение 🌸 в календарь полива, введите\n"
                                            f"/add (цветок) (сколько раз в неделю нужно поливать) \n\n"
                                            f"Например: Фиалка 3")


@dp.message(Command("add"))
async def add_flower(message: types.Message, bot: Bot, command: CommandObject):
    if command.args is None:
        await message.answer(
            "Ошибка: не переданы аргументы"
        )
        return
    elif len(command.args.split()) != 2:
        await message.answer(
            "Ошибка: неправильно передали аргументы"
        )

    flower, frequency = command.args.split()
    flowers[flower] = frequency

    scheduler.add_job(bot.send_message, 'interval', days=int(frequency),
                      args=[message.from_user.id, f"Напоминаю 💧 полить 💧 {flower}"])

    watering = datetime.now() + timedelta(days=int(frequency))
    await message.answer(f"Следующий полив 💧: {datetime.strftime(watering, '%A %H:%M')}")


async def main() -> None:
    scheduler.start()

    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await dp.start_polling(bot)

if __name__=="__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout
    )
    asyncio.run(main())