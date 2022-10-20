import pandas as pd

# TODO - grab this from CDISC library API instead
# https://mailchi.mp/cdisc/freemium

# The SDTMIG_v3.4.xlsx sheet can be found in the CDISC Library
# https://www.cdisc.org/members-only/cdisc-library-archives

if __name__ == "__main__":
    """
    This script grabs metadata from the SDTMIG_v3.4.xlsx sheet (assuming it is co-located)
    and prints out the results to help easy population of the BaseVariables export enums
    with oid, name, label, type, length.

    Example output for AE domain:

    ("STUDYID", "Study Identifier", "Char", "24")
    ("DOMAIN", "Domain Abbreviation", "Char", "200")
    ("USUBJID", "Unique Subject Identifier", "Char", "24")
    ("SPDEVID", "Sponsor Device Identifier", "Char", "200")
    ("AESEQ", "Sequence Number", "Num", "8")
    ("AEGRPID", "Group ID", "Char", "200")
    ("AEREFID", "Reference ID", "Char", "200")
    ("AESPID", "Sponsor-Defined Identifier", "Char", "200")
    ("AETERM", "Reported Term for the Adverse Event", "Char", "200")
    ("AEMODIFY", "Modified Reported Term", "Char", "200")
    ...
    """

    domain = "AE"  # Update to pull different domain
    vars = ["variable_name", "variable_label", "type"]

    df = pd.read_excel("SDTMIG_v3.4.xlsx", sheet_name="Variables")
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    vars = df[df["dataset_name"] == domain][vars]

    vars["length"] = 200  # Implementation guides max variable length
    vars.loc[vars["type"] == "Num", "length"] = 8
    vars.loc[vars["variable_name"].str.endswith("CD"), "length"] = 8
    vars.loc[vars["variable_name"].str.endswith("TEST"), "length"] = 40
    vars.loc[vars["variable_name"].str.endswith("PARM"), "length"] = 40
    vars.loc[vars["variable_name"].str.endswith("DECOD"), "length"] = 40
    vars.loc[vars["variable_name"].str.endswith("SUBJID"), "length"] = 24
    vars.loc[vars["variable_name"].str.endswith("STUDYID"), "length"] = 24

    for i, r in vars.iterrows():
        row_string = f"""("{r.variable_name}",\
 "{r.variable_label}", "{r.type}", "{r.length}")"""
        print(row_string)
