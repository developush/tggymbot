from peewee import fn
from telegram import (
    constants as tg_constants,
    InlineKeyboardMarkup
)
from datetime import datetime, timedelta

from constants import SubscriptionValue
from models import (
    ProgramGroup,
    ProgramLevel,
    Program,
    Exercise
)
from logic.base import DefaultMessageHandler


class ProgramGroupController(DefaultMessageHandler):
    check_subscription = True
    needed_subscription_value = SubscriptionValue.Medium

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
            'en': '✍️ Training Programs\nChoose suitable frequency:',
            'ru': '✍️ Программы тренировок\nВыбери подходящую частоту:',
            'ua': '✍️ Програми тренувань\nОбери відповідну частоту:',
        }

        buttons = [{'name': p.name[self.lang],
                    'callback_data': {'programs': True,
                                      'program_group': p.id}} for p in (ProgramGroup
                                                                        .select()
                                                                        .order_by(ProgramGroup.order,
                                                                                  ProgramGroup.id))]
        program = self.user.program
        if program:
            my_trainings = {
                'en': 'My program',
                'ru': 'Моя программа',
                'ua': 'Моя програма',
            }
            buttons.append({
                'name': my_trainings[self.lang],
                'callback_data': {'programs': True,
                                  'program_group': program.group.id,
                                  'program_level': program.level.id}
            })
        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('menu'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'programs' == callback_data


class ProgramLevelController(DefaultMessageHandler):
    check_subscription = True
    needed_subscription_value = SubscriptionValue.Medium

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
            'en': '✍️ Training Programs\nChoose a suitable option:',
            'ru': '✍️ Программы тренировок\nВыбери подходящий вариант:',
            'ua': '✍️ Програми тренувань\nОбери потрібний варіант:',
        }
        callback_data = self.callback_query.data
        group_id = callback_data['program_group']
        buttons = [{'name': p.name[self.lang],
                    'callback_data': {'programs': True,
                                      'program_group': group_id,
                                      'program_level': p.id}} for p in (ProgramLevel
                                                                        .select(fn.DISTINCT(ProgramLevel.id),
                                                                                ProgramLevel.name,
                                                                                ProgramLevel.order)
                                                                        .join(Program)
                                                                        .join(ProgramGroup)
                                                                        .where(ProgramGroup.id == group_id)
                                                                        .order_by(ProgramLevel.order,
                                                                                  ProgramLevel.id)
                                                                        )]
        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('programs'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return (callback_data.get('programs') and
                    callback_data.get('program_group') is not None and
                    callback_data.get('program_level') is None)
        return False


class ProgramController(DefaultMessageHandler):
    check_subscription = True
    needed_subscription_value = SubscriptionValue.Medium

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
        callback_data = self.callback_query.data
        program = Program.get(
            group_id=callback_data['program_group'],
            level_id=callback_data['program_level'],
        )
        name = program.group.name[self.lang]
        level = program.level.name[self.lang]
        texts = {
            'en': '✍️ Training Programs\n\n'
                  '{name} | {level}\n\n'
                  "⚠️You don't need to cram all training days into a calendar week from Mon to Sun!"
                  '1 microcycle of training can take 8 or even 9 days.'
                  '⚠️Focus only on the days of rest between classes and on your well-being!',
            'ru': '✍️ Программы тренировок\n\n'
                  '{name} | {level}\n\n'
                  '⚠️Вам не нужно впихивать все тренировочные дни в календарную неделю с ПН по ВС!\n'
                  '1 микроцикл тренировок может занимать 8 и даже 9 дней.\n'
                  '⚠️Ориентируйтесь только на дни отдыха между занятиями и на своё самочувствие!\n',
            'ua': '✍️ Програми тренувань\n\n'
                  '{name} | {level}\n\n'
                  '⚠️ Вам не потрібно впихати всі тренувальні дні в календарний тиждень з ПН по НД!'
                  '1 мікроцикл тренувань може тривати 8 і навіть 9 днів.'
                  '⚠️Орієнтуйтеся лише на дні відпочинку між заняттями та на своє самопочуття!',
        }
        text = texts[self.lang].format(name=name,
                                       level=level)
        if self.user.program == program:
            buttons = [
                {
                    'text': {
                        'en': '💪 Next day',
                        'ru': '💪 Следующий день',
                        'ua': '💪 Наступний день',
                    },
                    'callback_data': {'new_day': True,
                                      'program': program.id}
                },
                {
                    'text': {
                        'en': '🚫 Stop program',
                        'ru': '🚫 Закончить программу',
                        'ua': '🚫 Закінчити програму',
                    },
                    'callback_data': {'stop_program': True,
                                      'program': program.id}
                }
            ]
        else:
            buttons = [
                {
                    'text': {
                        'en': '💪 Start program',
                        'ru': '💪 Начать программу',
                        'ua': '💪 Почати програму',
                    },
                    'callback_data': {'new_day': True,
                                      'program': program.id}
                }
            ]
        buttons = [{'name': b['text'][self.lang],
                    'callback_data': b['callback_data']} for b in buttons]

        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        callback_data.pop('program_level')
        buttons.extend(self.attach_back_button(callback_data))
        return text, InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return (callback_data.get('programs') and
                    callback_data.get('program_group') is not None and
                    callback_data.get('program_level') is not None)
        return False


class StopProgramController(DefaultMessageHandler):
    check_subscription = True
    needed_subscription_value = SubscriptionValue.Medium

    async def _call(self):
        await self.callback_query.answer()

        text, buttons = self._get_data()
        try:
            await self.callback_query.edit_message_text(
                text=text,
                reply_markup=buttons,
                parse_mode=tg_constants.ParseMode.HTML
            )
        except:
            await self._context.bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                reply_markup=buttons,
                disable_notification=self.silent,
                parse_mode=tg_constants.ParseMode.HTML
            )
        self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        callback_data = self.callback_query.data
        program = Program.get_by_id(callback_data['program'])
        name = program.group.name[self.lang]
        texts = {
            'en': f'✍️ Training Programs\n\n{name}\n\n'
                  'You have completed the training program 💪\n'
                  'Looking forward to starting a new one!\n'
                  'If you do not know which program to choose next, consult in our <a href="https://t.me/+la91hUWvcas5N2Yy">Chat</a>',
            'ru': f'✍️ Программы тренировок\n\n{name}\n\n'
                  'Ты закончил программу тренировок 💪\n'
                  'С нетерпением жду, когда начнёшь новую!\n'
                  'Если не знаешь какую программу выбрать следующей, проконсультируйся в нашем <a href="https://t.me/+la91hUWvcas5N2Yy">Чате</a>',
            'ua': f'✍️ Програми тренувань\n\n{name}\n\n'
                  f'Ти закінчив програму тренувань 💪\n'
                  'З нетерпінням чекаю, коли почнеш нову!\n'
                  'Якщо не знаєш яку програму вибрати наступною, проконсультуйся у нашому <a href="https://t.me/+la91hUWvcas5N2Yy">Чаті</a>',
        }
        self.user.program = None
        if self.user.extra_data.get('days_in_row') is not None:
            self.user.extra_data.pop('days_in_row')
        self.user.extra_data['next_program_trainings'] = None
        self.user.save()

        buttons = [
            {
                'text': {
                    'en': '✍️ Trainings',
                    'ru': '✍️ Программы',
                    'ua': '✍️ Програми',
                },
                'callback_data': 'programs'
            },
            {
                'text': {
                    'en': 'Menu',
                    'ru': 'Меню',
                    'ua': 'Меню',
                },
                'callback_data': 'menu'
            }
        ]

        buttons = [{'name': b['text'][self.lang],
                    'callback_data': b['callback_data']} for b in buttons]

        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return (callback_data.get('stop_program') and
                    callback_data.get('program') is not None)
        return False


class NextDayProgramController(DefaultMessageHandler):
    check_subscription = True
    needed_subscription_value = SubscriptionValue.Medium

    async def _call(self):
        await self.callback_query.answer()

        text, buttons = self._get_data()
        try:
            await self.callback_query.edit_message_text(
                text=text,
                reply_markup=buttons,
                parse_mode=tg_constants.ParseMode.HTML,
            )
        except:
            await self._context.bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                reply_markup=buttons,
                disable_notification=self.silent,
                parse_mode=tg_constants.ParseMode.HTML
            )
        self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        callback_data = self.callback_query.data
        program = Program.get_by_id(callback_data['program'])
        description = program.description[self.lang]
        texts = {
            'en': f"✍️ Training Programs\n\n{description}\n\nToday's exercises:\n",
            'ru': f'✍️ Программы тренировок\n\n{description}\n\nСегодняшние упражнения:\n',
            'ua': f'✍️ Програми тренувань\n\n{description}\n\nСьогоднішні вправи:\n',
        }

        text = texts[self.lang]
        if self.user.program is not None and self.user.program != program:
            name = program.group.name[self.lang]
            level = program.level.name[self.lang]

            texts = {
                'en': '✍️ Training Programs\n\n'
                      'You already have an active training program:\n\n'
                      f'{name} | {level}\n\n'
                      'If you want to start a new one, you must first finish the old one.',
                'ru': '✍️ Программы тренировок\n\n'
                      'У тебя уже есть активная программа тренировок:\n\n'
                      f'{name} | {level}\n\n'
                      'Если хочешь начать новую, сначала нужно закончить старую.',
                'ua': '✍️ Програми тренувань\n\n'
                      'У тебе вже є активна програма тренувань:\n\n'
                      f'{name} | {level}\n\n'
                      'Якщо хочеш розпочати нову, спочатку потрібно закінчити стару.',
            }
            button_text = {
                'en': '🚫 Stop program',
                'ru': '🚫 Закончить программу',
                'ua': '🚫 Закінчити програму',
            }
            buttons = [
                {'name': button_text[self.lang],
                 'callback_data': {'stop_program': True,
                                   'program': program.id}
                 }
            ]
            buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
            buttons.extend(self.attach_back_button('menu'))
            return texts[self.lang], InlineKeyboardMarkup(buttons)

        self.user.program = program
        self.user.save()

        days_before_next = 0
        if self.user.extra_data.get('last_program_day'):
            last_day = datetime.strptime(self.user.extra_data['last_program_day'], '%Y-%m-%d')
            now = datetime.now().strftime('%Y-%m-%d')
            now = datetime.strptime(now, '%Y-%m-%d')
            days_before_next = last_day + timedelta(days=program.group.days_between_trainings) - now
            days_before_next = days_before_next.days

        self.user.extra_data['last_program_day'] = datetime.now().strftime('%Y-%m-%d')
        if self.user.extra_data.get('days_in_row') is not None:
            self.user.extra_data['days_in_row'] += 1
        else:
            self.user.extra_data['days_in_row'] = 0

        days_in_row = self.user.extra_data['days_in_row']
        exercises = program.exercises[days_in_row % len(program.exercises)]

        self.user.extra_data['next_program_trainings'] = list(reversed(exercises))
        self.user.save()

        exs = list(Exercise.select().where(Exercise.id.in_(exercises)))
        ex_dict = {e: i for i, e in enumerate(exercises)}
        exs = sorted(exs, key=lambda x: ex_dict[x.id])
        for e in exs:
            tool = e.tool
            group = e.group
            text += f'\t • {group.get_name(self.lang)} | ' \
                    f'{tool.get_name(self.lang)} | ' \
                    f'{e.get_name(self.lang)}\n'

        text += '\n'

        if days_before_next > 0:
            next_training_date = datetime.now() + timedelta(days=days_before_next)
            next_training_date = next_training_date.strftime('%Y-%m-%d')
            texts = {
                'en': '⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️\n'
                      'Today I advise you to <b><u>REST!</u></b>\n'
                      f'It is better not to do the next workout according to the program before <b>{next_training_date}</b>\n\n'
                      '<b><u>INCREASING THE FREQUENCY OF TRAINING CAN CAUSE MUSCLE LOSS</u></b>\n\n'
                      'If you want to practice more often without harming your progress, choose a <b>other</b> program\n'
                      '⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️\n',
                'ru': '⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️\n'
                      'Сегодня советую <b><u>ОТДОХНУТЬ!</u></b>\n'
                      f'Следующую тренировку по программе лучше не делать раньше <b>{next_training_date}</b>\n\n'
                      '<b><u>УВЕЛИЧЕНИЕ ЧАСТОТЫ ТРЕНИРОВОК МОЖЕТ ПРИВЕСТИ К ПОТЕРЕ МЫШЦ</u></b>\n\n'
                      'Если хочешь заниматься чаще без вреда прогрессу, выбери <b>другую</b> программу\n'
                      '⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️\n',
                'ua': '⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️\n'
                      'Сьогодні раджу <b><u>ВІДПОЧИТИ!</u></b>\n'
                      f'Наступне тренування за програмою краще не робити раніше <b>{next_training_date}</b>\n\n'
                      "<b><u>ЗБФЛЬШЕННЯ ЧАСТОТИ ТРЕНУВАНЬ МОЖЕ ПРИВЕСТИ ДО ВТРАТИ М'ЯЗІВ</u></b>\n\n"
                      'Якщо хочеш займатися частіше без шкоди прогресу, виберіть <b>іншу</b> програму\n'
                      '⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️\n',
            }
            text += texts[self.lang]

        exercise = Exercise.get_by_id(exercises[0])
        button_texts = {
            'en': 'Start training 💪',
            'ru': 'Начать тренировку 💪',
            'ua': 'Почати тренування 💪'
        }
        buttons = [{'name': button_texts[self.lang],
                    'callback_data': {
                        "group": exercise.group.id,
                        "tool": exercise.tool.id,
                        "exercise": exercise.unique_id}
                    }]

        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('menu'))
        return text, InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return (callback_data.get('new_day') and
                    callback_data.get('program') is not None)
        return False
