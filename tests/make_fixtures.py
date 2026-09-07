#!/usr/bin/env python3
"""Generate synthetic ordinance PDFs that reproduce known failure modes.

These are NOT real ordinances. They exist so the pipeline can be exercised on a
fresh machine before the real corpus is in place, and so a regex change can be
regression-tested in seconds.
"""
import shutil
import textwrap
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent / "fixtures"
RAW = ROOT / "data" / "raw" / "2016"

CASES = {
    # Clean document, enactment date on the line AFTER the anchor.
    "Ordinance No. 0116-16.pdf": """
        REPUBLIC OF THE PHILIPPINES
        CITY OF DAVAO
        OFFICE OF THE SANGGUNIANG PANLUNGSOD
        18th City Council
        22nd Regular Session
        Series of 2016

        ORDINANCE NO. 0116-16

        AN ORDINANCE REGULATING THE OPERATION OF PUBLIC MARKETS IN DAVAO CITY.

        Be it ordained by the Sangguniang Panlungsod of Davao City that:
        SECTION 1. Title. This ordinance shall be known as the Public Market Code.
        SECTION 2. Coverage. All public markets in the city are covered.

        ENACTED,
        March 15, 2016.

        APPROVED:
        SARA Z. DUTERTE-CARPIO
        City Mayor
        March 22, 2016
    """,
    # Title cites an AMENDED ordinance: the classic false-positive source.
    "Ordinance No. 0118-16.pdf": """
        OFFICE OF THE SANGGUNIANG PANLUNGSOD
        18th City Council
        Series of 2016

        ORDINANCE NO. 0118-16

        AN ORDINANCE AMENDING ORDINANCE NO. 0234-15, SERIES OF 2015, OTHERWISE
        KNOWN AS THE DAVAO CITY TRAFFIC CODE, AND FOR OTHER PURPOSES.

        WHEREAS, Ordinance No. 0234-15 was approved on December 1, 2015;
        WHEREAS, amendments are necessary;

        SECTION 1. Section 4 is hereby amended to read as follows.

        ENACTED, April 5, 2016.
        APPROVED: April 12, 2016
        City Mayor
    """,
    # Approval date is a stamp below the signature block only.
    "Ordinance No. 0301-16.pdf": """
        OFFICE OF THE SANGGUNIANG PANLUNGSOD
        18th City Council
        Series of 2016

        ORDINANCE NO. 0301-16

        AN ORDINANCE APPROPRIATING FUNDS FOR BARANGAY ROAD REPAIR.

        ENACTED by the 18th City Council on its regular session held on June 7, 2016.

        ATTESTED:
        BERNARDO M. AL-AG
        City Vice-Mayor and Presiding Officer

        CITY MAYOR
        June 20, 2016
    """,
    # Archaic date phrasing plus a citation to a 1976 ordinance.
    "Ordinance No. 0512-16.pdf": """
        ORDINANCE NO. 0512-16
        Series of 2016

        AN ORDINANCE DECLARING AUGUST AS DAVAO HERITAGE MONTH.

        Pursuant to Ordinance No. 0123, Series of 1976, as amended.

        ENACTED this 9th day of August, 2016 at Davao City.
        APPROVED: August 19, 2016
        City Mayor
    """,
    # Genuine misfile: a 2010 ordinance sitting in the 2016 folder.
    "Ordinance No. 0230-10.pdf": """
        OFFICE OF THE SANGGUNIANG PANLUNGSOD
        16th City Council
        Series of 2010

        ORDINANCE NO. 0230-10

        AN ORDINANCE ESTABLISHING THE DAVAO CITY WATER ZONING PLAN.

        ENACTED, June 1, 2010.
        APPROVED: June 10, 2010
        City Mayor
    """,
    # Weak and contradictory: only a cited series year survives.
    "Ordinance No. 0135-16.pdf": """
        ORDINANCE NO. 0135-16

        AN ORDINANCE AMENDING SECTION 4 OF ORDINANCE NO. 0087-95, SERIES OF 1995.

        WHEREAS the 1995 ordinance is outdated;
        Be it ordained.
    """,
    # Duplicate ordinance number under a different filename.
    "Ord 0116-16 duplicate.pdf": """
        ORDINANCE NO. 0116-16
        Series of 2016
        AN ORDINANCE REGULATING THE OPERATION OF PUBLIC MARKETS IN DAVAO CITY.
        ENACTED, March 15, 2016.
        APPROVED: March 22, 2016
        City Mayor
    """,
}


def build() -> Path:
    shutil.rmtree(ROOT, ignore_errors=True)
    RAW.mkdir(parents=True)
    # The pipeline derives every path from its own location, so the fixture
    # tree gets its own copy of the script and therefore its own outputs.
    (ROOT / "src").mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).resolve().parent.parent / "src" / "ordinance_eda_pipeline.py",
                ROOT / "src" / "ordinance_eda_pipeline.py")
    for name, body in CASES.items():
        doc = fitz.open()
        page = doc.new_page()
        page.insert_textbox(fitz.Rect(50, 50, 545, 780),
                            textwrap.dedent(body).strip(), fontsize=9, fontname="helv")
        doc.save(str(RAW / name))
        doc.close()
    # Byte-identical duplicate.
    shutil.copy(RAW / "Ordinance No. 0116-16.pdf", RAW / "Ordinance No. 0116-16 (copy).pdf")
    # Image-only page, no text layer.
    doc = fitz.open()
    doc.new_page()
    doc.save(str(RAW / "Ordinance No. 0999-16.pdf"))
    doc.close()
    print(f"Wrote {len(list(RAW.glob('*.pdf')))} fixture PDF(s) to {RAW}")
    return ROOT


if __name__ == "__main__":
    build()
