from telegram import (
    constants,
    InlineKeyboardMarkup,
)

from logic.base import DefaultMessageHandler
from constants import SubscriptionValue


class InfoMenuController(DefaultMessageHandler):
    async def _call(self):
        if not self._update.message:
            await self.callback_query.answer()

        text, buttons = self._get_data()
        if (self.callback_query and
                not self.callback_query.message.document and
                not self.callback_query.message.video):
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
        else:
            try:
                await self.callback_query.delete_message()
            finally:
                await self._context.bot.sendMessage(
                    chat_id=self.chat_id,
                    text=text,
                    reply_markup=buttons,
                    disable_notification=self.silent
                )

    def _get_data(self):
        texts = {
            'en': 'ℹ️ Info:',
            'ru': 'ℹ️ Информация:',
            'ua': 'ℹ️ Інформація:',
        }

        buttons = [{
            'text': {
                'en': 'Manual',
                'ru': 'Инструкция',
                'ua': 'Інструкція',
            },
            'callback_data': 'manual'
        }, {
            'text': {
                'en': 'Feedback',
                'ru': 'Обратная связь',
                'ua': "Зворотній зв'язок",
            },
            'callback_data': 'feedback'
        }, {
            'text': {
                'en': 'Terms of use',
                'ru': 'Условия использования',
                'ua': "Умови використання",
            },
            'callback_data': 'oferta'
        }, {
            'text': {
                'en': 'Help',
                'ru': 'Помощь',
                'ua': "Допомога",
            },
            'callback_data': 'help'
        }]

        buttons = [{'name': button['text'][self.lang],
                    'callback_data': button['callback_data']} for button in buttons]
        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('menu'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'info' == callback_data


class InfoManualController(DefaultMessageHandler):
    async def _call(self):
        if not self._update.message:
            await self.callback_query.answer()

        text, buttons, media = self._get_data()
        try:
            await self.callback_query.delete_message()
        finally:
            await self._context.bot.sendVideo(
                chat_id=self.chat_id,
                video=media,
                width=886,
                height=1920,
                caption=text,
                reply_markup=buttons,
                disable_notification=self.silent
            )
            if not self._update.message:
                self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        texts = {
            'en': 'ℹ️ Info | Manual:\n'
                  'A short video of how to use me correctly.\n'
                  'If you have any questions, all contact information in the "Feedback" section',
            'ru': 'ℹ️ Информация | Инструкция:\n'
                  'Короткое видео о том, как правильно пользоваться мной.\n'
                  'Если есть вопросы, вся контактная информация в разделе "Обратная связь"',
            'ua': 'ℹ️ Інформація | Інструкція:\n'
                  'Коротке відео про те, як правильно користуватись мною.\n'
                  'Якщо є питання, вся контактна інформація у розділі "Зворотній зв\'язок"',
        }

        with open(self._static_path + 'static/info/manual.MOV', 'rb') as f:
            media = f.read()

        buttons = self.attach_back_button('info')
        return texts[self.lang], InlineKeyboardMarkup(buttons), media

    @staticmethod
    def pattern(callback_data):
        return 'manual' == callback_data


class FeedbackController(DefaultMessageHandler):
    async def _call(self):
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
        self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        texts = {
            'en': 'ℹ️ Info | Feedback:\n'
                  'Feel free to ask any connected with bot question❓or offer your ideas💡\n'
                  '🦾Main developer: @prosto_vania\n'
                  '👑The main: @fitness_feel\n'
                  '📨Email: gymbuddybot@gmail.com\n',
            'ru': 'ℹ️ Информация | Обратная связь:\n'
                  'Не стесняйтесь задавать любые вопросы❓, связанные с ботом, или предлагать ваши идеи💡\n'
                  '🦾Главный разработчик: @prosto_vania\n'
                  '👑Самый главный: @fitness_feel\n'
                  '📨Электронная почта: gymbuddybot@gmail.com\n',
            'ua': "ℹ️ Інформація | Зворотній зв'язок:\n"
                  "Не соромся задавати будь-які запитання❓(одразу скажу, я не знаю як винищити усю русню ... покищо), "
                  "або пропонувати ваші ідеї💡\n"
                  "🦾Розробник: @prosto_vania\n"
                  '👑Гетман: @prosto_vania\n'
                  "📨Електронна адреса: gymbuddybot@gmail.com\n",
        }

        buttons = self.attach_back_button('info')
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'feedback' == callback_data


class OfertaController(DefaultMessageHandler):
    async def _call(self):
        await self.callback_query.answer()

        text, media, buttons = self._get_data()
        try:
            await self.callback_query.delete_message()
        finally:
            await self._context.bot.sendDocument(
                chat_id=self.chat_id,
                document=media,
                filename='terms_of_use.pdf',
                caption=text,
                reply_markup=buttons,
                disable_notification=self.silent
            )
            if not self._update.message:
                self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        texts = {
            'en': 'ℹ️ Info | Terms of use:\n\n'
                  'Individual entrepreneur "КАЛІШУК І.О."\n\n'
                  'Contacts:\n'
                  'Email: kalishukivan@gmail.com\n'
                  'Telephone: +380991611727\n\n'
                  'If you have any questions connected with bot functionality, '
                  'all developer contact information in the "Feedback" section',
            'ru': 'ℹ️ Информация | Условия использования:\n\n'
                  'ФЛП "КАЛІШУК І.О."\n\n'
                  'Контакты:\n'
                  'Email: kalishukivan@gmail.com\n'
                  'Телефон: +380991611727\n\n'
                  'Если есть вопросы связанные с функциональностью бота, '
                  'вся контактная информация в разделе "Обратная связь"',
            'ua': "ℹ️ Інформація | Умови використання:\n\n"
                  'ФОП "КАЛІШУК І.О."\n\n'
                  'Contacts:\n'
                  'Email: kalishukivan@gmail.com\n'
                  'Телефон: +380991611727\n\n'
                  'Якщо є питання пов\'язаны з ботом, '
                  'вся контактна інформація у розділі "Зворотній зв\'язок"',
        }

        with open(self._static_path + 'static/info/oferta.pdf', 'rb') as f:
            media = f.read()

        buttons = self.attach_back_button('info')
        return texts[self.lang], media, InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'oferta' == callback_data


class HelpController(DefaultMessageHandler):
    async def _call(self):
        if not self._update.message:
            await self.callback_query.answer()

        text, buttons = self._get_data()

        if not self._update.message:
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
        else:
            try:
                await self.callback_query.delete_message()
            finally:
                await self._context.bot.sendMessage(
                    chat_id=self.chat_id,
                    text=text,
                    reply_markup=buttons,
                    disable_notification=self.silent
                )

    def _get_data(self):
        texts = {
            'en': 'ℹ️ Info | Help:\n'
                  'GymBro for every gym lover💪\n'
                  '🧠 Functionality: \n'
                  ' • Records of workouts\n'
                  ' • Calculator kcal.\n'
                  ' • Videos and descriptions of exercises\n'
                  ' • Progress analytics\n'
                  ' • Access to training programs\n\n'
                  'All you need for gym in one place!',
            'ru': 'ℹ️ Информация | Помощь:\n'
                  'GymBro для каждого любителя спортзала💪\n'
                  '🧠Функции:\n'
                  ' • Учёт тренировок\n'
                  ' • Калькулятор ккал.\n'
                  ' • Видео и описания упражнений\n'
                  ' • Аналитика прогресса\n'
                  ' • Доступ к программам тренировок\n\n'
                  'Все что нужно для фитнеса в одном месте!',
            'ua': "ℹ️ Інформація | Допомога:\n"
                  'GymBro для кожного любителя тренажерного залу💪\n'
                  '🧠 Функціональні можливості:\n'
                  ' • Облік тренувань\n'
                  ' • Калькулятор ккал.\n'
                  ' • Відео та описи вправ\n'
                  ' • Аналітика прогресу\n'
                  ' • Доступ до програм тренувань\n\n'
                  'Все, що вам потрібно для тренажерного залу в одному місці!',
        }

        buttons = self.attach_back_button('info')
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'help' == callback_data


class GuideController(DefaultMessageHandler):
    check_subscription = True
    needed_subscription_value = SubscriptionValue.Medium

    async def _call(self):
        await self.callback_query.answer()

        text, buttons, file = self._get_data()

        try:
            await self.callback_query.delete_message()
        finally:
            await self.bot.sendDocument(
                chat_id=self.chat_id,
                document=file,
                filename='boss_of_the_gym.pdf',
                caption=text,
                disable_notification=self.silent,
                parse_mode=constants.ParseMode.HTML
            )

            menu_text = {
                'en': 'Menu:',
                'ru': 'Меню:',
                'ua': 'Меню:'
            }
            menu_buttons = self.build_menu(self._menu_buttons[self.lang])
            await self._context.bot.sendMessage(
                chat_id=self.chat_id,
                text=menu_text[self.lang],
                reply_markup=menu_buttons,
                disable_notification=self.silent
            )
        self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        texts = {
            'en': '🧠 Guide\n\n'
                  ' • The guide includes the main structured information about nutrition and training to build the shape of your dreams!\n'
                  ' • Watch the <a href="https://youtu.be/kSYXXmJ0BfE">lecture</a> in parallel with the guide.\n'
                  '<b><u>IT IS NECESSARY.</u></b>\n'
                  ' • The lecture explains in detail each point, aspect of the guide and contains detailed answers to the main questions\n'
                  ' • This format was specially chosen for better assimilation of the material.\n'
                  'Enjoy watching✌️',
            'ru': '🧠 Гайд + лекция\n\n'
                  ' • Гайд включает в себя главную структурированную информацию о питании и тренировках для построения формы твоей мечты!\n'
                  ' • Просматривайте <a href="https://youtu.be/kSYXXmJ0BfE">лекцию</a> параллельно с гайдом.\n'
                  '<b><u>ЭТО ОБЯЗАТЕЛЬНО.</u></b>\n'
                  ' • Лекция детально обьясняет каждый пункт, аспект гайда и содержит развернутые ответы на основные вопросы\n'
                  ' • Специально выбран такой формат, для лучшего усвоения материала.\n'
                  'Приятного просмотра✌️',
            'ua': '🧠 Гайд + лекція\n\n'
                  " • Гайд включає головну структуровану інформацію про харчування та тренування для побудови форми твоєї мрії!\n"
                  ' • Переглядайте <a href="https://youtu.be/kSYXXmJ0BfE">лекцію</a> паралельно із гайдом.\n'
                  "<b><u>ЦЕ ОБОВ'ЯЗКОВО.</u></b>\n"
                  ' • Лекція детально пояснює кожен пункт, аспект гайду та містить розгорнуті відповіді на основні питання\n'
                  ' • Спеціально вибрано такий формат для кращого засвоєння матеріалу.\n'
                  "Приємного перегляду✌️",
        }

        with open(self._static_path + 'static/guide.pdf', 'rb') as f:
            file = f.read()

        buttons = self.attach_back_button('menu')
        return texts[self.lang], InlineKeyboardMarkup(buttons), file

    @staticmethod
    def pattern(callback_data):
        return 'guide' == callback_data
