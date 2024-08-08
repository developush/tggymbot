import re
import typing
from collections import defaultdict
from datetime import datetime
from peewee import fn
from random import choice
from telegram import (
    InlineKeyboardMarkup,
)

from models import (
    db,
    MuscleGroup,
    Exercise,
    Tool,
    Set,
    Training,
    User
)
from logic.base import DefaultMessageHandler


class MuscleGroupsController(DefaultMessageHandler):
    check_subscription = True

    async def _call(self):
        await self.callback_query.answer()

        text, buttons = self._get_data()
        if (self.callback_query.message.video or
                self.callback_query.message.photo):
            try:
                await self.callback_query.delete_message()
            finally:
                await self._context.bot.sendMessage(
                    chat_id=self.chat_id,
                    text=text,
                    reply_markup=buttons,
                    disable_notification=self.silent
                )
        else:
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
            'en': '💪Select muscle group:',
            'ru': '💪Выбери группу мышц:',
            'ua': "💪Обери групу м'язів",
        }
        groups = MuscleGroup.select().order_by(MuscleGroup.order)
        buttons = [{'name': group.name[self.lang],
                    'callback_data': {'group': group.unique_id}} for group in groups]
        buttons = self.build_menu(buttons, raw=True)
        buttons.extend(self.attach_back_button('menu'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'start_training' == callback_data


class ExerciseToolController(DefaultMessageHandler):
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
        callback_data = self.callback_query.data
        self._log.info(f'Callback data - {callback_data}')

        group = MuscleGroup.get(unique_id=callback_data['group'])

        header = f'💪 {group.name[self.lang].upper()}\n'
        texts = {
            'en': header + 'Choose tool for exercise:',
            'ru': header + 'Выбери инструмент для упражнения:',
            'ua': header + 'Обери інструмент для вправи:'
        }

        buttons = [{'name': tool.name[self.lang],
                    'callback_data': {
                        'group': callback_data['group'],
                        'tool': tool.id}} for tool in (Tool
                                                       .select(fn.DISTINCT(Tool.id),
                                                               Tool.name,
                                                               Tool.order,
                                                               Tool.created)
                                                       .join(Exercise)
                                                       .join(MuscleGroup)
                                                       .where(MuscleGroup.unique_id == callback_data['group'])
                                                       .order_by(Tool.order,
                                                                 Tool.created))]
        buttons = self.build_menu(buttons, buttons_in_row=1, raw=True)
        buttons.extend(self.attach_back_button('start_training'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return (callback_data.get('group') is not None and
                    callback_data.get('tool') is None)
        return False


class GroupExercisesController(DefaultMessageHandler):
    check_subscription = True

    async def _call(self):
        await self.callback_query.answer()
        buttons, text = self._get_data()
        if self.callback_query.message.text:
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
        self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        callback_data = self.callback_query.data
        self._log.info(f'Callback data - {callback_data}')

        exercises = list(Exercise
                         .select()
                         .join(MuscleGroup)
                         .where(MuscleGroup.unique_id == callback_data['group'],
                                Exercise.tool_id == callback_data['tool'])
                         .order_by(Exercise.order,
                                   Exercise.created)
                         )
        sets = (Set
                .select()
                .where(Set.user == self.user,
                       Set.exercise_id.in_([e.id for e in exercises])))
        exercise_order = defaultdict(int)
        recent_exercises = []
        for s in sets:
            exercise_order[s.exercise_id] += 1
            name = s.exercise.name
            name = name.get(self.lang, name['en'])
            recent_exercises.append(f'• {name}')

        ex = exercises[0]
        header = f'💪 {ex.group.name[self.lang].upper()} | {ex.tool.name[self.lang].upper()}\n'
        texts = {
            'en': header + 'Choose exercise',
            'ru': header + 'Выбери упражнениe',
            'ua': header + 'Обери вправу'
        }

        text = texts[self.lang]
        if recent_exercises:
            recent_exercises = '\n'.join(set(recent_exercises))
            texts = {
                'en': '\nRecent:\n',
                'ru': '\nНедавние:\n',
                'ua': '\nНедавні:\n'
            }
            text += texts[self.lang] + recent_exercises

        exercises = sorted(exercises, key=lambda x: exercise_order.get(x.id, 0), reverse=True)

        buttons = [{'name': exc.get_name(self.lang),
                    'callback_data': {'group': exc.group.unique_id,
                                      'tool': exc.tool_id,
                                      'exercise': exc.unique_id}} for exc in exercises]

        buttons = self.build_menu(buttons, buttons_in_row=2, raw=True)

        buttons.extend(self.attach_back_button({'group': callback_data['group']}))
        return InlineKeyboardMarkup(buttons), text

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return (callback_data.get('group') is not None and
                    callback_data.get('tool') is not None and
                    callback_data.get('exercise') is None)
        return False


class ExerciseController(DefaultMessageHandler):
    check_subscription = True

    async def _call(self):
        await self.callback_query.answer()
        media, text, buttons = self._get_data()
        try:
            await self.callback_query.delete_message()
        finally:
            await self._context.bot.sendVideo(
                chat_id=self.chat_id,
                height=1920,
                width=1080,
                video=media,
                caption=text,
                reply_markup=buttons,
                disable_notification=self.silent
            )
            self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        callback_data = self.callback_query.data
        self._log.info(f'Callback data - {callback_data}')
        exercise = Exercise.get(unique_id=callback_data['exercise'])

        path = self._static_path + exercise.media[self.gender][0]
        with open(path, 'rb') as f:
            media = f.read()

        ex_name = exercise.get_name(self.lang)
        header = f'💪 {exercise.group.name[self.lang].upper()} | {exercise.tool.name[self.lang].upper()}'
        description = exercise.description.get(self.lang)
        if description is None:
            description = exercise.description['en']
        text = f'{header}\n\n{ex_name}\n\n{description}'

        buttons_texts = {'ru': [{'name': 'Начать упражнение 💪',
                                 'callback_data': {'start_exercise': exercise.unique_id}}],
                         'en': [{'name': 'Start exercise 💪',
                                 'callback_data': {'start_exercise': exercise.unique_id}}],
                         'ua': [{'name': 'Почати вправу 💪',
                                 'callback_data': {'start_exercise': exercise.unique_id}}]
                         }

        buttons = self.build_menu(buttons_texts[self.lang],
                                  buttons_in_row=1,
                                  raw=True)
        if self.user.extra_data.get('next_program_trainings') is None:
            buttons.extend(self.attach_back_button({'group': exercise.group.unique_id,
                                                    'tool': exercise.tool_id}))
        return media, text, InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return (callback_data.get('group') is not None and
                    callback_data.get('tool') is not None and
                    callback_data.get('exercise') is not None)
        return False


class StartExerciseController(DefaultMessageHandler):
    check_subscription = True
    end_buttons = {
        'ru': [{'name': 'Закончить тренировку 🚫',
                'callback_data': 'stop_training_check'}],
        'en': [{'name': 'Stop training 🚫',
                'callback_data': 'stop_training_check'}],
        'ua': [{'name': 'Закінчити тренування 🚫',
                'callback_data': 'stop_training_check'}]
    }

    async def _call(self):
        await self.callback_query.answer()
        text, buttons, exercise = self._get_data()
        try:
            await self.callback_query.delete_message()
        finally:
            msg = await self._context.bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                reply_markup=buttons,
                disable_notification=self.silent
            )
            await self._update_training(exercise, msg)
            self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        callback_data = self.callback_query.data
        self._log.info(f'Callback data - {callback_data}')
        exercise = Exercise.get(unique_id=callback_data['start_exercise'])

        text = self._get_text(exercise)

        next_program_trainings = self.user.extra_data.get('next_program_trainings')
        if next_program_trainings is not None and exercise.id in next_program_trainings:
            if exercise.id != next_program_trainings[-1]:
                next_program_trainings.pop()
            if not next_program_trainings or exercise.id == next_program_trainings[0]:
                next_program_trainings = []
            self.user.extra_data['next_program_trainings'] = next_program_trainings
            self.user.save()

        if next_program_trainings is None:
            buttons = self.build_menu(self.end_buttons[self.lang],
                                      buttons_in_row=1,
                                      raw=True)
            buttons.extend(self.attach_back_button({'group': exercise.group.unique_id,
                                                    'tool': exercise.tool_id},
                                                   names={'en': 'Next exercise 💪',
                                                          'ru': 'Следующее упражнение 💪',
                                                          'ua': 'Наступна вправа 💪'}))
            buttons.extend(self.attach_back_button('start_training',
                                                   names={'en': 'To muscle groups 👈',
                                                          'ru': 'К группам мышц 👈',
                                                          'ua': "До груп м'язiв 👈"}))
        elif next_program_trainings:
            next_exercise = Exercise.get_by_id(next_program_trainings[-2])
            buttons = self.attach_back_button({"group": next_exercise.group.id,
                                               "tool": next_exercise.tool.id,
                                               "exercise": next_exercise.unique_id},
                                              names={'en': 'Next exercise 💪',
                                                     'ru': 'Следующее упражнение 💪',
                                                     'ua': 'Наступна вправа 💪'})
        else:
            buttons = self.build_menu(self.end_buttons[self.lang],
                                      buttons_in_row=1,
                                      raw=True)
        return text, InlineKeyboardMarkup(buttons), exercise

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return callback_data.get('start_exercise') is not None
        return False

    def _get_text(self, exercise):
        previous_set = (Set
                        .select()
                        .where(Set.user == self.user,
                               Set.exercise == exercise,
                               Set.end.is_null(False))
                        .order_by(Set.id.desc()))

        need_weight = exercise.tool.need_weight
        ex_name = exercise.get_name(self.lang)
        if ex_name is None:
            ex_name = exercise.name['en']
        if previous_set.exists():
            previous_set = previous_set.first()
            if need_weight:
                data = '\n'.join(['{}. {} - {} kg'.format(index + 1, rep['reps'], rep['weight'])
                                  for index, rep in enumerate(previous_set.data)])
            else:
                data = '\n'.join(
                    ['{}. {}'.format(index + 1, rep['reps']) for index, rep in enumerate(previous_set.data)])
            text = {
                'en': f'Exercise - {ex_name}\n'
                      f'Previous reps:\n'
                      f'{data}\n'
                      f'❗Format REPS{"" if not need_weight else " WEIGHT"} ❗\n',
                'ru': f'Упражнение - {ex_name}\n'
                      f'Прошлые подходы:\n'
                      f'{data}\n'
                      f'❗Формат ПОВТОРЕНИЯ{"" if not need_weight else " ВЕС"} ❗\n',
                'ua': f'Вправа - {ex_name}\n'
                      f'Минулі підходи:\n'
                      f'{data}\n'
                      f'❗Формат ПОВТОРЕННЯ{"" if not need_weight else " ВАГА"} ❗\n',
            }
        else:
            tmp = "" if not need_weight else " 50"
            text = {
                'en': f'Exercise - {ex_name}\n'
                      f'❗Input format REPS{"" if not need_weight else " WEIGHT"} ❗\n'
                      f'Example 10{tmp}',
                'ru': f'Упражнение - {ex_name}\n'
                      f'❗Формат ввода ПОВТОРЕНИЯ{"" if not need_weight else " ВЕС"} ❗\n'
                      f'Пример 10{tmp}',
                'ua': f'Вправа - {ex_name}\n'
                      f'❗Формат введення ПОВТОРЕННЯ{"" if not need_weight else " ВАГА"} ❗\n'
                      f'Приклад 10{tmp}',
            }
        return text[self.lang]

    async def _update_training(self, exercise, msg):
        with db.atomic():
            training = (Training
                        .select()
                        .where(Training.user == self.user,
                               Training.end.is_null()))
            if not training.exists():
                training = Training.create(
                    user=self.user,
                )
                self._get_set(exercise, training)

            user = User.get_by_id(self.user.id)
            user.extra_data['last_exercise'] = exercise.id
            user.extra_data['message_id'] = msg.message_id
            user.save()
            self._user = user
            return training

    def _get_set(self, exercise, training):
        tr_set = (Set
                  .select()
                  .where(Set.user == self.user,
                         Set.training_id == training.id,
                         Set.exercise == exercise,
                         Set.end.is_null()))
        if tr_set.exists():
            return tr_set.first()
        return Set.create(
            user=self.user,
            exercise=exercise,
            training=training,
        )


class UpdateSetController(StartExerciseController):
    update_set = True

    async def _call(self):
        current_set = self._update_set()
        text, buttons = self._get_data(current_set)
        user = User.get_by_id(self.user.id)
        if user.extra_data.get('message_id'):
            await self.bot.edit_message_text(
                text=text,
                chat_id=self.chat_id,
                message_id=user.extra_data['message_id'],
                reply_markup=buttons,
            )

    def _update_set(self):
        user = User.get_by_id(self.user.id)
        exercise = Exercise.get_by_id(user.extra_data['last_exercise'])
        training = (Training
                    .select()
                    .where(Training.user == self.user,
                           Training.end.is_null())
                    .first())
        tr_set = self._get_set(exercise, training)
        if self.update_set:
            if self._update.edited_message:
                text = self._update.edited_message.text
                tr_set.data.pop()
            else:
                text = self._update.message.text
            data = re.findall(r'\d+(?:[.,]\d+)?', text)
            tr_set.data.append({
                'reps': int(data[0]),
                'weight': 0 if len(data) == 1 else float(data[1].replace(',', '.')),
                'timestamp': datetime.now().timestamp()
            })
            tr_set.save()
        return tr_set

    def _get_data(self, tr_set):
        text = self._get_text(tr_set)

        exercise = tr_set.exercise
        next_program_trainings = self.user.extra_data.get('next_program_trainings')

        if next_program_trainings is None:
            buttons = self.build_menu(self.end_buttons[self.lang],
                                      buttons_in_row=1,
                                      raw=True)
            buttons.extend(self.attach_back_button({'group': exercise.group.unique_id,
                                                    'tool': exercise.tool_id},
                                                   names={'en': 'Next exercise 💪',
                                                          'ru': 'Следующее упражнение 💪',
                                                          'ua': 'Наступна вправа 💪'}))
            buttons.extend(self.attach_back_button('start_training',
                                                   names={'en': 'To muscle groups 👈',
                                                          'ru': 'К группам мышц 👈',
                                                          'ua': "До груп м'язiв 👈"}))
        elif next_program_trainings:
            exercise = Exercise.get_by_id(next_program_trainings[-2])
            buttons = self.attach_back_button({"group": exercise.group.id,
                                               "tool": exercise.tool.id,
                                               "exercise": exercise.unique_id},
                                              names={'en': 'Next exercise 💪',
                                                     'ru': 'Следующее упражнение 💪',
                                                     'ua': 'Наступна вправа 💪'})
        else:
            buttons = self.build_menu(self.end_buttons[self.lang],
                                      buttons_in_row=1,
                                      raw=True)
        return text, InlineKeyboardMarkup(buttons)

    def _get_text(self, tr_set):
        need_weight = tr_set.exercise.tool.need_weight
        ex_name = tr_set.exercise.get_name(self.lang)
        previous_set = (Set
                        .select()
                        .where(Set.user == self.user,
                               Set.exercise == tr_set.exercise,
                               Set.end.is_null(False))
                        .order_by(Set.created.desc()))
        previous_data = []
        if previous_set.exists():
            previous_set = previous_set.first()
            if need_weight:
                previous_data = '\n'.join(
                    ['{}. {} - {} kg'.format(index + 1, rep['reps'], rep['weight'])
                     for index, rep in enumerate(previous_set.data)])
            else:
                previous_data = '\n'.join(['{}. {}'.format(index + 1, rep['reps'])
                                           for index, rep in enumerate(previous_set.data)])

        if need_weight:
            data = '\n'.join(['{}. {} - {} kg'.format(index + 1, rep['reps'], rep['weight'])
                              for index, rep in enumerate(tr_set.data)])
        else:
            data = '\n'.join(['{}. {}'.format(index + 1, rep['reps']) for index, rep in enumerate(tr_set.data)])
        text = {
            'en': f'Exercise - {ex_name}\n' + ("Last reps:\n" + f"{previous_data}" + '\n' if previous_data else '') +
                  f'Current reps:\n'
                  f'{data}\n'
                  f'❗Format REPS{"" if not need_weight else " WEIGHT"} ❗\n',
            'ru': f'Упражнение - {ex_name}\n' + (
                "Прошлые подходы:\n" + f"{previous_data}" + '\n' if previous_data else '') +
                  f'Текущие подходы:\n'
                  f'{data}\n'
                  f'❗Формат ПОВТОРЕНИЯ{"" if not need_weight else " ВЕС"} ❗\n',
            'ua': f'Вправа - {ex_name}\n' + ("Минулі підходи:\n" + f"{previous_data}" + '\n' if previous_data else '') +
                  f'Поточні підходи:'
                  f'{data}\n'
                  f'❗Формат ПОВТОРЕННЯ{"" if not need_weight else " ВАГА"} ❗\n',
        }
        return text[self.lang]

    @classmethod
    def pattern(cls):
        return r'^\d+(?:[.,]\d+)?$'

    @classmethod
    def extended_pattern(cls):
        return r'^\d+(?:[.,]\d+)?\s*?\d+(?:[.,]\d+)?$'


class CheckEndTrainingController(UpdateSetController):
    update_set = False
    end_buttons = {
        'ru': [{'name': 'Вы уверены ⁉️',
                'callback_data': 'stop_training'}],
        'en': [{'name': 'Are you sure ⁉️',
                'callback_data': 'stop_training'}],
        'ua': [{'name': 'Ви впевнені ⁉️',
                'callback_data': 'stop_training'}]
    }

    async def _call(self):
        await self.callback_query.answer()
        current_set = self._update_set()
        text, buttons = self._get_data(current_set)
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

    @staticmethod
    def pattern(callback_data):
        return callback_data == 'stop_training_check'


class EndTrainingController(DefaultMessageHandler):
    gifs = (
        'static/end_training/cat-meme.mp4',
        'static/end_training/curls-gym.mp4',
        'static/end_training/funny-workout.mp4',
        'static/end_training/gym-fail.mp4',
        'static/end_training/gym-passedout.mp4',
        'static/end_training/gym-time.mp4',
        'static/end_training/hasbulla-hasbullah.mp4',
        'static/end_training/ukr.mp4'
    )

    async def _call(self):
        if not self._update.message:
            await self.callback_query.answer()

        training, sets = self._end_training()
        texts, gif = self._get_data(training, sets)
        if gif is not None:
            try:
                await self.callback_query.delete_message()
            finally:
                await self._context.bot.sendVideo(
                    chat_id=self.chat_id,
                    video=gif,
                    caption=texts[self.lang],
                    disable_notification=self.silent
                )
                text = {
                    'en': 'Menu:',
                    'ru': 'Меню:',
                    'ua': 'Меню:'
                }
                await self._context.bot.sendMessage(
                    text=text[self.lang],
                    chat_id=self.chat_id,
                    reply_markup=self.build_menu(self._menu_buttons[self.lang]),
                    disable_notification=self.silent
                )
        else:
            await self._context.bot.sendMessage(
                chat_id=self.chat_id,
                text=texts[self.lang],
                reply_markup=self.build_menu(self._menu_buttons[self.lang]),
                disable_notification=self.silent
            )
        if not self._update.message:
            self._context.drop_callback_data(self.callback_query)

    def _get_data(self, training: typing.Union['Training', None], sets: list['Set']):
        if training is None:
            texts = {
                'en': "You didn't start a workout to finish it. Let's fix it!",
                'ru': 'Ты не начинал тренировку, чтобы её заканчивать. Надо это исправлять!',
                'ua': 'Ти не починав тренування, щоб його закінчувати. Потрібно це виправляти!'
            }
            return texts, None

        training_time = (training.end - training.created).total_seconds()
        exercises = []
        weight_lifted = 0
        avg_set_duration = 0
        avg_rest_duration = 0
        exc_num = 0
        for s in sets:
            exc = f'\t - {s.exercise.get_name(self.lang)}'
            if exc not in exercises:
                exercises.append(exc)
            for i in range(len(s.data)):
                weight_lifted += s.data[i].get('weight', 0) * s.data[i].get('reps', 0)
                if i == len(s.data) - 1:
                    pass
                else:
                    avg_rest_duration += s.data[i + 1]['timestamp'] - s.data[i]['timestamp']
            exc_num += len(s.data)
            avg_set_duration += s.data[-1]['timestamp'] - s.data[0]['timestamp']
        exercises = '\n'.join(exercises)
        weight_lifted = round(weight_lifted)
        avg_set_duration = round(avg_set_duration / max(len(sets), 1))
        avg_rest_duration = round(avg_rest_duration / max(exc_num, 1))

        texts = {'en': 'Training summary:\n'
                       f'• Exercises: \n{exercises}\n'
                       f'• Weight lifted: {weight_lifted} kg\n'
                       f'• Training time: {int(training_time // 60)} min. {int(training_time % 60)} sec. \n'
                       f'• Avg. set duration: {avg_set_duration // 60} min. {avg_set_duration % 60} sec.\n'
                       f'• Avg. rest duration: {avg_rest_duration // 60} min. {avg_rest_duration % 60} sec.',
                 'ru': 'Итог тренировки:\n'
                       f'• Упражнения: \n{exercises}\n'
                       f'• Поднятый вес: {weight_lifted} kg\n'
                       f'• Время тренировки: {int(training_time // 60)} min. {int(training_time % 60)} sec. \n'
                       f'• Среднее время на упражнение: {avg_set_duration // 60} min. {avg_set_duration % 60} sec.\n'
                       f'• Среднее время отдыха: {avg_rest_duration // 60} min. {avg_rest_duration % 60} sec.',
                 'ua': 'Підсумок тренування:\n'
                       f'• Вправи: \n{exercises}\n'
                       f'• Піднята вага: {weight_lifted} kg\n'
                       f'• Час тренування: {int(training_time // 60)} min. {int(training_time % 60)} sec. \n'
                       f'• Середній час на вправу: {avg_set_duration // 60} min. {avg_set_duration % 60} sec.\n'
                       f'• Сeредній час відпочинку: {avg_rest_duration // 60} min. {avg_rest_duration % 60} sec.', }

        with open(self._static_path + choice(self.gifs), 'rb') as f:
            gif = f.read()

        return texts, gif

    def _end_training(self):
        sets = []
        with db.atomic():
            last_training = (
                Training
                .select()
                .where(Training.user == self.user,
                       Training.end.is_null()))
            last_training = last_training.first()
            if last_training is not None:
                tr_sets = Set.select().where(Set.training == last_training)
                for tr_set in tr_sets:
                    tr_set = Set.get_by_id(tr_set)
                    if tr_set.data:
                        end = tr_set.data[-1]
                        tr_set.end = datetime.fromtimestamp(end['timestamp'])
                        sets.append(tr_set)
                        tr_set.save()
                    else:
                        tr_set.delete_instance()
                last_training.end = datetime.now()
                last_training.save()
            self.user.extra_data['next_program_trainings'] = None
            self.user.save()
        return last_training, sets

    @staticmethod
    def pattern(callback_data):
        return callback_data == 'stop_training'
