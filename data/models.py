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
    state = models.IntegerField(default=0)
    pill = models.ForeignKey(Pill, blank=True, null=True, default=None)

    @classmethod
    def get_state(cls, chat_id, user_id):
        try:
            return cls.objects.get(chat_id=chat_id, user_id=user_id)
        except cls.DoesNotExist:
            s = cls(chat_id=chat_id, user_id=user_id, state=0)
            s.save()
            return s
