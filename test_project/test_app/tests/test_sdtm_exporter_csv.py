import csv

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
from test_project.test_app.tests.example import (
    DOMAIN,
    EXPORT_DISCLAIMER_TEXT,
    STUDY_NAME,
    SUBJECT_ID,
    ExampleSDTMExporter,
    Variables,
)

EXPECTED_CSV_CONTENT = [
    [EXPORT_DISCLAIMER_TEXT],
    [
        Variables.STUDY_NAME.oid,
        Variables.DOMAIN.oid,
        Variables.SUBJECT_ID.oid,
        Variables.VALUE.oid,
        Variables.UNIT.oid,
        Variables.TEST_CONSTANT.oid,
    ],
    [STUDY_NAME, DOMAIN, SUBJECT_ID, "Yes", "", "0"],
    [STUDY_NAME, DOMAIN, SUBJECT_ID, "10", "kg", "0"],
]

EXPECTED_SINGLE_ROW_CSV = [
    [EXPORT_DISCLAIMER_TEXT],
    ["Name", "Value", "Description"],
    [
        Variables.STUDY_NAME.oid,
        STUDY_NAME,
        Variables.STUDY_NAME.name,
    ],
    [
        Variables.DOMAIN.oid,
        DOMAIN,
        Variables.DOMAIN.name,
    ],
    [
        Variables.SUBJECT_ID.oid,
        SUBJECT_ID,
        Variables.SUBJECT_ID.name,
    ],
    [
        Variables.VALUE.oid,
        "Yes",
        Variables.VALUE.name,
    ],
    [
        Variables.UNIT.oid,
        "",
        Variables.UNIT.name,
    ],
    [Variables.TEST_CONSTANT.oid, "0", Variables.TEST_CONSTANT.name],
]


@pytest.fixture(scope="session")
def csv_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "export.csv"


@pytest.mark.django_db
class TestSDTMCSVExporter:
    def test_export_to_csv(self, csv_file):
        study = G(Study, name=STUDY_NAME)
        participant = G(Participant, study=study, subject_id=SUBJECT_ID)
        input1 = G(
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

        with open(csv_file, "w") as f:
            exporter.export_to_csv(f)

        with open(csv_file) as f:
            reader = list(csv.reader(f))
            assert len(reader) == len(EXPECTED_CSV_CONTENT)
            assert set(",".join(r) for r in reader) == set(
                ",".join(r) for r in EXPECTED_CSV_CONTENT
            )

        with open(csv_file, "w") as f:

            # transposing two rows should throw an error
            with pytest.raises(ValueError):
                exporter.export_to_csv(
                    f, subtree_node=None, options={"transpose": True}
                )

        with open(csv_file, "w") as f:
            exporter.export_to_csv(f, subtree_node=input1, options={"transpose": True})

        with open(csv_file) as f:
            reader = csv.reader(f)

            assert list(reader) == EXPECTED_SINGLE_ROW_CSV
