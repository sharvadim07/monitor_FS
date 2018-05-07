from peewee import *

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

# the user model specifies its fields (or columns) declaratively, like django
class User(BaseModel):
    username = CharField(unique=True)
    uid = IntegerField()

def create_tables():
    psql_db.create_tables([User])