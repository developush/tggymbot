from telegram import (
    InlineKeyboardMarkup,
)

from constants import Languages, BOOLS, USER_LANGUAGES
from models import User
from logic.base import DefaultMessageHandler


class SettingsController(DefaultMessageHandler):
    async def _call(self):
        if not self._update.message:
            await self.callback_query.answer()

        text, buttons = self._get_data()
        try:
            await self.callback_query.edit_message_text(
                text=text,
                reply_markup=buttons,
            )
        except:
            await self._context.bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                reply_markup=buttons,
                disable_notification=self.silent
            )
        if not self._update.message:
            self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        texts = {
            'en': '⚙️Settings:',
            'ru': '⚙️Настройки:',
            'ua': '⚙️Налаштування:',
        }
        lang_name = Languages.Names[self.lang][self.lang]
        notif_name = BOOLS[not(self.user.extra_data.get('silent', False))][self.lang]
        buttons = {
            'lang': {
                'text': {
                    'en': f'Language: {lang_name}',
                    'ru': f'Язык: {lang_name}',
                    'ua': f'Мова: {lang_name}',
                },
                'callback_data': 'change_language'
            },
            'notifications': {
                'text': {
                    'en': f'Notification sound: {notif_name}',
                    'ru': f'Звук уведомлений: {notif_name}',
                    'ua': f'Звук повідомлень: {notif_name}',
                },
                'callback_data': 'change_notifications'
            },
        }

        buttons = [{'name': buttons[key]['text'][self.lang],
                    'callback_data': buttons[key]['callback_data']} for key in buttons.keys()]
        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('menu'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'settings' == callback_data


class NotificationsController(SettingsController):
    async def _call(self):
        await self.callback_query.answer()

        await self.update_settings()
        text, buttons = self._get_data()
        try:
            await self.callback_query.edit_message_text(
                text=text,
                reply_markup=buttons,
            )
        except:
            await self._context.bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                reply_markup=buttons,
                disable_notification=self.silent
            )

        self._context.drop_callback_data(self.callback_query)

    async def update_settings(self):
        user = User.get_by_id(self.user.id)
        user.extra_data['silent'] = not user.extra_data.get('silent', False)
        user.save()
        self._user = user

    @staticmethod
    def pattern(callback_data):
        return 'change_notifications' == callback_data


class LanguageController(NotificationsController):
    async def update_settings(self):
        pass

    def _get_data(self):
        texts = {
            'en': '⚙️Settings | Language:',
            'ru': '⚙️Настройки | Язык:',
            'ua': '⚙️Налаштування | Мова:',
        }

        buttons = [{'name': Languages.Names[key][self.lang],
                    'callback_data': {'set_lang': key}} for key in Languages.all()]
        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('settings'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'change_language' == callback_data


class LanguageSetterController(LanguageController):
    async def update_settings(self):
        user = User.get_by_id(self.user.id)
        user.lang = self.callback_query.data['set_lang']
        user.save()
        self._user = user
        USER_LANGUAGES[user.id] = user.lang

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return callback_data.get('set_lang')
        return False
