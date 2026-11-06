from pathlib import Path
from zipfile import ZipFile


def write_ods(path: Path, rows: str) -> None:
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
 <office:body><office:spreadsheet><table:table table:name="Sheet1">
  {rows}
 </table:table></office:spreadsheet></office:body>
</office:document-content>"""
    with ZipFile(path, "w") as archive:
        archive.writestr("content.xml", content)
