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
from .example import (
    EXPECTED_CSV_CONTENT,
    EXPECTED_DATA,
    EXPECTED_SINGLE_ROW_CSV,
    STUDY_NAME,
    SUBJECT_ID,
    ExampleSDTMExporter,
)


@pytest.fixture(scope="session")
def csv_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "export.csv"


@pytest.mark.django_db
class TestSDTMCSVExporter:
    def test_visitor(self, csv_file):
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
            value="10.0",
            unit=G(Unit, unit="kg"),
            question=G(Question),
        )

        exporter = ExampleSDTMExporter(study)
        exported_data = exporter.export().to_dict("list")

        assert set(exported_data.keys()) == set(EXPECTED_DATA.keys())
        for k, values in exported_data.items():
            assert sorted(values, key=str) == sorted(EXPECTED_DATA[k], key=str)

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
