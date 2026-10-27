"""Anonymise a real ETS6 project (.knxproj) into a test fixture.

The structure of the project stays as it is (topology, rooms, group addresses and
links, devices, application programs), everything that points to people or to the
installation is replaced or removed:

* free text (names, comments, descriptions of group addresses, rooms, devices,
  group ranges) is checked word by word: words from `vocabulary.txt` (generic
  home automation terms) stay, every other word is replaced by a made-up first name
* project name, GUID, user names, serial numbers, MAC address, keys, certificates,
  signatures and timestamps are replaced or dropped
* the application programs of the manufacturers are reduced to what xknxproject
  reads (communication objects, channels, module arguments, German texts)

Usage: python tools/fixtures/anonymize_project.py <input.knxproj> <output.knxproj>

The input has to be an unprotected export. tests/test_einfamilienhaus.py checks
the committed result for leftovers. After anonymising a new project, compare the
xknxproject output of input and output: only names (and the project id) may differ.
Then write the golden manifest with tools/reference (see CONTRIBUTING.md).
"""

from __future__ import annotations

import io
from pathlib import Path
import re
import sys
from xml.etree import ElementTree
import zipfile

HERE = Path(__file__).parent
VOCABULARY = HERE / "vocabulary.txt"
PROJECT_ID = "P-0C2D"
PROJECT_NAME = "Beispielhaus"
STAMP = (2026, 1, 1, 0, 0, 0)
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
# attributes of the project files that hold free text
TEXT_ATTRIBUTES = ("Name", "Comment", "Description", "Text", "FunctionText")
# attributes that identify a device, installation or moment
DROPPED_ATTRIBUTES = (
    "BCUKey",
    "ToolKey",
    "LoadedToolKey",
    "SequenceNumber",
    "SequenceNumberTimestamp",
    "MACAddress",
    "LoadedImage",
    "CheckSums",
    "LastModified",
    "LastDownload",
    "ProjectStart",
)
PSEUDONYMS = (
    "Anna",
    "Ben",
    "Clara",
    "David",
    "Emma",
    "Felix",
    "Greta",
    "Hans",
    "Ida",
    "Jonas",
    "Klara",
    "Lukas",
    "Marta",
    "Nils",
    "Olga",
    "Paul",
    "Rosa",
    "Stefan",
    "Tilda",
    "Uwe",
    "Vera",
    "Willi",
    "Xenia",
    "Yannik",
    "Zoe",
    "Adrian",
    "Bella",
    "Carlo",
    "Dora",
    "Emil",
    "Fiona",
    "Gustav",
    "Hanna",
    "Ingo",
    "Jana",
    "Kurt",
    "Lena",
    "Moritz",
    "Nora",
    "Otto",
)


def vocabulary() -> set[str]:
    words = {line.strip() for line in VOCABULARY.read_text(encoding="utf-8").splitlines()}
    return {w for w in words if w and not w.startswith("#")}


class Anonymizer:
    def __init__(self) -> None:
        self.vocabulary = vocabulary() | set(PSEUDONYMS) | {PROJECT_NAME}
        self.pseudonyms: dict[str, str] = {}
        self.serials: dict[str, str] = {}

    def word(self, word: str) -> str:
        if word in self.vocabulary:
            return word
        # one stable name per word, so that "Kind" and its group addresses keep belonging together
        if word not in self.pseudonyms:
            self.pseudonyms[word] = PSEUDONYMS[len(self.pseudonyms) % len(PSEUDONYMS)]
        return self.pseudonyms[word]

    def text(self, value: str) -> str:
        return WORD.sub(lambda m: self.word(m.group()), value)

    def serial(self, value: str) -> str:
        if value not in self.serials:
            self.serials[value] = f"SN{len(self.serials) + 1:06d}"
        return self.serials[value]

    def project_xml(self, content: str, *, project: bool) -> str:
        """Anonymise project.xml (`project=True`) or 0.xml."""
        content = content.lstrip("\ufeff")
        content = re.sub(r"\s*<ProjectTraces>.*?</ProjectTraces>", "", content, flags=re.S)
        content = re.sub(r"\s*<DeviceCertificates>.*?</DeviceCertificates>", "", content, flags=re.S)
        content = re.sub(rf'\s(?:{"|".join(DROPPED_ATTRIBUTES)})="[^"]*"', "", content)
        content = re.sub(r'\sGuid="[^"]*"', ' Guid="00000000-0000-4000-8000-000000000000"', content)
        content = re.sub(r'(SerialNumber=")([^"]*)(")', lambda m: m[1] + self.serial(m[2]) + m[3], content)
        if project:
            content = re.sub(r'(<ProjectInformation Name=")[^"]*(")', rf"\g<1>{PROJECT_NAME}\g<2>", content)
        attributes = "|".join(TEXT_ATTRIBUTES)
        return re.sub(rf'(\s(?:{attributes})=")([^"]*)(")', lambda m: m[1] + self.text(m[2]) + m[3], content)


def prune_application(content: bytes, language: str) -> bytes:
    """Reduce an application program to what xknxproject reads."""
    namespace = re.search(rb'xmlns="([^"]+)"', content)[1].decode()
    ElementTree.register_namespace("", namespace)
    root = ElementTree.fromstring(content)
    ns = f"{{{namespace}}}"
    keep = {"ComObject", "ComObjectRef", "Allocator", "Argument", "NumericArg", "Channel"}

    def prune(element: ElementTree.Element) -> bool:
        children = [child for child in element if prune(child)]
        element[:] = children
        return element.tag.removeprefix(ns) in keep or bool(children)

    for application in root.iter(f"{ns}ApplicationProgram"):
        for part in list(application):
            if part.tag == f"{ns}Languages":
                part[:] = [lang for lang in part if lang.get("Identifier") == language]
            elif not prune(part):
                application.remove(part)
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)


def prune_master(content: bytes, language: str) -> bytes:
    """Keep manufacturers, space usages, function types and the texts of one language."""
    namespace = re.search(rb'xmlns="([^"]+)"', content)[1].decode()
    ElementTree.register_namespace("", namespace)
    root = ElementTree.fromstring(content)
    ns = f"{{{namespace}}}"
    master = root.find(f"{ns}MasterData")
    keep = {"Manufacturers", "SpaceUsages", "ProductLanguages", "FunctionTypes", "Languages"}
    for child in list(master):
        if child.tag.removeprefix(ns) not in keep:
            master.remove(child)
    for languages in master.findall(f"{ns}Languages"):
        languages[:] = [lang for lang in languages if lang.get("Identifier") == language]
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)


def anonymize(source: Path, language: str = "de-DE") -> bytes:
    anonymizer = Anonymizer()
    out: dict[str, bytes] = {}
    with zipfile.ZipFile(source) as archive:
        project_id = next(
            n.removesuffix(".signature") for n in archive.namelist() if re.fullmatch(r"P-\w+\.signature", n)
        )
        for name in sorted(archive.namelist()):
            data = archive.read(name)
            new_name = name.replace(project_id, PROJECT_ID)
            # whitelist: signatures, certificates, `.validation` (holds the licensee) and similar stay out
            if not re.fullmatch(
                rf"knx_master\.xml|{project_id}/(?:project|0)\.xml|M-\w+/(?:Catalog|Hardware|M-\w+_A-[\w-]+)\.xml", name
            ):
                continue
            if name == "knx_master.xml":
                data = prune_master(data, language)
            elif name.startswith(project_id + "/"):
                text = data.decode("utf-8").replace(project_id, PROJECT_ID)
                data = anonymizer.project_xml(text, project=name.endswith("project.xml")).encode("utf-8")
            elif re.fullmatch(r"M-\w+/M-\w+_A-.*\.xml", name):
                data = prune_application(data, language)
            out[new_name] = data
    out[f"{PROJECT_ID}.signature"] = b""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for name, data in sorted(out.items()):
            target.writestr(zipfile.ZipInfo(name, STAMP), data, zipfile.ZIP_DEFLATED, 9)
    return buffer.getvalue()


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    Path(argv[2]).write_bytes(anonymize(Path(argv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
