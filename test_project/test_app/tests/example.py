from enum import Enum

from sdtm_export.sdtm_exporter import SDTMExporterBase
from sdtm_export.variables import BaseVariables
from test_project.test_app.models import Input, Participant, Study

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


class ExampleSDTMExporter(SDTMExporterBase):
    nodes = [
        (Study, "participants", None),
        (Participant, "inputs", "study"),
        (Input, None, "participant"),
    ]

    variables = Variables

    constants = {Variables.TEST_CONSTANT: "0.0"}

    csv_export_disclaimer_text = EXPORT_DISCLAIMER_TEXT

    domain_variable = Variables.DOMAIN
    domain = "EXAMPLE"
    label = "Example"

    def visit_study(self, study):
        return {Variables.STUDY_NAME: study.name}

    def visit_participant(self, participant):
        return {Variables.SUBJECT_ID: participant.subject_id}

    def visit_input(self, input):
        if hasattr(input, "unit") and input.unit:
            unit = input.unit.unit
        else:
            unit = ""
        return {Variables.VALUE: input.value, Variables.UNIT: unit}


EXPECTED_DATA = {
    Variables.STUDY_NAME: [STUDY_NAME, STUDY_NAME],
    Variables.DOMAIN: [DOMAIN, DOMAIN],
    Variables.SUBJECT_ID: [SUBJECT_ID, SUBJECT_ID],
    Variables.VALUE: ["Yes", "10.0"],
    Variables.UNIT: ["", "kg"],
    Variables.TEST_CONSTANT: ["0.0", "0.0"],
}

EXPECTED_CSV_CONTENT = [
    [EXPORT_DISCLAIMER_TEXT],
    [
        Variables.STUDY_NAME.value,
        Variables.DOMAIN.value,
        Variables.SUBJECT_ID.value,
        Variables.VALUE.value,
        Variables.UNIT.value,
        Variables.TEST_CONSTANT.value,
    ],
    [STUDY_NAME, DOMAIN, SUBJECT_ID, "Yes", "", "0.0"],
    [STUDY_NAME, DOMAIN, SUBJECT_ID, "10.0", "kg", "0.0"],
]

EXPECTED_SINGLE_ROW_CSV = [
    [EXPORT_DISCLAIMER_TEXT],
    ["Name", "Value", "Description"],
    [
        Variables.STUDY_NAME.value,
        STUDY_NAME,
        Variables.STUDY_NAME.name,
    ],
    [
        Variables.DOMAIN.value,
        DOMAIN,
        Variables.DOMAIN.name,
    ],
    [
        Variables.SUBJECT_ID.value,
        SUBJECT_ID,
        Variables.SUBJECT_ID.name,
    ],
    [
        Variables.VALUE.value,
        "Yes",
        Variables.VALUE.name,
    ],
    [
        Variables.UNIT.value,
        "",
        Variables.UNIT.name,
    ],
    [Variables.TEST_CONSTANT.value, "0.0", Variables.TEST_CONSTANT.name],
]
