import sys
import datetime

try:
    from django.db import models
except Exception as e:
    print("There was an error loading django modules. Do you have django installed?")
    raise e
    sys.exit()

class Pill(models.Model):
    chat_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    name = models.CharField(max_length=60)

    def add_time_from_re_match(self, match):
        self.add_time(*match.group(1, 2))

    def add_time(self, hour, minute):
        t = datetime.time(int(hour), int(minute))
        Time(pill=self, time=t).save()

class WeekDaysRepetion(models.Model):
    pill = models.ForeignKey(Pill, related_name="wdays")
    day = models.IntegerField()

    def remove(self):
        return self.delete(keep_parents=True)

class RepeatEveryDay(models.Model):
    pill = models.OneToOneField(Pill, related_name="everyday")

class RepeatEveryNthDay(models.Model):
    pill = models.OneToOneField(Pill, related_name="everynday")
    n = models.IntegerField()

class Time(models.Model):
    pill = models.ForeignKey(Pill, related_name="times")
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

    def clean(self):
        return self.delete(keep_parents=True)
