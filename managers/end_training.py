import typing
from datetime import datetime
from telegram import (
    Bot,
)
from random import choice

from config import (
    TOKEN,
    MAIN_PATH
)
from models import (
    db,
    Training,
    Set
)
from utils import (
    Logger,
    fh,
)


class TrainingController():
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

    def __init__(self, training_id):
        self.training = Training.get_by_id(training_id)
        self.user = self.training.user
        self.chat_id = self.user.chat_id
        self.lang = self.user.lang
        self.silent = self.user.extra_data.get('silent', False)
        self.bot = Bot(token=TOKEN)
        self._log = Logger(fh, 'TrainingController')
        self._static_path = MAIN_PATH

    async def call(self):
        training, sets = self._end_training()
        texts, gif = self._get_data(training, sets)
        if gif is not None:
            await self.bot.sendVideo(
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
            await self.bot.sendMessage(
                text=text[self.lang],
                chat_id=self.chat_id,
                disable_notification=self.silent
            )
        else:
            await self.bot.sendMessage(
                chat_id=self.chat_id,
                text=texts[self.lang],
                disable_notification=self.silent
            )

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
