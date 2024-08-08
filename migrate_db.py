import logging
import sys

from peewee_migrate import Router
from playhouse.pool import PooledPostgresqlExtDatabase

from config import DB_CONFIG
from utils import Logger

fh = logging.StreamHandler(sys.stdout)
fh.setLevel(logging.DEBUG)
logger = Logger(fh, 'peewee_migrate')

db = PooledPostgresqlExtDatabase(**DB_CONFIG)
db.commit_select = True
db.autorollback = True

router = Router(db, logger=logger)

print(router.diff)
router.run()
