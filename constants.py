DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'


class MuscleGroupTypes:
    Upper = 1
    Lower = 2
    Cardio = 3


class Languages:
    Russian = 'ru'
    English = 'en'
    Ukrainian = 'ua'

    Names = {
        'en': {
            'en': 'English',
            'ru': 'Английский',
            'ua': 'Англійська',
        },
        'ru': {
            'en': 'Russian',
            'ru': 'Русский',
            'ua': 'Російська',
        },
        'ua': {
            'en': 'Ukrainian',
            'ru': 'Украинский',
            'ua': 'Українська',
        },
    }

    @classmethod
    def all(cls):
        return (cls.Russian,
                cls.English,
                cls.Ukrainian)


USER_LANGUAGES = {}


BOOLS = {
    True: {
        'en': 'On',
        'ru': 'Вкл.',
        'ua': 'Вкл.'
    },
    False: {
        'en': 'Off',
        'ru': 'Выкл.',
        'ua': 'Вимк.'
    }
}


class EfficiencyCoefficients:
    BaseCF = 1.0278
    RepCF = 0.0278


class SubscriptionValue:
    Low = 1
    Medium = 2
    High = 3


class Genders:
    Man = 'male'
    Woman = 'female'


ActivityLevelCoefficients = [1.2, 1.375, 1.55, 1.725, 1.9]
