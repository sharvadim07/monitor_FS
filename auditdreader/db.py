from peewee import *
import datetime

# create a peewee database instance -- our models will use this database to
# persist information
psql_db = PostgresqlDatabase("auditreader_db", user="root", password = "123")
psql_db.connect()

# model definitions -- the standard "pattern" is to define a base model class
# that specifies which database to use.  then, any subclasses will automatically
# use the correct storage.
class BaseModel(Model):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = psql_db

# the user model specifies its fields (or columns) declaratively
class User(BaseModel):
    username = CharField(unique=True)
    uid = IntegerField(unique=True)

# the directory model
class Directory(BaseModel):
    owner = ForeignKeyField(User, backref = 'directories', null = True)
    name = CharField(null=True)
    inode = IntegerField(unique = True)
    parent = ForeignKeyField('self', backref = 'children', null=True)
    size = BigIntegerField(default=0)
    time_update = DateTimeField(default=datetime.datetime.now)

# the file model
class File(BaseModel):
    owner = ForeignKeyField(User, backref = 'files', null = True)
    name = CharField(null = True)
    inode = IntegerField(unique = True)
    parent = ForeignKeyField(Directory, backref = 'children', null = True)
    size = BigIntegerField(default = 0)
    time_update = DateTimeField(default = datetime.datetime.now)

# the file system event model
class Event(BaseModel):
    id = CharField(unique = True)
    file = ForeignKeyField(File, backref = 'events')
    directory = ForeignKeyField(Directory, backref = 'events')
    user = ForeignKeyField(User, backref = 'events')
    time = DateTimeField(default = datetime.datetime.now)
    size = BigIntegerField()


def create_tables():
    # Drop the table and re-create it.
    psql_db.drop_tables([User, File, Directory, Event])
    psql_db.create_tables([User, File, Directory, Event])
