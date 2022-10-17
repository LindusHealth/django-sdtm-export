# django-sdtm-export

> :warning: **_This package is still under construction!_**

**django-sdtm-export** is a library which allows [Django framework](https://www.djangoproject.com/) users to define simple and declarative classes to export clinical model instances to a CSV or Dataset-JSON file while adhering to [CDISC SDTM guidelines](https://www.cdisc.org/standards/foundational/sdtm).

<p align="center">
    <img width= "300" height="300" src="https://user-images.githubusercontent.com/5873158/196236868-02ab6b3f-537e-4460-b213-82cc5085ca57.png" /></p>

_<p align="center">Our logo, generated by Dall-E (prompt: "a python caduceus in cyberspace doing data science")</p>_

## Requirements

- Python 3.8 or later
- Django 3.2 or later

## Example

Imagine a model structure for collecting information about concomitant medications like so

```python

class Study(models.Model):
    name = models.CharField(max_length=255)


class Participant(models.Model):
    study = models.ForeignKey(
        Study,
        on_delete=models.PROTECT,
        related_name="participants",
    )
    subject_id = models.CharField(max_length=255)

class ConcomitantMedication(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.PROTECT,
        related_name="concomitant_medications",
    )

    name = models.CharField(max_length=255)
    dose = models.CharField(max_length=63)
    unit = models.CharField(max_length=63)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

```

In order to export the CM domain from these models, we first define the variables to include and an `SDTMExporter` for the domain. This exporter will include how each variable is collected from each model with a series of `visit` methods

```python

from django_sdtm_exporter import SDTMExporterBase

class Variables(Enum):
    STUDY_ID = "STUDYID"
    DOMAIN = "DOMAIN"
    SUBJECT_ID = "USUBJID"
    SEQUENCE_NUMBER = "CMSEQ"
    TREATMENT_NAME = "CMTRT"
    DOSE = "CMDOSE"
    DOSE_UNIT = "CMDOSU"
    START_DATE = "CMSTDTC"
    END_DATE = "CMENDTC"


class ConcomitantMedicationSDTMExporter(SDTMExporterBase):

    nodes = [
        (Study, "participants", None),
        (Participant, "concomitant_medications", "study"),
        (ConcomitantMedication, None, "participant"),
    ]

    variables = Variables

    domain_variable = Variables.DOMAIN
    domain = "CM"
    label = "Concomitant Medications"

    def visit_study(self, study):
        return {Variables.STUDY_ID: study.name}

    def visit_participant(self, participant):
        return {Variables.SUBJECT_ID: participant.subject_id}

    def visit_concomitant_medication(self, concomitant_medication):
        return {
            Variables.TREATMENT_NAME: concomitant_medication.name,
            Variables.CATEGORY: concomitant_medication.category,
            Variables.INDICATION: concomitant_medication.indication,
            Variables.DOSE: concomitant_medication.dose,
            Variables.DOSE_UNIT: concomitant_medication.unit,
            Variables.START_DATE: concomitant_medication.start_date,
            Variables.END_DATE: concomitant_medication.end_date,
        }

```

And you're ready to export! You can do the following:

```python

>>> from exporters.cm import ConcomitantMedicationSDTMExporter
>>> from apps.study.models import Study
>>> study = Study.objects.get()
>>> exporter = ConcomitantMedicationSDTMExporter(study)
>>> exporter.export_to_json('cm.json')

```

### A note about Exporter Implementation

The content of an exporter implementation can effectively be determined from `define.xml`. Future extensions of this project could explore importing `define.xml` to generate all the exporters required.

## Getting started

Install using your favourite Python package manager, e.g.:

```sh
poetry add django-sdtm-export
```

Add `sdtm_export` to your Django project's installed apps in `settings.py`:

```python
INSTALLED_APPS = [
    "...",
    "sdtm_export"
]
```

The `sdtm_export` package will then be available for import.

## License

Distributed under the MIT License. See `LICENSE` for more information.
