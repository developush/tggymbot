from functools import wraps
from peewee import (
    Model,
    CharField,
    DateTimeField,
    ForeignKeyField,
    datetime as peewee_datetime,
    IntegerField,
    BooleanField,
    DoubleField
)
from playhouse.pool import PooledPostgresqlExtDatabase
from playhouse.postgres_ext import BinaryJSONField

from config import DB_CONFIG, DEFAULT_LANGUAGE
from constants import MuscleGroupTypes, SubscriptionValue
from utils import get_base_58_string

peewee_now = peewee_datetime.datetime.now

db = PooledPostgresqlExtDatabase(**DB_CONFIG)
db.commit_select = True
db.autorollback = True


def open_db_connection():
    if db.is_closed():
        db.connect()


def close_db_connection():
    if not db.is_closed():
        db.close()


def db_connect_wrapper(func):
    """
    connect to db and disconnect from it
    """

    @wraps(func)
    def wrapper(*args, **kwds):
        try:
            open_db_connection()
            return func(*args, **kwds)
        finally:
            close_db_connection()

    return wrapper


class _Model(Model):
    class Meta:
        database = db


class MuscleGroup(_Model):
    class Meta:
        db_table = 'muscle_groups'

    unique_id = CharField(unique=True, index=True)
    name = BinaryJSONField(default=dict)
    config = BinaryJSONField(default=dict)
    order = IntegerField(default=0)
    type = IntegerField(default=MuscleGroupTypes.Upper)
    created = DateTimeField(default=peewee_datetime.datetime.now)

    @classmethod
    def create(cls, **query):
        inst = cls(**query)
        inst.unique_id = f'group_{get_base_58_string()}'
        inst.save(force_insert=True)
        return inst

    def get_name(self, lang):
        return self.name.get(lang, self.name['en'])


class Tool(_Model):
    class Meta:
        db_table = 'tools'

    name = BinaryJSONField(default=dict)
    order = IntegerField(default=0)
    need_weight = BooleanField(default=True)
    created = DateTimeField(default=peewee_datetime.datetime.now)

    def get_name(self, lang):
        return self.name.get(lang, self.name['en'])


class Exercise(_Model):
    class Meta:
        db_table = 'exercises'

    unique_id = CharField(unique=True, index=True)
    name = BinaryJSONField(default=dict)
    group = ForeignKeyField(MuscleGroup)
    tool = ForeignKeyField(Tool)
    config = BinaryJSONField(default=dict)
    order = IntegerField(default=0)
    media = BinaryJSONField(default=dict)  # {'male' : ['path'], 'female' : ['path']}
    description = BinaryJSONField(default=dict)
    created = DateTimeField(default=peewee_datetime.datetime.now)

    @classmethod
    def create(cls, **query):
        inst = cls(**query)
        inst.unique_id = f'exercise_{get_base_58_string()}'
        inst.save(force_insert=True)
        return inst

    def get_name(self, lang):
        return self.name.get(lang, self.name['en'])


class ProgramGroup(_Model):
    class Meta:
        db_table = 'program_groups'

    name = BinaryJSONField(default=dict)
    order = IntegerField(default=0)
    days_between_trainings = IntegerField(default=1)
    created = DateTimeField(default=peewee_datetime.datetime.now)


class ProgramLevel(_Model):
    class Meta:
        db_table = 'program_levels'

    name = BinaryJSONField(default=dict)
    order = IntegerField(default=0)
    created = DateTimeField(default=peewee_datetime.datetime.now)


class Program(_Model):
    class Meta:
        db_table = 'programs'

    group = ForeignKeyField(ProgramGroup)
    level = ForeignKeyField(ProgramLevel)
    description = BinaryJSONField(default=dict)
    exercises = BinaryJSONField(default=list)
    created = DateTimeField(default=peewee_datetime.datetime.now)


class Subscription(_Model):
    class Meta:
        db_table = 'subscriptions'

    unique_id = CharField(unique=True, index=True)
    name = BinaryJSONField(default=dict)
    price = DoubleField()
    value = IntegerField(default=SubscriptionValue.Low)
    description = BinaryJSONField(default=dict)
    extra_data = BinaryJSONField(default=dict)

    @classmethod
    def create(cls, **query):
        inst = cls(**query)
        inst.unique_id = f'subscription_{get_base_58_string()}'
        inst.save(force_insert=True)
        return inst


class User(_Model):
    class Meta:
        db_table = 'users'

    tg_account = CharField(unique=True, index=True, null=True)
    name = CharField(null=True)
    chat_id = CharField(unique=True, index=True)
    lang = CharField(default=DEFAULT_LANGUAGE)
    extra_data = BinaryJSONField(default=dict)
    program = ForeignKeyField(Program, null=True)
    subscription = ForeignKeyField(Subscription, null=True)
    created = DateTimeField(default=peewee_datetime.datetime.now)
    last_interacted = DateTimeField(default=peewee_datetime.datetime.now)
    subscription_end = DateTimeField(default=peewee_datetime.datetime.now() + peewee_datetime.timedelta(days=7))


class Training(_Model):
    class Meta:
        db_table = 'trainings'

    user = ForeignKeyField(User)
    created = DateTimeField(default=peewee_datetime.datetime.now)
    end = DateTimeField(null=True)


class Set(_Model):
    class Meta:
        db_table = 'sets'

    user = ForeignKeyField(User)
    exercise = ForeignKeyField(Exercise)
    training = ForeignKeyField(Training)
    data = BinaryJSONField(default=list)  # [{'weight': '', 'reps': '', 'timestamp': float}]
    created = DateTimeField(default=peewee_datetime.datetime.now)
    end = DateTimeField(null=True)


CREATING_LIST = [
    MuscleGroup,
    Tool,
    Exercise,
    ProgramGroup,
    ProgramLevel,
    Program,
    Subscription,
    User,
    Set,
    Training
]


def init_db():
    try:
        db.connect()
        db.drop_tables(CREATING_LIST)
        print("tables dropped")
        db.create_tables(CREATING_LIST)
        print("tables created")
        db.close()
    except:
        db.rollback()
        raise

# if __name__ == '__main__':
#     init_db()
