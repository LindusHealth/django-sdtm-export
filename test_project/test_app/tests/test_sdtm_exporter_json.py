from ddf import G
import pytest

from test_project.test_app.models import (
    Input,
    InputType,
    Participant,
    Question,
    Study,
    Unit,
)
from test_project.test_app.tests.example_sdtm_exporter import (
    STUDY_NAME,
    SUBJECT_ID,
    ExampleSDTMExporter,
)


@pytest.fixture()
def response():
    return {
        "clinicalData": {
            "studyOID": 333,
            "metaDataVersionOID": 333,
            "itemGroupData": {
                "IG.EXAMPLE": {
                    "itemData": [
                        ["Test Name", "EXAMPLE", "test-subject", "Yes", "", "0"],
                        ["Test Name", "EXAMPLE", "test-subject", "10", "kg", "0"],
                    ],
                    "name": "EXAMPLE",
                    "label": "Example",
                    "records": 2,
                    "items": [
                        {
                            "OID": "IT.STUDY_NAME",
                            "name": "STUDY_NAME",
                            "label": "Study Name",
                            "type": "Char",
                            "length": "200",
                        },
                        {
                            "OID": "IT.DOMAIN",
                            "name": "DOMAIN",
                            "label": "Domain",
                            "type": "Char",
                            "length": "200",
                        },
                        {
                            "OID": "IT.SUBJECT_ID",
                            "name": "SUBJECT_ID",
                            "label": "Subject Id",
                            "type": "Char",
                            "length": "24",
                        },
                        {
                            "OID": "IT.VALUE",
                            "name": "VALUE",
                            "label": "Value",
                            "type": "Char",
                            "length": "200",
                        },
                        {
                            "OID": "IT.UNIT",
                            "name": "UNIT",
                            "label": "Unit",
                            "type": "Char",
                            "length": "200",
                        },
                        {
                            "OID": "IT.CONST",
                            "name": "TEST_CONSTANT",
                            "label": "Test Constant",
                            "type": "Char",
                            "length": "200",
                        },
                    ],
                }
            },
        }
    }


@pytest.mark.django_db
class TestSDTMDatasetJSONExporter:
    def test_export_to_json(self, response):
        study = G(Study, name=STUDY_NAME, id=333)
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
        result = exporter.export_to_json()

        assert result == response
