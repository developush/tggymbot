import logging
from environs import Env


env = Env()
env.read_env()

with env.prefixed("APP_"):
    TZ = env.str("TIMEZONE", "Europe/Kiev")

    with env.prefixed("LOG_"):
        LOG_TO = env.str("TO")
        LOGGER = dict(level=logging.getLevelName(env.str("LEVEL", "INFO")),
                      formatter=logging.Formatter(
                          env.str("FORMAT",
                                  "%(asctime)s [%(thread)d:%(threadName)s] [%(levelname)s] - %(name)s:%(message)s"), ),
                      file='gymbuddybot.log',
                      peewee_file='peewee.log',
                      )

    with env.prefixed("DB_"):
        DB_CONFIG = dict(
            database=env.str("NAME"),
            user=env.str("USER"),
            password=env.str("PASSWORD"),
            host=env.str("HOST"),
            port=env.int("PORT"),
            max_connections=env.int("MAX_CONNECTIONS", 50),
            stale_timeout=env.int("STALE_TIMEOUT", 600),
            register_hstore=False,
            server_side_cursors=False
        )

    with env.prefixed("CELERY_"):
        CELERY = dict(BROKER=env.str("BROKER", "redis://127.0.0.1:6379"),
                      BACKEND=env.str("BACKEND", "redis://127.0.0.1:6379"))

    TOKEN = env.str('TOKEN')
    PAYMENT_TOKEN = env.str('PAYMENT_TOKEN')
    DEFAULT_LANGUAGE = env.str('DEFAULT_LANGUAGE', 'ru')
    BUTTONS_PER_MESSAGE = env.int('BUTTONS_PER_MESSAGE', 8)
    MAIN_PATH = env.str('MAIN_PATH', '/Users/kalishuk/GymBuddyBot/')
    WKHTMLTOPDF = env.str('WKHTMLTOPDF', '/usr/local/bin/wkhtmltopdf')
    CURRENCY = env.str('CURRENCY', 'USD')
    LAST_TRAININGS_NUM = env.int('LAST_TRAININGS_NUM', 5)

