from telegram import (
    InlineKeyboardMarkup,
)

from config import (
    LAST_TRAININGS_NUM,
)
from constants import (
    SubscriptionValue,
    DATE_FORMAT
)
from models import (
    Set,
    Training
)
from logic.base import DefaultMessageHandler
from tasks.src.main import send_analytics


class AnalyticsMenuController(DefaultMessageHandler):
    check_subscription = True
    needed_subscription_value = SubscriptionValue.Medium

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
            'en': '📈Analytics:',
            'ru': '📈Аналитика:',
            'ua': "📈Аналітика:",
        }
        periods = [
            {'name': {'en': 'My trainings',
                      'ru': 'Мои тренировки',
                      'ua': 'Мої тренування'},
             "callback_data": 'my_trainings'},
            {'name': {'en': '1 month',
                      'ru': '1 месяц',
                      'ua': '1 місяць'},
             "callback_data": {'analytics': True,
                               'period': '1'}},
            {'name': {'en': '3 month',
                      'ru': '3 месяца',
                      'ua': '3 місяці'},
             "callback_data": {'analytics': True,
                               'period': '3'}},
            {'name': {'en': 'All time',
                      'ru': 'Всё время',
                      'ua': 'Весь час'},
             "callback_data": {'analytics': True,
                               'period': '-1'}},
        ]
        buttons = [{'name': period['name'][self.lang],
                    'callback_data': period['callback_data']} for period in periods]
        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('menu'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'analytics' == callback_data


class AnalyticsGeneratorController(DefaultMessageHandler):
    check_subscription = True
    needed_subscription_value = SubscriptionValue.Medium

    async def _call(self):
        await self.callback_query.answer()
        chat_id = self.chat_id
        if (Training
                .select()
                .where(Training.user == self.user)
                .exists()):
            try:
                await self.callback_query.delete_message()
            finally:
                texts = {
                    'en': 'Your analytics is being formed. It can take some time ⏳',
                    'ru': 'Твоя аналитика формируется. Это может занять некоторое время ⏳',
                    'ua': 'Твоя аналітика формується. Це може зайняти деякий час ⏳'
                }
                await self._context.bot.sendMessage(
                    chat_id=chat_id,
                    text=texts[self.lang],
                    disable_notification=self.silent
                )
        send_analytics.apply_async(args=[self.user.id, self.callback_query.data['period']])
        self._context.drop_callback_data(self.callback_query)

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return callback_data.get('analytics', False)
        return False


class MyTrainingsController(DefaultMessageHandler):
    check_subscription = True
    needed_subscription_value = SubscriptionValue.Medium

    async def _call(self):
        await self.callback_query.answer()

        text, buttons = await self._get_data()
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

    async def _get_data(self):
        buttons = self.attach_back_button('analytics')
        headers = {
            'en': '📈Analytics | My trainings:\n',
            'ru': '📈Аналитика | Мои тренировки:\n',
            'ua': "📈Аналітика | Мої тренування:\n",
        }

        trainings = (Training
                     .select()
                     .where(Training.user == self.user,
                            Training.end.is_null(False))
                     .order_by(Training.id.desc(),
                               Training.created.desc())
                     .limit(LAST_TRAININGS_NUM))

        if not trainings.count():
            texts = {
                'en': "\nYou haven't had any training yet. \nIt's time to fix it 💪",
                'ru': '\nУ тебя пока не было тренировок. \nПора это исправить 💪',
                'ua': "\nКамон, в тебе ще не було тренувань. \nЧас це виправити 💪",
            }
        else:
            trainings_text = await self._get_sets_data(trainings)
            texts = {
                'en': f'Your last trainings: \n {trainings_text}',
                'ru': f'Твои последние тренировки: \n {trainings_text}',
                'ua': f'Твої останні тренування: \n {trainings_text}',
            }

        return headers[self.lang] + texts[self.lang], InlineKeyboardMarkup(buttons)

    async def _get_sets_data(self, trainings):
        text = ''
        for training in trainings:
            text += f'\n📅 {training.created.strftime(DATE_FORMAT)} 📅\n'
            for s in (Set
                    .select()
                    .where(Set.training == training)
                    .order_by(Set.created)):
                exercise = s.exercise
                tool = exercise.tool
                group = exercise.group
                text += f'\t • {group.get_name(self.lang)} | ' \
                        f'{tool.get_name(self.lang)} | ' \
                        f'{exercise.get_name(self.lang)}\n'
        return text

    @staticmethod
    def pattern(callback_data):
        return 'my_trainings' == callback_data
