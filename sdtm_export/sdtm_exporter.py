from collections import defaultdict
from collections.abc import Iterable
from typing import Any, Dict, List, Optional
import csv
import re

from django.db import models

from pandas import DataFrame


class MissingVisitorError(Exception):
    pass


class InvalidAttributeError(Exception):
    pass


class InvalidConfigurationError(Exception):
    pass


class SDTMExporterBase:
    """
    This is a base class for exporting data in SDTM format.

    Configuring:
    -------------

    To use this exporter, subclass it and set the following attributes

    `nodes`:
        An ordered list of all nodes to be included in the export.

        Each node should be specified as a tuple with three values:
        - The node class. Typically a model class, but any class is allowed
        - The child accessor (either a function or an attribute name string)
                May return an iterator or a single object.
                None for a leaf node
        - The parent accessor (either a function or an attribute name string)
                Must return a single object (not an iterator)
                None for the root node

        For example:
            nodes = [
                (Study, 'participants', None),
                (Participant, 'lab_results', 'study'),
                (LabResult, 'lab_test', 'participant),
                (LabTest, None, get_lab_result_for_lab_test),
            ]

        For each node type a visitor must be defined which returns the data to
        be exported from that node. The name convention for these visitors is
        snake case, for example:

            def visit_lab_result(self, lab_result):
                return {'value': lab_result.value}

    `variables`:
        An enum containing all the variables included in the export
        Their order of definition is the order in which they will appear in a CSV
        export.

    `constants`:
        Constant variables here which will be added to each row.
        These definitions will take precedence over any values returned
        by visiting an individual node.

    `csv_export_disclaimer_text`:
        Text to be added to the top of CSV exports. The default disclaimer can be
        overridden, or this can be set to None for no disclaimer to be included.

    `domain`:
        Required. A domain string, e.g. "AE".

    `domain_variable`:
        Required. Member of `variables` which corresponds to the domain variable.

    `label`
        A label string, e.g. "Adverse Events" (required for Dataset-JSON only)

    `sort_by`:
        member of `variables` or a list of members of `variables` to sort the output data
        by.

    `sort_order`:
        'asc' or 'desc' (or a list of 'asc' or 'desc'). Default: 'asc'

    Exporting:
    -----------

    In order to export data following the structure configured above, there are two options

    `export`:
        This method returns the data in a pandas DataFrame where the keys are members of
        `variables`

        Parameters:
            - `subtree_node`:
                If provided, only export the "sub tree" from this node
                downwards. For example, if our node structure is
                    Study -> Participant -> Lab Result
                and we only want to export the lab results for one specific
                participant we could call
                    exporter.export(participant)
                and only this participant's rows would be exported

    `export_to_csv`:
        Parameters:
            - `file`: file object to write to
            - `subtree_node`: See above (optional)
            - `options`: (optional)
                A dictionary of export options. Currently supported options are:
                    - transpose: boolean ('csv' only)
                        If true, transpose a single row being exported so that the
                        first column is the variable names, the second column is the
                        value and the third column is a description of the variable

                        Meant to be used in conjunction with `subtree_node`. This option
                        will throw an error if more than one row is being exported

    `export_to_json`:
        Example output
        "clinicalData": {
            "studyOID": "bhpYrydVzN9bvESQn5J8Vc",
            "metaDataVersionOID": "xxx",
            "itemGroupData": {
                "IG.AE": {
                    "records": 2,
                    "name": "AE",
                    "label": "Adverse Events",
                    "items": [
                        {
                            "OID": "IT.AESEQ",
                            "name": "AESEQ",
                            "label": "Adverse Event Sequence",
                            "type": "integer",
                        },
                        {
                            "OID": "IT.STUDYID",
                            "name": "STUDYID",
                            "label": "Study Identifier",
                            "type": "string",
                            "length": 22
                        },
                        {
                            "OID": "IT.AETERM",
                            "name": "AETERM",
                            "label": "Adverse Event Term",
                            "type": "string"
                        },
                        {
                            "OID": "IT.AESER",
                            "name": "AESER",
                            "label": "Is Adverse Event Serious",
                            "type": "string",
                            "length": 1,
                        },
                        ...
                    ]
                    "itemData": [
                        [1, "MyStudy", "headache", "N"],
                        [2, "MyStudy", "allergic reaction", "Y"],
                    ]
                }
            }

        },
        "referenceData": {
            "studyOID": "xxx",
            "metaDataVersionOID": "xxx",
            "itemGroupData": { ... }
        }

    """

    nodes = []
    variables = None

    constants = {}

    domain_variable = None
    domain = None
    label = None

    sort_by = None
    sort_order = None
    annotators = None

    def get_study_id(self):
        study = self.get_ancestor("Study")
        return study.id if study else None

    csv_export_disclaimer_text = (
        "These results are preliminary pending validation and "
        + "database lock. Don’t use this data for any public facing materials or to "
        + "make final assessments on the efficacy of the treatment being investigated."
    )

    def __init__(self, root):
        self.root = root
        self._initialize_node_structure()
        self._initialize_node_cache()
        self._initialize_visitor_names()

    def _initialize_node_structure(self):
        # TODO: Maybe some assertions about order and types?
        self._node_structure = {
            node.__name__: {"child": child, "parent": parent}
            for node, child, parent in self.nodes
        }

    def _initialize_node_cache(self):
        self._node_cache = {node.__name__: None for node, _, _ in self.nodes}
        self._node_cache[self.root.__class__.__name__] = self.root

    def _initialize_visitor_names(self):
        to_snake_case = re.compile(r"(?<!^)(?=[A-Z])")
        names = [node.__name__ for node, _, _ in self.nodes]
        self._visitor_names = {
            name: f"visit_{to_snake_case.sub('_', name).lower()}" for name in names
        }

    def _update_node_cache(self, node):
        self._node_cache[node.__class__.__name__] = node

    def get_ancestor(self, node):
        if isinstance(node, str):
            key = node
        else:
            key = node.__name__
        return self._node_cache[key]

    def _visit_node(self, node) -> Dict[str, str]:
        self._update_node_cache(node)
        visitor_name = self._visitor_names[node.__class__.__name__]
        try:
            accessor = getattr(self, visitor_name)
        except AttributeError:
            raise MissingVisitorError(visitor_name)

        return accessor(node)

    def _is_node_leaf(self, node) -> bool:
        return self._node_structure[node.__class__.__name__]["child"] is None

    def _evaluate_attribute(self, attr, node):
        if isinstance(attr, str):
            value = getattr(node, attr)
            if isinstance(value, models.Manager):
                value = value.all()
        elif callable(attr):
            value = attr(node)
        else:
            raise InvalidAttributeError()

        return value

    def _get_children(self, node) -> List:
        child_attr = self._node_structure[node.__class__.__name__]["child"]
        if child_attr is None:
            return []
        value = self._evaluate_attribute(child_attr, node)
        if isinstance(value, Iterable):
            return value
        if value is None:
            return []
        return [value]

    def _get_parent(self, node) -> Optional[Any]:
        parent_attr = self._node_structure[node.__class__.__name__]["parent"]
        if parent_attr is None:
            return None
        value = self._evaluate_attribute(parent_attr, node)
        if isinstance(value, Iterable):
            raise InvalidAttributeError()
        return value

    def export(self, subtree_node=None) -> DataFrame:
        # Validate configuration
        if not self.domain or not self.domain_variable:
            raise InvalidConfigurationError("domain and domain_variable must be set")

        if subtree_node:
            data = self._export_subtree(subtree_node)
        else:
            data = self._export(self.root)

        data = DataFrame(data)
        return self._post_process(data)

    def _export(self, node, extra_data=None) -> Dict[str, List[str]]:
        """
        Parameters: A node (i.e. study, survey, response, etc.)
        Returns:
          A dictionary representation of an exported spreadsheet
          for this node: {header: [row items]}

        If the node has no children, this method simply visits the
        node and returns the resulting data as a single row. If the
        node does have children, this method collects all the exported
        data for the children and then adds the results of visiting the
        node as a new set of columns to all the rows.
        """
        node_data = self._visit_node(node)
        if extra_data:
            node_data = {**extra_data, **node_data}
        if self._is_node_leaf(node):
            return {k: [v] for k, v in node_data.items()}

        children = self._get_children(node)
        child_data, row_count = self._export_list(children)
        if row_count is not None:
            for k, v in node_data.items():
                child_data[k] = [v] * row_count

        return child_data

    def _export_list(self, nodes: List) -> Dict[str, List[str]]:
        """
        Parameters: A list of nodes (i.e. surveys, responses, etc.)
        Returns: A tuple with...
          - A defaultdict(list) with all joined exported data from the nodes
          - The number of rows that each value in the dict has
        Throws:
          A ValueError if two dict keys (headers) have a different number
          of rows beneath them

        Note - This method does not handle the case where two siblings return
        different data, e.g. one question on a survey returns VSLOC (measurement
        location) and another doesn't. It will need to extended so that None is
        populated in missing fields for cases like this
        """
        data = defaultdict(list)

        for node in nodes:
            node_data = self._export(node)
            for k, v in node_data.items():
                data[k].extend(v)

        row_count = None
        for v in data.values():
            if row_count is None:
                row_count = len(v)
            elif row_count != len(v):
                raise ValueError("Sibling nodes have differing row counts")

        return data, row_count

    def _export_subtree(self, node):
        """
        Parameters: A node (i.e. study, survey, response, etc.)
        Returns:
          A dictionary of an exportable data for the subtree represented
          by this node and all of it's children. E.g. if a single lab
          result is passed, the dictionary will contain only data
          related to that one lab result
        """
        # In order to ensure that attributes on the visitor are properly
        # set, we still need to visit nodes in the order of their depth.

        # Start by building data from the root to the current exported node
        path_to_root = []
        cur = self._get_parent(node)
        if cur is None:
            raise ValueError("Cannot export subtree for a root node")

        while cur:
            path_to_root.append(cur)
            cur = self._get_parent(cur)

        # Confirm that the subtree node matches this exporter's root
        if self.root != path_to_root[-1]:
            raise ValueError("Subtree export doesn't match export visitor root")

        # Reverse the path to the root to start from the top of the tree
        parent_data = dict()
        for n in reversed(path_to_root):
            parent_data = {**self._visit_node(n), **parent_data}

        return self._export(node, parent_data)

    def _post_process(self, data: DataFrame):
        self._add_domain(data)
        self._add_constants(data)
        self._add_missing_columns(data)
        self._sort(data)
        self._annotate(data)
        # Order columns properly
        return data[list([v.oid for v in self.variables])]

    def _sort(self, data: DataFrame):
        if self.sort_by:
            order = (
                self.sort_order != "desc"
                if not isinstance(self.sort_order, list)
                else [o != "desc" for o in self.sort_order]
            )
            data.sort_values(self.sort_by, ascending=order, inplace=True)

    def _add_domain(self, data: DataFrame):
        data[self.domain_variable] = self.domain

    def _add_constants(self, data: DataFrame):
        for key, value in self.constants.items():
            data[key] = value

    def _add_missing_columns(self, data: DataFrame):
        for variable in self.variables:
            if variable.oid not in data:
                data[variable.oid] = ""

    def _annotate(self, data: DataFrame):
        if self.annotators:
            if not self.sort_by:
                raise InvalidConfigurationError("sort by must be set")

            if isinstance(self.annotators, list):
                for annotator in self.annotators:
                    annotator.annotate(self, data)
            else:
                self.annotators.annotate(self, data)

    def export_to_csv(self, file, subtree_node=None, options={}):
        transpose = options.get("transpose", False)
        if transpose:
            self._export_to_csv_single_row_transposed(file, subtree_node)
        else:
            self._export_to_csv(file, subtree_node)

    def _write_csv_disclaimer(self, file):
        writer = csv.writer(file)
        if self.csv_export_disclaimer_text:
            writer.writerow([self.csv_export_disclaimer_text])
        return writer

    def _export_to_csv(self, file, subtree_node=None):
        self._write_csv_disclaimer(file)

        headers = [h.oid for h in self.variables]

        data = self.export(subtree_node)

        data.to_csv(file, header=headers, index=False)

    def export_to_json(self, subtree_node=None):
        if self.label is None:
            raise InvalidConfigurationError(
                "label attribute is required for json export"
            )

        data = self.export(subtree_node)


        # ensure the columns are in the proper order
        data = data[[v.oid for v in self.variables]]

        return {
            "clinicalData": {
                "studyOID": self.get_study_id(),
                "metaDataVersionOID": self.get_study_id(),
                "itemGroupData": {
                    "IG."
                    + self.domain: {
                        "itemData": data.values.tolist(),
                        "name": self.domain,
                        "label": self.label,
                        "records": len(data.index),
                        "items": [
                            {
                                "OID": "IT." + str(v.oid),
                                "name": v._name_,
                                "label": v.cdisc_label,
                                "type": v.type,
                                "length": v.length,
                            }
                            for v in self.variables
                        ],
                    },
                },
            }
        }

    def _export_to_csv_single_row_transposed(self, file, subtree_node=None):
        """
        For single row exports we may want to change the CSV format.

        Rather than:
            Header1, Header 2, ...
            value1, value2, ...

        This method exports in the format:
            Name,    Value,  Description
            Header1, value1, This is the first header
            Header2,
        """
        writer = self._write_csv_disclaimer(file)

        data = self.export(subtree_node)
        if len(data) != 1:
            raise ValueError("Can only transpose an export of exactly one row")

        # TODO: Support better variable descriptions than just
        # the name
        writer.writerow(["Name", "Value", "Description"])
        writer.writerows([(h.oid, data[h.oid][0], h.name) for h in self.variables])
