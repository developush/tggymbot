import re
import typing
import traceback

from datetime import datetime, timedelta
import telegram.constants
from telegram import (
    Bot,
    BotCommand,
    CallbackQuery,
    Chat,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    User as TGUser,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

from config import (
    DEFAULT_LANGUAGE,
    MAIN_PATH
)
from constants import Languages, USER_LANGUAGES
from models import User, db_connect_wrapper
from utils import logger


class DefaultMessageHandler:
    check_subscription = False
    needed_subscription_value = 0

    def __init__(self, app: 'Application'):
        self._app = app
        self._update = None
        self._context = None
        self._user = None
        self._user_created = False
        self._log = logger
        self._static_path = MAIN_PATH
        self._last_chat_id = None
        self._menu_buttons = {
            'ru': [{'name': '💪Упражнения', 'callback_data': 'start_training'},
                   {'name': '🧮Калькулятор', 'callback_data': 'calculator'},
                   {'name': '✍️Программы', 'callback_data': 'programs'},
                   {'name': '🧠Гайд', 'callback_data': 'guide'},
                   {'name': '📈Аналитика', 'callback_data': 'analytics'},
                   {'name': 'ℹ️Информация', 'callback_data': 'info'},
                   {'name': '⚙️Настройки', 'callback_data': 'settings'},
                   {'name': '💰Подписка', 'callback_data': 'subscription'}],
            'ua': [{'name': '💪Вправи', 'callback_data': 'start_training'},
                   {'name': '🧮Калькулятор', 'callback_data': 'calculator'},
                   {'name': '✍️Програми', 'callback_data': 'programs'},
                   {'name': '🧠Гайд', 'callback_data': 'guide'},
                   {'name': '📈Аналітика', 'callback_data': 'analytics'},
                   {'name': 'ℹ️Інформація', 'callback_data': 'info'},
                   {'name': '⚙️Налаштування', 'callback_data': 'settings'},
                   {'name': '💰Передплата', 'callback_data': 'subscription'}],
            'en': [{'name': '💪Workout', 'callback_data': 'start_training'},
                   {'name': '🧮Calculator', 'callback_data': 'calculator'},
                   {'name': '✍️Programs', 'callback_data': 'programs'},
                   {'name': '🧠Guide', 'callback_data': 'guide'},
                   {'name': '📈Analytics', 'callback_data': 'analytics'},
                   {'name': 'ℹ️Info', 'callback_data': 'info'},
                   {'name': '⚙️Settings', 'callback_data': 'settings'},
                   {'name': '💰Subscription', 'callback_data': 'subscription'}],
        }

    @property
    def bot(self) -> 'Bot':
        return self._app.bot

    @property
    def from_user(self) -> 'TGUser':
        if self._update.message:
            return self._update.message.from_user
        if self._update.callback_query:
            return self._update.callback_query.from_user

    @property
    def user(self) -> 'User':
        if (self._user is None or
                self._last_chat_id is None or
                self._last_chat_id != self.chat_id):
            self._user = User.get_or_none(
                chat_id=self.chat_id,
            )
            self._user_created = False
            if self._user is None:
                self.create_user()
            self._last_chat_id = self.chat_id
        return self._user

    def _clear_user(self):
        self._user = None

    @property
    def gender(self) -> str:
        return self.user.extra_data.get('gender', 'male')

    @property
    def chat(self) -> typing.Union[None, Chat]:
        if self._update.message:
            return self._update.message.chat
        if self._update.edited_message:
            return self._update.edited_message.chat

    @property
    def chat_id(self) -> int:
        if self.chat:
            return self.chat.id
        if self.callback_query.message:
            return self.callback_query.message.chat_id

    @property
    def callback_query(self) -> 'CallbackQuery':
        return self._update.callback_query

    @property
    def lang(self) -> str:
        if self.user is not None:
            return USER_LANGUAGES.get(self.user.id, self.user.lang)
        lang = self.from_user.language_code
        if lang not in Languages.all():
            lang = DEFAULT_LANGUAGE
        return lang

    @property
    def silent(self):
        return self.user.extra_data.get('silent', False)

    def _setter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._update = update
        self._context = context

    def build_menu(self, buttons, buttons_in_row=2, raw=False) -> typing.Union[InlineKeyboardMarkup, list]:
        markup = []
        new_row = []
        for button in buttons:
            new_row.append(InlineKeyboardButton(button['name'],
                                                callback_data=button['callback_data']))
            if len(new_row) == buttons_in_row:
                markup.append(new_row)
                new_row = []
        if new_row:
            markup.append(new_row)
        if raw:
            return markup

        return InlineKeyboardMarkup(markup)

    def create_user(self):
        lang = self.from_user.language_code
        if lang not in Languages.all():
            lang = DEFAULT_LANGUAGE
        self._user, self._user_created = User.get_or_create(
            chat_id=self.chat_id,
            defaults=dict(
                name=' '.join([self.from_user.first_name or '',
                               self.from_user.last_name or '']),
                tg_account=self.from_user.username,
                lang=lang,
                subscription_end=datetime.now() + timedelta(days=7),
            )
        )

    def save_interaction(self):
        if self._user is not None:
            self._user.last_interacted = datetime.now()
            self._user.save(only=[User.last_interacted])

    @db_connect_wrapper
    async def call(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            self._setter(update, context)
            self._clear_user()
            self.save_interaction()
            if self.check_subscription:
                if not self.is_subscription_active():
                    return await self.subscription_end()
                elif not self.is_valid_subscription():
                    return await self.not_valid_subscription()
            return await self._call()
        except:
            self._log.error(traceback.format_exc())

    async def _call(self):
        raise NotImplementedError

    async def set_bot_menu_buttons(self):
        commands = {
            'en': [{'command': 'start', 'text': 'Start Bot'},
                   {'command': 'menu', 'text': 'Show menu'},
                   {'command': 'end_training', 'text': 'End training'},
                   {'command': 'show_analytics', 'text': 'Show your progress'},
                   {'command': 'info', 'text': 'Info'},
                   {'command': 'settings', 'text': 'Settings'},
                   {'command': 'help', 'text': 'Help'}],
            'ru': [{'command': 'start', 'text': 'Старт'},
                   {'command': 'menu', 'text': 'Меню'},
                   {'command': 'end_training', 'text': 'Закончить тренировку'},
                   {'command': 'show_analytics', 'text': 'Аналитика'},
                   {'command': 'info', 'text': 'Информация'},
                   {'command': 'settings', 'text': 'Настройки'},
                   {'command': 'help', 'text': 'Помощь'}],
            'ua': [{'command': 'start', 'text': 'Початок бота'},
                   {'command': 'menu', 'text': 'Показати меню'},
                   {'command': 'end_training', 'text': 'Закінчити тренування'},
                   {'command': 'show_analytics', 'text': 'Показати твій прогрес'},
                   {'command': 'info', 'text': 'Info'},
                   {'command': 'settings', 'text': 'Налаштування'},
                   {'command': 'help', 'text': 'Допомога'}],

        }
        commands = [BotCommand(c['command'], c['text']) for c in commands['en']]
        await self.bot.set_my_commands(commands=commands,
                                       language_code=self.lang)

    def attach_back_button(self, callback_data, names=None):
        if names is None:
            names = {}
        back_buttons = {'ru': [{'name': names.get('ru', '👈 Назад'), 'callback_data': callback_data}],
                        'en': [{'name': names.get('ru', '👈 Back'), 'callback_data': callback_data}],
                        'ua': [{'name': names.get('ua', '👈 Назад'), 'callback_data': callback_data}]}
        back_buttons = self.build_menu(back_buttons[self.lang], buttons_in_row=1, raw=True)
        return back_buttons

    def is_subscription_active(self):
        user = User.get_or_none(chat_id=self.chat_id)
        return user is None or user.subscription_end >= datetime.now()

    async def subscription_end(self):
        if self.callback_query:
            await self.callback_query.answer()

        text, buttons = self._get_subscription_end_data()
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

    def _get_subscription_end_data(self):
        texts = {
            'en': 'Your subscription has ended 😩\n'
                  'To continue using the bot, renew your subscription in the menu "💰Subscription"',
            'ru': 'Ваша подписка закончилась 😩\n'
                  'Чтобы продолжить пользоваться ботом продлите вашу подписку в меню "💰Подписка"',
            'ua': 'Ваша передплата закінчилась 😩\n'
                  'Щоб продовжити користуватися ботом продовжіть вашу передплату в меню "💰Передплата"'
        }
        buttons = self.build_menu(self._menu_buttons[self.lang])
        return texts[self.lang], buttons

    def is_valid_subscription(self):
        if self.user.subscription:
            return self.user.subscription.value >= self.needed_subscription_value
        return not self.needed_subscription_value

    async def not_valid_subscription(self):
        if self.callback_query:
            await self.callback_query.answer()

        text, buttons = self._get_not_valid_subscription_level_data()
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

    def _get_not_valid_subscription_level_data(self):
        texts = {
            'en': 'This functionality is not included in your subscription😢\n'
                  'To get access here, you can get the appropriate subscription level in the menu "💰Subscription"',
            'ru': 'Данный функционал не входит в твою подписку😢\n'
                  'Чтобы получить сюда доcтуп, можешь оформить подходящий уровень подписки в меню "💰Подписка"',
            'ua': 'Даний функціонал не входить до твоєї підписки😢\n'
                  'Щоб отримати сюди доcтуп, можеш оформити відповідний рівень підписки в меню "💰Підписка"'
        }
        buttons = self.build_menu(self._menu_buttons[self.lang])
        return texts[self.lang], buttons


class Registration(DefaultMessageHandler):
    GENDER, AGE, BODY_PARAMS, GOALS, MENU = range(5)

    Genders = {
        'ru': [["Мужчина"], ["Женщина"]],
        'en': [["Man"], ["Woman"]],
        'ua': [["Чоловік"], ["Жінка"]]
    }
    Goals = {
        'ru': [["Набор мышечной массы"], ["Похудение"], ["Поддержание формы"]],
        'en': [["Muscle mass gain"], ["Weight loss"], ["Keeping fit"]],
        'ua': [["Набір м'язової маси"], ["Схуднення"], ["Підтримка форми"]]
    }

    GenderRegEx = f"^({'|'.join(['|'.join([i[0][0], i[1][0]]) for i in Genders.values()])})$"
    GoalsRegEx = f"^({'|'.join(['|'.join([i[0][0], i[1][0], i[2][0]]) for i in Goals.values()])})$"
    AgeRegEx = r'\d+.*'
    BodyParamsRegEx = r'.*?\d+\.?\d+.*?\d+\.?\d+'

    async def start(self) -> typing.Union[None, int]:
        self.create_user()
        if self._user_created:
            texts = {
                'ru': f'Привет, я буду твоим партнёром в зале 💪. \n'
                      f'Итак начнём, это меню управления. Здесь ты можешь:'
                      '\n• Начать новую тренировку'
                      '\n• Получить аналитику твоего прогресса'
                      '\n• Просчитать свою норму ккал.'
                      '\n• Получить полезную информацию',
                'en': f"Hi, I'll be your partner in the gym 💪. \n"
                      f"So let's start, this is the control menu. Here you can:"
                      '\n• Start new workout'
                      '\n• Get analytics of your progress'
                      '\n• Calculate your norm kcal.'
                      '\n• Get useful information',
                'ua': f'Привіт, я буду твоїм партнером у залі 💪. \n'
                      f'Отже почнемо, це меню куревання. Тут ти можеш:'
                      '\n• Розпочати нове тренування'
                      '\n• Отримати аналітику твого прогресу'
                      '\n• Прорахувати свою норму ккал.'
                      '\n• Отримати корисну інформацію',
            }
            await self._update.message.reply_text(
                texts[self.lang],
            )

        # await self.set_bot_menu_buttons()
        await self.bot_menu()
        return self.MENU

    def set_start(self):
        self._call = self.start
        return self

    async def age(self) -> int:
        texts = {
            'ru': f'Супер, теперь скажи пожалуйста сколько тебе лет. '
                  f'Если хочешь держать в секрете 🤫, то просто нажми на /skip',
            'en': f'Great, now tell me please how old are you. '
                  f'If you want to keep a secret 🤫, then just click on /skip',
            'ua': f"Супер, тепер скажи, будь ласка, скільки тобі років. "
                  f"Якщо хочеш тримати в секреті 🤫, то просто натисніть на /skip",
        }

        self._save_gender()
        await self._update.message.reply_text(
            texts[self.lang],
            reply_markup=ReplyKeyboardRemove(),
        )
        return self.BODY_PARAMS

    def _save_gender(self):
        genders = self.Genders[self.lang]
        selected_gender = self._update.message.text
        if not selected_gender:
            return
        for index, gender in enumerate(genders):
            if gender[0] == selected_gender:
                if index == 0:
                    self.user.extra_data['gender'] = 'male'
                else:
                    self.user.extra_data['gender'] = 'female'
                self.user.save()

    def set_age(self):
        self._call = self.age
        return self

    async def skip_age(self) -> int:
        texts = {
            'ru': f'Ладно, значит будем секретничать 🤐. \nНу, а про рост и вес расскажешь? '
                  f'Чтобы я мог корректно давать советы, если не хочешь нажми на /skip. \n'
                  '❗️Формат ввода: 185 75 ❗️',
            'en': f"Okay, so let's keep it secret 🤐. \nSo, what about height and weight? "
                  f"So that I can correctly give advice, if you do not want to click on /skip. \n"
                  f"❗️Input format: 185 75 ❗️",
            'ua': f"Гаразд, тоді триматимемо це у секреті 🤐. \nНу, а про зріст і вагу розкажеш? "
                  f"Щоб я міг коректно давати поради, якщо не хочеш натисни на /skip. \n"
                  f"❗Формат введення: 185 75 ❗",
        }

        await self._update.message.reply_text(
            texts[self.lang]
        )
        return self.GOALS

    def set_skip_age(self):
        self._call = self.skip_age
        return self

    async def body_params(self) -> int:
        texts = {
            'ru': f'А про рост и вес расскажешь? \n'
                  f'Это нужно чтобы я мог корректно давать советы, если не хочешь нажми на /skip. \n'
                  '❗️Формат ввода: 185 75❗️',
            'ua': f"Ну, а про зріст і вагу розкажеш? \n"
                  f"Це потрібно щоб я міг коректно давати поради, якщо не хочеш натисни на /skip. \n"
                  f"❗️Формат введення: 185 75❗️",
            'en': f"So, what about height and weight? \n"
                  f"So that I can correctly give advice, if you do not want to click on /skip. \n"
                  f"❗️Input format: 185 75❗️"
        }
        self._save_age()
        await self._update.message.reply_text(
            texts[self.lang],
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=telegram.constants.ParseMode.MARKDOWN
        )
        return self.GOALS

    def _save_age(self):
        params = re.findall(r'\d+(?:[.,]\d+)?', self._update.message.text)
        if len(params) == 1:
            self.user.extra_data['age'] = params[0]
            self.user.save()

    def set_body_params(self):
        self._call = self.body_params
        return self

    def set_skip_body_params(self):
        self._call = self.goals
        return self

    async def goals(self) -> int:
        texts = {
            'ru': f"А теперь последнее, но не менее важное. Выбери с какой целью ты занимаешься?",
            'ua': f"А тепер останнє, але не менш важливе. Вибери, з якою метою ти займаєшся?",
            'en': f"And now, last but not least, choose for what purpose do you go to the gym?"
        }

        self._save_body_params()
        await self._update.message.reply_text(
            texts[self.lang],
            reply_markup=ReplyKeyboardMarkup(
                self.Goals[self.lang],
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
        )
        return self.MENU

    def _save_body_params(self):
        params = re.findall(r'\d+(?:[.,]\d+)?', self._update.message.text)
        if len(params) == 2:
            self.user.extra_data['height'] = params[0]
            self.user.extra_data['weight'] = params[1]
            self.user.save()

    def set_goals(self):
        self._call = self.goals
        return self

    async def bot_menu(self) -> None:
        texts = {
            'ru': 'Регистрация закончена, ты молодец! Итак начнём, это меню управления. Здесь ты можешь:'
                  '\n• Начать новую тренировку'
                  '\n• Получить аналитику твоего прогресса'
                  '\n• Получить полезную информацию',
            'en': "Registration is over, well done! So let's start, this is the control menu. Here you can:"
                  "\n• Start a new workout"
                  "\n• Get analytics of your progress"
                  "\n• Get useful information",
            'ua': "Реєстрація закінчена, ти молодець! Отже почнемо, це меню керування. Тут ти можеш:"
                  "\n• Почати нове тренування"
                  "\n• Здобути аналітику твого прогресу"
                  "\n• Отримати корисну інформацію",
        }
        menu_texts = {
            'ru': 'Меню управления:',
            'en': "Control menu:",
            'ua': "Меню керування:",
        }
        if self._update.message:
            if self._update.message.text not in ['/menu', '/start']:
                self._save_goals()
                try:
                    await self._update.message.reply_text(
                        text=texts[self.lang],
                        reply_markup=ReplyKeyboardRemove(),
                    )
                finally:
                    await self._update.message.reply_text(
                        text=menu_texts[self.lang],
                        reply_markup=self.build_menu(self._menu_buttons[self.lang]),
                    )
            else:
                await self._update.message.reply_text(
                    text=menu_texts[self.lang],
                    reply_markup=self.build_menu(self._menu_buttons[self.lang]),
                )
        elif self.callback_query:
            await self.callback_query.answer()
            await self.callback_query.edit_message_text(
                text=menu_texts[self.lang],
                reply_markup=self.build_menu(self._menu_buttons[self.lang]),
            )
            self._context.drop_callback_data(self.callback_query)

    def _save_goals(self):
        goals = self.Goals[self.lang]
        selected_goal = self._update.message.text
        if not selected_goal:
            return
        for index, goal in enumerate(goals):
            if goal[0] == selected_goal:
                if index == 0:
                    goal = 'mass_gain'
                elif index == 1:
                    goal = 'weight_loss'
                else:
                    goal = 'keeping_feet'
                self.user.extra_data['goal'] = goal
                self.user.save()
                return

    def set_bot_menu(self):
        self._call = self.bot_menu
        return self


def get_start_handler(app: 'Application'):
    return ConversationHandler(
        entry_points=[CommandHandler("start",
                                     Registration(app).set_start().call)],
        states={
            Registration(app).AGE: [MessageHandler(filters.Regex(Registration(app).GenderRegEx),
                                                   Registration(app).set_age().call)],

            Registration(app).BODY_PARAMS: [MessageHandler(filters.Regex(Registration(app).AgeRegEx),
                                                           Registration(app).set_body_params().call),
                                            CommandHandler("skip",
                                                           Registration(app).set_skip_age().call)],

            Registration(app).GOALS: [MessageHandler(filters.Regex(Registration(app).BodyParamsRegEx),
                                                     Registration(app).set_goals().call),
                                      CommandHandler("skip",
                                                     Registration(app).set_skip_body_params().call)],

            Registration(app).MENU: [MessageHandler(filters.Regex(Registration(app).GoalsRegEx),
                                                    Registration(app).set_bot_menu().call)]

        },
        fallbacks=[CommandHandler("cancel",
                                  Registration(app).set_bot_menu().call)],
    )
