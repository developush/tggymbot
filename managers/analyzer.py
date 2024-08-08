import os
import pdfkit
from jinja2 import Environment, FileSystemLoader
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from telegram import (
    Bot,
)

from config import (
    MAIN_PATH,
    WKHTMLTOPDF,
    TOKEN
)
from constants import (
    EfficiencyCoefficients as EffC,
)
from models import (
    User,
    Training,
    Set
)
from utils import (
    Logger,
    fh,
    get_base_58_string
)


class Analyzer:
    def __init__(self, user_id, period):
        self.user = User.get_by_id(user_id)
        self.chat_id = self.user.chat_id
        self.lang = self.user.lang
        self.silent = self.user.extra_data.get('silent', False)
        self.period = period
        self.bot = Bot(token=TOKEN)
        self._log = Logger(fh, 'AnalyticGenerator')

    async def call(self):
        text, analytics_file, analytics_path = self._get_data(self.user)
        if analytics_file is not None:
            await self.bot.sendDocument(
                chat_id=self.chat_id,
                document=analytics_file,
                filename='analytics.pdf',
                caption=text,
                disable_notification=self.silent
            )
            self.remove_file(analytics_path)
        else:
            await self.bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                disable_notification=self.silent
            )

        menu_text = {
            'en': '⬇️ Use bot menu to continue work 💪',
            'ru': '⬇️ Используйте меню бота для продолжения работы 💪',
            'ua': '⬇️ Для продовження роботи використовуйте меню бота 💪'
        }
        await self.bot.sendMessage(
            chat_id=self.chat_id,
            text=menu_text[self.lang],
            disable_notification=self.silent
        )

    def _get_data(self, user):
        self._log.info(f'Start generating analytics for {user.id}')
        texts = {
            'en': "That's your analytics. \nKeep going 💪",
            'ru': 'Вот твоя аналитика. \nПродолжай в том же духе 💪',
            'ua': "Ось твоя аналітика. \nПродовжуй в тому ж дусі 💪",
        }
        empty_texts = {
            'en': "There were no trainings during selected period. \nIt's time to fix it 💪",
            'ru': 'За выбранный период не было тренировок. \nПора это исправить 💪',
            'ua': "За вибраний період не було тренувань. \nЧас це виправити 💪",
        }
        periods = {
            '1': {'en': '1 MONTH',
                  'ru': '1 МЕСЯЦ',
                  'ua': '1 МІСЯЦЬ'},
            '3': {'en': '3 MONTH',
                  'ru': '3 МЕСЯЦА',
                  'ua': '3 МІСЯЦІ'},
            '-1': {'en': 'ALL TIME',
                   'ru': 'ВСЁ ВРЕМЯ',
                   'ua': 'ВЕСЬ ЧАС'},
        }

        analytics_path, plots = self._get_file(self.period,
                                               periods[str(self.period)],
                                               user)
        if analytics_path is None:
            return empty_texts[self.lang], None, None

        with open(analytics_path, 'rb') as f:
            analytics_file = f.read()

        return (texts[self.lang],
                analytics_file,
                analytics_path)

    def _get_trainings_data(self, period, user):
        trainings = (Training
                     .select()
                     .where(Training.user == user,
                            Training.end.is_null(False))
                     .order_by(Training.created))
        if period != 'all':
            start_date = datetime.now() - timedelta(days=30 * int(period))
            trainings.where(Training.created >= start_date)

        user_weight = int(user.extra_data.get('weight', 10))

        total_trainings = trainings.count()
        if not total_trainings:
            return None, None, None, None, None, None
        avg_training_time = 0
        avg_time_btw_training = 0
        total_sets = 0
        exercises_max_scores = {}
        reps_data = {}
        for training in trainings:
            sets = Set.select().where(Set.training_id == training.id)
            total_sets += sets.count()
            avg_training_time += (training.end - training.created).total_seconds()
            for s in sets:
                if exercises_max_scores.get(s.exercise.get_name(user.lang)) is None:
                    group = s.exercise.group.name[user.lang]
                    exercises_max_scores[s.exercise.get_name(user.lang)] = {'group': group,
                                                                            'max_score': 0}
                else:
                    group = exercises_max_scores[s.exercise.get_name(user.lang)]['group']
                ex_date = s.created
                exercise = s.exercise.get_name(user.lang)
                if reps_data.get(group) is None:
                    reps_data[group] = {}
                if reps_data[group].get(exercise) is None:
                    reps_data[group][exercise] = []

                score = 0
                if reps_data.get(group) is None:
                    reps_data[group] = {exercise: []}
                if reps_data[group].get(exercise) is None:
                    reps_data[group][exercise] = []
                for sub_set in s.data:
                    weight = sub_set['weight']
                    if not weight:
                        weight = user_weight
                    score += self._get_score(weight, sub_set['reps'])

                max_score = max(exercises_max_scores[exercise]['max_score'], score)
                exercises_max_scores[exercise]['max_score'] = max_score

                reps_data[group][exercise].append({'score': score,
                                                   'date': ex_date})

        for index in range(total_trainings - 1):
            avg_time_btw_training += (trainings[index + 1].created - trainings[index].created).total_seconds()

        avg_training_time = avg_training_time / total_trainings
        avg_time_btw_training = avg_time_btw_training / max(total_trainings - 1, 1)

        return (total_trainings,
                total_sets,
                exercises_max_scores,
                reps_data,
                avg_training_time,
                avg_time_btw_training)

    def _get_score(self, weight, reps):
        return round(weight / (EffC.BaseCF - EffC.RepCF * reps / 10) * 100)

    def _create_plot(self, name, data, max_score):
        texts = {
            'x': {'en': 'Date',
                  'ru': 'Дата',
                  'ua': 'Дата'},
            'y': {'en': 'Progres',
                  'ru': 'Прогресс',
                  'ua': 'Прогрес'}
        }
        self._log.info('Start creating plot')
        scores = []
        for index, d in enumerate(data):
            scores.append(round((d['score'] / max_score) * 100, 2))
        dates = [i + 1 for i in range(len(scores))]
        index = np.arange(len(scores))
        plt.figure()
        plt.bar(dates, scores, color=['#ed5555', '#ed8355', '#edd155', '#99ed55',
                                      '#55edd5', '#559ced', '#5855ed', '#ba55ed',
                                      '#ed55cf', '#ed5585'])
        plt.xlabel(texts['x'][self.lang])
        plt.ylabel(texts['y'][self.lang])
        plt.xticks(index, dates)
        plt.title(name)
        fig_name = f'{MAIN_PATH}/static/tmp/{get_base_58_string()}.png'
        plt.savefig(fig_name, bbox_inches='tight')
        plt.close()
        self._log.info('End creating plot')
        return fig_name

    def _get_file(self, period, title, user):
        texts = {
            'total_trainings': {
                'en': 'Total trainings:',
                'ru': 'Количество тренировок:',
                'ua': 'Кількість тренувань:'},
            'total_sets': {
                'en': 'Total sets:',
                'ru': 'Количество упражнений:',
                'ua': 'Кількість вправ:'},
            'avg_training_time': {
                'en': 'Avg. training time:',
                'ru': 'Среднее время тренировки:',
                'ua': 'Середній час тренування:'},
            'avg_time_btw_training': {
                'en': 'Avg. time between trainings:',
                'ru': 'Среднее время между тренировками:',
                'ua': 'Середній час між тренуваннями:'},
            'date_btw': {
                'en': '{} d. {} h.',
                'ru': '{} д. {} ч.',
                'ua': '{} д. {} г.'
            },
            'date_tr': {
                'en': '{} h. {} m.',
                'ru': '{} ч. {} м.',
                'ua': '{} г. {} хв.'
            }
        }
        self._log.info('Start generating plot data')
        (total_trainings,
         total_sets,
         exercises_max_scores,
         reps_data,
         avg_training_time,
         avg_time_btw_training) = self._get_trainings_data(period, user)
        self._log.info('End generating plot data')
        if total_trainings is None:
            return None, None

        plots = {}
        for group in reps_data.keys():
            tmp = []
            if plots.get(group) is None:
                plots[group] = []
            for exercise in reps_data[group].keys():
                if not exercises_max_scores[exercise]['max_score']:
                    continue
                plot_file = self._create_plot(exercise,
                                              reps_data[group][exercise],
                                              exercises_max_scores[exercise]['max_score'])
                tmp.append(plot_file)
                if len(tmp) == 3:
                    plots[group].append(tmp)
                    tmp = []
            if tmp:
                plots[group].append(tmp)

        main_info = {
            texts['total_trainings'][self.lang]: total_trainings,
            texts['total_sets'][self.lang]: total_sets,
            texts['avg_training_time'][self.lang]: texts['date_tr'][self.lang].format(
                int(avg_training_time // 3600),
                int(avg_time_btw_training // 60 % 60)),
            texts['avg_time_btw_training'][self.lang]: texts['date_btw'][self.lang].format(
                int(avg_time_btw_training // 86400),
                int(avg_time_btw_training // 3600 % 24)),
        }

        self._log.info('Start generating pdf')
        env = Environment(loader=FileSystemLoader(MAIN_PATH + '/static'))
        template = env.get_template("analytics/template.html")
        html_string = template.render(title=title[self.lang],
                                      main_info=main_info,
                                      plots=plots,
                                      style_path=MAIN_PATH + '/static/analytics/style.css')
        config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF)
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'enable-local-file-access': None,
            'no-outline': None
        }
        analytics_path = f'{MAIN_PATH}/static/tmp/{get_base_58_string()}.pdf'
        pdfkit.from_string(html_string,
                           analytics_path,
                           configuration=config,
                           options=options)
        self._log.info('End generating pdf')
        for group in plots.keys():
            for i in plots[group]:
                for j in i:
                    self.remove_file(j)

        return analytics_path, plots

    def remove_file(self, file_path):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            self._log.warning(f"Can't remove file - {file_path}")
