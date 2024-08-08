from telegram import (
    Bot,
)

from config import (
    TOKEN
)
from models import (
    User,
)
from utils import (
    Logger,
    fh,
)


class ProgramRemind:
    def __init__(self, user_id):
        self.user = User.get_by_id(user_id)
        self.chat_id = self.user.chat_id
        self.lang = self.user.lang
        self.silent = self.user.extra_data.get('silent', False)
        self.bot = Bot(token=TOKEN)
        self._log = Logger(fh, 'ProgramRemind')

    async def call(self):
        text, analytics_file, analytics_path = self._get_data()
        await self.bot.sendMessage(
            chat_id=self.chat_id,
            text=text,
            disable_notification=self.silent
        )

    def _get_data(self):
        texts = {
            'en': 'Hey, new day, new workout😉\n'
                  'The next day of your program is already available!\n'
                  'Come on quickly💪\n\n'
                  '⬇️ Use bot menu to continue work',
            'ru': 'Хей, новый день — новая тренировка😉\n'
                  'Следующий день твоей программы уже доступен!\n'
                  'Давай скорей💪\n\n'
                  '⬇️ Используй меню бота для продолжения работы',
            'ua': 'Хей, новий день — нове тренування 😉\n'
                  'Наступний день вашої програми вже доступний!\n'
                  'Давай швидше 💪\n\n'
                  '⬇️ Для продовження роботи використовуй меню бота'
        }
        return texts[self.lang]
