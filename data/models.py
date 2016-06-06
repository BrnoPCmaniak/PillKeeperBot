import sys

try:
    from django.db import models
except  Exception:
    print("There was an error loading django modules. Do you have django installed?")
    sys.exit()

class Pill(models.Model):
    chat_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    name = models.CharField(max_length=60)

class WeekDaysRepetion(models.Model):
    pill = models.ForeignKey(Pill)
    day = models.IntegerField()

class RepeatEveryDay(models.Model):
    pill = models.OneToOneField(Pill)

class RepeatEveryNthDay(models.Model):
    pill = models.OneToOneField(Pill)
    n = models.IntegerField()

class Time(models.Model):
    pill = models.ForeignKey(Pill)
    time = models.TimeField()
    last_done = models.DateField(auto_now=True)

class State(models.Model):
    chat_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    state = models.IntegerField()
