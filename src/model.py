import peewee as pw
from db_config import db


class Task(pw.Model):
    uuid = pw.CharField(primary_key=True)
    name = pw.CharField()
    start_time = pw.DateTimeField()
    end_time = pw.DateTimeField(null=True)
    name = pw.CharField()
    is_logged = pw.BooleanField()
    taskId = pw.IntegerField(null=True)
    projectId = pw.IntegerField(null=True)

    class Meta:
        database = db
        table_name = "tasks"


class LogHistory(pw.Model):
    uuid = pw.CharField(primary_key=True)

    class Meta:
        database = db
        table_name = "last_logged"


class HarvestClient(pw.Model):
    projectId = pw.IntegerField(primary_key=True)
    name = pw.CharField()

    class Meta:
        database = db
        table_name = "harvest_clients"


class HarvestProject(pw.Model):
    projectId = pw.IntegerField(primary_key=True)
    client = pw.ForeignKeyField(HarvestClient, backref="projects")
    name = pw.CharField()

    class Meta:
        database = db
        table_name = "harvest_projects"


class HarvestTask(pw.Model):
    taskId = pw.IntegerField(primary_key=True)
    project = pw.ForeignKeyField(HarvestProject, backref="tasks")
    client = pw.ForeignKeyField(HarvestClient, backref="tasks")
    name = pw.CharField()

    class Meta:
        database = db
        table_name = "harvest_tasks"


if __name__ == "__main__":
    db.connect()
    db.create_tables([HarvestClient, HarvestProject, HarvestTask])
