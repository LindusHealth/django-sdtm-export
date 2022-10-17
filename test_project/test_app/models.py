from django.db import models

from enumfields import Enum, EnumField


class Study(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "studies"

    def __str__(self):
        return self.name


class Participant(models.Model):
    subject_id = models.CharField(max_length=255)
    study = models.ForeignKey(
        Study, related_name="participants", on_delete=models.CASCADE
    )


class Question(models.Model):
    question = models.CharField(max_length=255)


class Unit(models.Model):
    unit = models.CharField(max_length=255)


class InputType(Enum):
    NUMBER = "NUMBER"
    NUMBER_WITH_UNIT = "NUMBER_WITH_UNIT"
    DATE = "DATE"
    DATETIME = "DATETIME"
    STRING = "STRING"
    STRING_LIST = "STRING_LIST"
    BOOLEAN = "BOOLEAN"
    OBJECT = "OBJECT"


class Input(models.Model):
    participant = models.ForeignKey(
        Participant, related_name="inputs", on_delete=models.CASCADE
    )
    type = EnumField(InputType, max_length=31)
    question = models.ForeignKey(
        Question, related_name="inputs", on_delete=models.CASCADE
    )

    unit = models.ForeignKey(Unit, null=True, on_delete=models.CASCADE)
    value = models.TextField(null=True)
