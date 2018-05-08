from peewee import *
import datetime

# create a peewee database instance -- our models will use this database to
# persist information
psql_db = PostgresqlDatabase("auditreader_db", user="student")
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
    owner = ForeignKeyField(User, backref='directories',null=True)
    path = CharField(unique=True)
    inode = IntegerField(unique=True)
    parent_path = ForeignKeyField('self', backref='children')
    size = BigIntegerField()
    time_update = DateTimeField(default=datetime.datetime.now)

# the file system event model
class Event(BaseModel):
    id = CharField(unique=True)
    file_name = CharField()
    file_inode = IntegerField()
    directory = ForeignKeyField(Directory, backref='events')
    user = ForeignKeyField(User, backref='events')
    time = DateTimeField(default=datetime.datetime.now)
    size_directory = BigIntegerField()


def create_tables():
    psql_db.create_tables([User, Directory, Event])