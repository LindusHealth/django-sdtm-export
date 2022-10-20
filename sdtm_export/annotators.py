from pandas import DataFrame

from .sdtm_exporter import InvalidConfigurationError, SDTMExporterBase


class Annotator:
    header = None

    def annotate(self, sdtm_exporter: SDTMExporterBase, data: DataFrame):
        raise NotImplementedError


class SequenceAnnotator(Annotator):
    """
    This annotator adds a new column to the data named "SEQUENCE_NUMBER"
    which uses the sorted by keys as grouping fields to cumulatively
    count the order in which the row displays.
    It can act as a unique ID if two rows are otherwise the same.

    For example:

    | SUBJECT_ID | VALUE |
    | ---- | -- |
    | s001 | 10 |
    | s001 | 20 |
    | s002 | 10 |

    becomes

    | SUBJECT_ID | VALUE | SEQUENCE_NUMBER |
    | ---- | -- | - |
    | s001 | 10 | 1 |
    | s001 | 20 | 2 |
    | s002 | 10 | 1 |
    """

    header = "SEQUENCE_NUMBER"

    def __init__(self, group_by=None):
        self.group_by = group_by

    def annotate(self, sdtm_exporter: SDTMExporterBase, data: DataFrame):
        group_by = self.group_by or sdtm_exporter.sort_by
        if getattr(sdtm_exporter.variables, self.header, None):
            data[sdtm_exporter.variables[self.header].oid] = (
                data.groupby(group_by).cumcount() + 1
            ).astype(str)
        else:
            raise InvalidConfigurationError("a header must be set on the annotator")
