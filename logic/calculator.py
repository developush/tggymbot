import re
from telegram import (
    constants,
    InlineKeyboardMarkup
)

from constants import Genders, ActivityLevelCoefficients
from logic.base import DefaultMessageHandler


class CalculatorGenderController(DefaultMessageHandler):
    check_subscription = True

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
            'en': '🧮 Calculator\nChoose your gender:',
            'ru': '🧮 Калькулятор\nВыбери свой пол:',
            'ua': '🧮 Калькулятор\nОбери свою стать:',
        }

        buttons = [{
            'text': {
                'en': 'Man',
                'ru': 'Мужчина',
                'ua': 'Чоловік',
            },
            'callback_data': {'calculator': True,
                              'gender': Genders.Man}
        }, {
            'text': {
                'en': 'Woman',
                'ru': 'Женщина',
                'ua': "Жінка",
            },
            'callback_data': {'calculator': True,
                              'gender': Genders.Man}
        }]

        buttons = [{'name': button['text'][self.lang],
                    'callback_data': button['callback_data']} for button in buttons]
        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('menu'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'calculator' == callback_data


class CalculatorLevelController(DefaultMessageHandler):
    check_subscription = True

    async def _call(self):
        await self.callback_query.answer()

        text, buttons = self._get_data()
        try:
            await self.callback_query.edit_message_text(
                text=text,
                reply_markup=buttons,
                parse_mode=constants.ParseMode.HTML
            )
        except:
            await self._context.bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                reply_markup=buttons,
                disable_notification=self.silent,
                parse_mode=constants.ParseMode.HTML
            )
        self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        callback_data = self.callback_query.data
        datas = []
        for i in ActivityLevelCoefficients:
            tmp = callback_data.copy()
            tmp['activity_level'] = i
            datas.append(tmp)
        texts = {
            'en': '🧮 Calculator\n'
                  'Choose your activity level:\n\n'
                  '<b>Seal</b>\n\t\tMoist, little or no training\n\n'
                  '<b>Common</b>\n\t\tIntermittent activity, light training 1-3 times per week\n\n'
                  '<b>Moderate</b>\n\t\tModerate activity, moderate physical work or regular exercise 3-5 days a week\n\n'
                  '<b>Stick in the ass</b>\n\t\tActive person, full-time physical work or intense training 6-7 times a week\n\n'
                  '<b>Gigachad</b>\n\t\tthe most active person, lives in the gym and sleeps in sets of 5 to 10 reps',
            'ru': '🧮 Калькулятор\n'
                  'Выбери свой уровень активности:\n\n'
                  '<b>Тюленьчик</b>\n\t\tМолоподвижный, тренировок мало или вообще отстусвуют\n\n'
                  '<b>Рядовой</b>\n\t\tПериодичная активость, легкие тренировки 1-3 раза в неделю\n\n'
                  '<b>Среднечёк</b>\n\t\tУмеренная активность, физическая работа средней тяжести или регулярные тренировки 3-5 дней в неделю\n\n'
                  '<b>Шило в заднице</b>\n\t\tАктивный человек, физическая работа полный день или интенсивные тренировки 6-7 раз в неделю\n\n'
                  '<b>Гигачад</b>\n\t\tСамый активный человек, живёт в зале и спит подходами 5 по 10',
            'ua': '🧮 Калькулятор\n'
                  'Обери свій рівень активності:\n\n'
                  '<b>Руснявий полонений</b>\n\t\tМолорухливий, єдина активність — сдача в полон ЗСУ\n\n'
                  '<b>Арестович</b>\n\t\tПеріодична активність, легкі тренування 2-3 рази на тиждень\n\n'
                  '<b>Середнячок</b>\n\t\tДля помірно активних людей: фізична робота середньої тяжкості або регулярні тренування 3-5 днів на тиждень\n\n'
                  '<b>Шило в дупі</b>\n\t\tАктивна людина, фізична робота повний день або інтенсивні тренування 6-7 разів на тиждень\n\n'
                  '<b>Гігачад</b>\n\t\tНайактивніша людина, живе в залі і спить підходами 5 по 10',
        }

        buttons = [{
            'text': {
                'en': 'Seal',
                'ru': 'Тюленьчик',
                'ua': 'Руснявий полонений',
            },
            'callback_data': datas[0]
        }, {
            'text': {
                'en': 'Common',
                'ru': 'Рядовой',
                'ua': 'Арестович',
            },
            'callback_data': datas[1]
        }, {
            'text': {
                'en': 'Moderate',
                'ru': 'Среднечёк',
                'ua': 'Середнячок',
            },
            'callback_data': datas[2]
        }, {
            'text': {
                'en': 'Stick in the ass',
                'ru': 'Шило в заднице',
                'ua': 'Шило в дупі',
            },
            'callback_data': datas[3]
        }, {
            'text': {
                'en': 'Gigachad',
                'ru': 'Гигачад',
                'ua': 'Гігачад',
            },
            'callback_data': datas[4]
        }
        ]

        buttons = [{'name': button['text'][self.lang],
                    'callback_data': button['callback_data']} for button in buttons]
        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('calculator'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return (callback_data.get('calculator') and
                    callback_data.get('gender') and
                    not callback_data.get('activity_level'))
        return False


class CalculatorParamsController(DefaultMessageHandler):
    check_subscription = True

    async def _call(self):
        await self.callback_query.answer()
        self._save_calculator_data()

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

        texts = {
            'en': '🧮 Calculator\n'
                  'Enter your Age | Height | Weight:\n'
                  '❗️Input format: 20 185 75 ❗️',
            'ru': '🧮 Калькулятор\n'
                  'Введи свой Возраст | Рост | Вес:\n'
                  '❗️Формат ввода: 20 185 75 ❗️',
            'ua': '🧮 Калькулятор\n'
                  'Введи свій Вік | Зріст | Вагу:\n'
                  '❗Формат введення: 20 185 75 ❗',
        }
        callback_data.pop('activity_level')
        buttons = self.attach_back_button(callback_data)
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    def _save_calculator_data(self):
        self.user.extra_data['calculator'] = self.callback_query.data
        self.user.save()

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return (callback_data.get('calculator') and
                    callback_data.get('gender') and
                    callback_data.get('activity_level'))
        return False


class CalculatorResultController(DefaultMessageHandler):
    check_subscription = True

    async def _call(self):
        text, buttons = self._get_data()
        menu_text = {
            'en': 'Menu:',
            'ru': 'Меню:',
            'ua': 'Меню:',
        }
        try:
            await self.bot.edit_message_text(
                text=text,
                chat_id=self.chat_id,
                reply_markup=buttons,
                parse_mode=constants.ParseMode.HTML
            )
        except:
            await self.bot.sendMessage(
                text=text,
                chat_id=self.chat_id,
                parse_mode=constants.ParseMode.HTML
            )
        await self.bot.sendMessage(
            text=menu_text[self.lang],
            chat_id=self.chat_id,
            reply_markup=buttons,
        )

    def _get_data(self):
        text = self._update.message.text
        data = re.findall(r'\d+(?:[.,]\d+)?', text)
        base, average, eating_cals, else_cals, deficit, surplus, imt = self._calculate(data)
        result_emoji = {
            'good': '🟢',
            'medium': '🟠',
            'bad': '🔴',
        }
        result = 'medium'
        if 18.5 <= imt <= 25:
            result = 'good'
        elif 15 >= imt or imt >= 30:
            result = 'bad'

        result = result_emoji[result]

        texts = {
            'en': '🧮 Calculator\n'
                  f'<b>Rating</b> — {result}\n\n'
                  f'<b>BMI</b> — {imt}\n'
                  f'<b>RATE OF CALORIES</b> — {average} kcal.\n'
                  '<b>Consumption of kcal.:</b>\n'
                  f'  • <b>{eating_cals}</b> — Digestion of food\n'
                  f'  • <b>{else_cals}</b> — Physical activity\n'
                  f'  • <b>{base}</b> — Basic metabolism (organ function, respiration, etc.)\n\n'
                  '*BMI - Body Mass Index, the norm is from 18.5 to 25\n\n'
                  '<b>Kcal. deficiency for weight loss:</b>\n<pre>'
                  '\t%\t|\tKcal\t|\tWeight loss rate\n' +
                  '\n'.join([f'\t{i["percent"]}\t|\t{i["cals"]}\t|\t{i["weight"]} кg/month' for i in deficit]) +
                  '</pre>'
                  '\n\n<b>Kcal. surplus for weight gain:</b>\n<pre>'
                  '\t%\t|\tKcal\t|\tWeight gain rate\n' +
                  '\n'.join([f'\t{i["percent"]}\t|\t{i["cals"]}\t|\t{i["weight"]} кg/month' for i in surplus]) +
                  '</pre>'
                  '\n\n<b>WARNING</b>\n'
                  'All weight gain and loss calculations are approximate.\n'
                  'For qualified advice, please ask in our <a href="https://t.me/+la91hUWvcas5N2Yy">Chat</a>',
            'ru': '🧮 Калькулятор\n'
                  f'<b>Оценка</b> — {result}\n\n'
                  f'<b>ИМТ</b> — {imt}\n'
                  f'<b>НОРМА КАЛОРИЙ</b> — {average} ккал.\n'
                  '<b>Трата ккал.</b>:\n'
                  f'  • <b>{eating_cals}</b> — Усвоение пищи\n'
                  f'  • <b>{else_cals}</b> — Физическая активность\n'
                  f'  • <b>{base}</b> — Базовый метаболизм (работа органов, дыхание и т.д.)\n\n'
                  '*ИМТ — Индекс Массы Тела, норма от 18.5 до 25\n\n'
                  '<b>Дефицит ккал. для похудения:</b>\n'
                  '<pre>\t%\t\t|\tКкал\t|\tCкорость похудения\n' +
                  '\n'.join([f'\t{i["percent"]}\t|\t{i["cals"]}\t|\t{i["weight"]} кг/месяц' for i in deficit]) +
                  '</pre>'
                  '\n\n<b>Добавочные ккал. для набора:</b>\n'
                  '<pre>\t%\t\t|\tКкал\t|\tCкорость набора\n' +
                  '\n'.join([f'\t{i["percent"]}\t|\t{i["cals"]}\t|\t{i["weight"]} кг/месяц' for i in surplus]) +
                  '</pre>'
                  '\n\n<b>ВАЖНО</b>\n'
                  'Все расчёты по набору и потере массы примерные.\n'
                  'Для получения квалифицированной консультации обратитесь в наш <a href="https://t.me/+la91hUWvcas5N2Yy">Чат</a>',
            'ua': '🧮 Калькулятор\n'
                  f'<b>Оцінка</b> — {result}\n\n'
                  f'<b>ІМТ</b> — {imt}\n'
                  f'<b>НОРМА КАЛОРІЙ</b> — {average} ккал.\n'
                  '<b>Трата ккал.:</b>\n'
                  f'  • <b>{eating_cals}</b> — Засвоєння їжі\n'
                  f'  • <b>{else_cals}</b> — Фізична активність\n'
                  f'  • <b>{base}</b> — Базовий метаболізм (робота органів, дихання і т.д.)\n\n'
                  '*ІМТ - Індекс Маси Тіла, норма від 18.5 до 25\n\n'
                  '<b>Дефіцит ккал. для схуднення:</b>\n<pre>'
                  '\t%\t|\tКкал\t|\tШвидкість схуднення\n' +
                  '\n'.join([f'\t{i["percent"]}\t|\t{i["cals"]}\t|\t{i["weight"]} кг/місяць' for i in deficit]) +
                  '</pre>'
                  '\n\n<b>Додаткові ккал. для набору:</b>\n<pre>'
                  '\t%\t|\tКкал\t|\tШвидкість набору\n' +
                  '\n'.join([f'\t{i["percent"]}\t|\t{i["cals"]}\t|\t{i["weight"]} кг/місяць' for i in surplus]) +
                  '</pre>'
                  '\n\n<b>ВАЖЛИВО</b>\n'
                  'Всі розрахунки з набору та втрати маси зразкові.\n'
                  'Для отримання кваліфікованої консультації звертайся у наш <a href="https://t.me/+la91hUWvcas5N2Yy">Чат</a>',
        }

        buttons = self.build_menu(self._menu_buttons[self.lang])
        return texts[self.lang], buttons

    def _calculate(self, data):
        saved_data = self.user.extra_data.pop('calculator')
        gender = saved_data['gender']
        activity_level = float(saved_data['activity_level'])
        age, height, weight = [float(i.replace(',', '.')) for i in data]

        imt = round(weight / (height / 100) ** 2, 1)
        base = round(10 * weight + 6.25 * height - 5 * age, 1)
        if gender == Genders.Man:
            base += 5
        else:
            base -= 161
        average = base * activity_level
        eating_cals = round(average * 0.1, 1)
        else_cals = round(average - base - eating_cals, 1)
        deficit = []
        for i in [5, 10, 15, 20]:
            percent = i / 100
            if i == 5:
                i = '5\t'
            deficit.append(dict(
                percent=i,
                cals=round(average * (1 - percent)),
                weight=round(average * percent / 250, 1)
            ))
        surplus = []
        for i in [5, 10, 15, 20]:
            percent = i / 100
            if i == 5:
                i = '5\t'
            surplus.append(dict(
                percent=i,
                cals=round(average * (1 + percent)),
                weight=round(average * percent / 250, 1)
            ))
        return base, average, eating_cals, else_cals, deficit, surplus, imt

    @classmethod
    def pattern(cls):
        return r'^\d+(?:[.,]\d+)?\s*?\d+(?:[.,]\d+)?\s\d+(?:[.,]\d+)?$'
