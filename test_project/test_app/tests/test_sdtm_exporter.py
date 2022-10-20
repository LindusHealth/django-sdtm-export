
import csv
import pytest
from ddf import G
from sdtm_export.annotators import SequenceAnnotator
from sdtm_export.sdtm_exporter import SDTMExporterBase
from sdtm_export.variables import BaseVariables
from test_project.test_app.models import Input, InputType, Participant, Question, Study, Unit
from test_project.test_app.tests.example import DOMAIN, EXPORT_DISCLAIMER_TEXT, STUDY_NAME, SUBJECT_ID, ExampleSDTMExporter, Variables


STUDY_NAME = "Test Name"
DOMAIN = "EXAMPLE"
SUBJECT_ID = "test-subject"
EXPORT_DISCLAIMER_TEXT = "Test disclaimer"


class Variables(BaseVariables):
    STUDY_NAME = ("STUDY_NAME", "Study Name", "Char", "200")
    DOMAIN = ("DOMAIN", "Domain", "Char", "200")
    SUBJECT_ID = ("SUBJECT_ID", "Subject Id", "Char", "24")
    VALUE = ("VALUE", "Value", "Char", "200")
    UNIT = ("UNIT", "Unit", "Char", "200")
    TEST_CONSTANT = ("CONST", "Test Constant", "Char", "200")


class AnnotatedVariables(BaseVariables):
    STUDY_NAME = ("STUDY_NAME", "Study Name", "Char", "200")
    DOMAIN = ("DOMAIN", "Domain", "Char", "200")
    SUBJECT_ID = ("SUBJECT_ID", "Subject Id", "Char", "24")
    VALUE = ("VALUE", "Value", "Char", "200")
    UNIT = ("UNIT", "Unit", "Char", "200")
    TEST_CONSTANT = ("CONST", "Test Constant", "Char", "200")
    SEQUENCE_NUMBER = ("SEQUENCE_NUMBER", "Sequence Number", "Char", "200")


class ExampleSDTMExporter(SDTMExporterBase):
    nodes = [
        (Study, "participants", None),
        (Participant, "inputs", "study"),
        (Input, None, "participant"),
    ]
    constants = {Variables.TEST_CONSTANT.oid: "0"}
    variables = Variables

    csv_export_disclaimer_text = EXPORT_DISCLAIMER_TEXT

    domain_variable = Variables.DOMAIN.oid
    domain = "EXAMPLE"
    label = "Example"

    def visit_study(self, study):
        return {Variables.STUDY_NAME.oid: study.name}

    def visit_participant(self, participant):
        return {Variables.SUBJECT_ID.oid: participant.subject_id}

    def visit_input(self, input):
        if hasattr(input, "unit") and input.unit:
            unit = input.unit.unit
        else:
            unit = ""
        return {
            Variables.VALUE.oid: input.value,
            Variables.UNIT.oid: unit,
        }


class AnnotatedExampleSDTMExporter(ExampleSDTMExporter):
    variables = AnnotatedVariables

    constants = {AnnotatedVariables.TEST_CONSTANT.oid: "0"}

    domain_variable = AnnotatedVariables.DOMAIN.oid

    def visit_study(self, study):
        return {AnnotatedVariables.STUDY_NAME.oid: study.name}

    def visit_participant(self, participant):
        return {AnnotatedVariables.SUBJECT_ID.oid: participant.subject_id}

    def visit_input(self, input):
        if hasattr(input, "unit") and input.unit:
            unit = input.unit.unit
        else:
            unit = ""
        return {
            AnnotatedVariables.VALUE.oid: input.value,
            AnnotatedVariables.UNIT.oid: unit,
        }


@pytest.mark.django_db
class TestSDTMExporter:
    def test_export(self):

        EXPECTED_DATA = {
            Variables.STUDY_NAME.oid: [STUDY_NAME, STUDY_NAME],
            Variables.DOMAIN.oid: [DOMAIN, DOMAIN],
            Variables.SUBJECT_ID.oid: [SUBJECT_ID, SUBJECT_ID],
            Variables.VALUE.oid: ["Yes", "10"],
            Variables.UNIT.oid: ["", "kg"],
            Variables.TEST_CONSTANT.oid: ["0", "0"],
        }

        study = G(Study, name=STUDY_NAME)
        participant = G(Participant, study=study, subject_id=SUBJECT_ID)
        G(
            Input,
            participant=participant,
            type=InputType.STRING,
            value="Yes",
            question=G(Question),
        )
        G(
            Input,
            participant=participant,
            type=InputType.NUMBER_WITH_UNIT,
            value="10",
            unit=G(Unit, unit="kg"),
            question=G(Question),
        )

        exporter = ExampleSDTMExporter(study)
        exported_data = exporter.export().to_dict("list")

        assert set(exported_data.keys()) == set(EXPECTED_DATA.keys())
        for k, values in exported_data.items():
            assert sorted(values, key=str) == sorted(EXPECTED_DATA[k], key=str)

        # Using subtree export on the root should raise an error
        with pytest.raises(ValueError):
            exporter.export(study)

        study2 = G(Study, name="Second Study")

        participant2 = G(Participant, study=study2, subject_id="test2")
        input2 = G(
            Input,
            participant=participant2,
            type=InputType.STRING,
            value="Yes",
            question=G(Question),
        )

        # Trying to use an exporter for one study on another study's data
        # should raise an error
        with pytest.raises(ValueError):
            exporter.export(input2)

    def test_sorted_export(self):
        study = G(Study, name=STUDY_NAME)
        participant1 = G(Participant, study=study, subject_id="1")
        participant2 = G(Participant, study=study, subject_id="2")
        G(
            Input,
            participant=participant2,
            type=InputType.STRING,
            value="Maybe",
            question=G(Question),
        )
        G(
            Input,
            participant=participant2,
            type=InputType.STRING,
            value="No",
            question=G(Question),
        )
        G(
            Input,
            participant=participant1,
            type=InputType.STRING,
            value="Yes",
            question=G(Question),
        )

        row_one = [STUDY_NAME, DOMAIN, "2", "Maybe", "", "0"]
        row_two = [STUDY_NAME, DOMAIN, "2", "No", "", "0"]
        row_three = [STUDY_NAME, DOMAIN, "1", "Yes", "", "0"]

        exporter = ExampleSDTMExporter(study)
        exporter.sort_by = Variables.VALUE.oid

        data = exporter.export()

        assert (data.values[0] == row_one).all()
        assert (data.values[1] == row_two).all()
        assert (data.values[2] == row_three).all()

        exporter.sort_order = "desc"
        data = exporter.export()

        assert (data.values[0] == row_three).all()
        assert (data.values[1] == row_two).all()
        assert (data.values[2] == row_one).all()

        exporter.sort_by = [
            Variables.SUBJECT_ID.oid,
            Variables.VALUE.oid,
        ]
        exporter.sort_order = "asc"
        data = exporter.export()

        assert (data.values[0] == row_three).all()
        assert (data.values[1] == row_one).all()
        assert (data.values[2] == row_two).all()

        exporter.sort_order = ["asc", "desc"]
        data = exporter.export()

        assert (data.values[0] == row_three).all()
        assert (data.values[1] == row_two).all()
        assert (data.values[2] == row_one).all()

    def test_annotated_export(self):
        study = G(Study, name=STUDY_NAME)
        participant1 = G(Participant, study=study, subject_id="1")
        participant2 = G(Participant, study=study, subject_id="2")
        G(
            Input,
            participant=participant2,
            type=InputType.STRING,
            value="Maybe",
            question=G(Question),
        )
        G(
            Input,
            participant=participant2,
            type=InputType.STRING,
            value="No",
            question=G(Question),
        )
        G(
            Input,
            participant=participant1,
            type=InputType.STRING,
            value="Yes",
            question=G(Question),
        )

        row_one = [STUDY_NAME, DOMAIN, "2", "Maybe", "", "0", "1"]
        row_two = [STUDY_NAME, DOMAIN, "2", "No", "", "0", "2"]
        row_three = [STUDY_NAME, DOMAIN, "1", "Yes", "", "0", "1"]

        exporter = AnnotatedExampleSDTMExporter(study)
        exporter.sort_by = [AnnotatedVariables.SUBJECT_ID.oid]
        exporter.sort_order = "asc"
        exporter.annotators = SequenceAnnotator()
        data = exporter.export()

        assert (data.values[0] == row_three).all()
        assert (data.values[1] == row_one).all()
        assert (data.values[2] == row_two).all()
