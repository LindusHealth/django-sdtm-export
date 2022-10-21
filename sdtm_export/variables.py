from enum import Enum


class BaseVariables(Enum):
    def __new__(cls, oid, cdisc_label, type, length):
        """
        Base Variable class for CDISC Dataset-JSON export
        """
        obj = object.__new__(cls)
        obj.oid = oid
        obj.cdisc_label = cdisc_label
        obj.type = type
        obj.length = length

        return obj
