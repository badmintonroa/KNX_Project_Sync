"""Build synthetic ETS6 project files (.knxproj) for tests.

The archives are small but structured like real ETS6 exports, so that both
xknxproject and the knx2home reference parser can read them:

    knx_master.xml
    P-0A1B.signature
    P-0A1B/project.xml
    P-0A1B/0.xml
    M-0083/Hardware.xml
    M-0083/M-0083_A-<app>.xml   (one per application program)

Fixtures:
    musterhaus_v1         base project
    musterhaus_v2         later revision of the same project: renames, a re-addressed
                          group address, a removed and an added device (update/diff tests)
    musterhaus_overrides  v1 with texts/DPTs overridden on ComObjectRef and
                          ComObjectInstanceRef level, as ETS applications commonly do
    musterhaus_protected  v1 as password protected ETS6 export (password: geheim)

Usage: python tools/fixtures/build_fixtures.py [output_dir]
"""

from __future__ import annotations

import base64
import copy
from dataclasses import dataclass, field
import hashlib
import io
import json
from pathlib import Path
import sys
from xml.sax.saxutils import quoteattr
import zipfile

import pyzipper  # dependency of xknxproject, used for the AES protected fixture

NS = "http://knx.org/xml/project/23"
PROJECT_ID = "P-0A1B"
PROTECTED_PASSWORD = "geheim"
MANUFACTURER = "M-0083"


@dataclass
class GA:
    """Group address. `ga_id` is the ETS id suffix (e.g. GA-3), stable across renames."""

    ga_id: str
    address: str  # three level, e.g. 1/0/1
    name: str
    dpt: str | None  # e.g. DPST-1-1


@dataclass
class CO:
    """Communication object of an application program and its links in the project."""

    number: int
    text: str
    function_text: str
    dpt: str
    flags: str  # subset of "RWTU" that is enabled
    size: str
    links: list[str] = field(default_factory=list)  # GA ids, first one is the sending GA
    ref_attrs: dict[str, str] = field(default_factory=dict)  # overrides on the ComObjectRef
    instance_attrs: dict[str, str] = field(default_factory=dict)  # overrides on the ComObjectInstanceRef


@dataclass
class Device:
    """Device instance with a dedicated (tiny) application program."""

    di_id: str
    address: int  # device part of the individual address 1.1.x
    name: str
    app: str  # application suffix, e.g. 0010-11-AAAA
    hardware: str
    com_objects: list[CO]


@dataclass
class Project:
    name: str
    group_addresses: list[GA]
    devices: list[Device]
    password: str | None = None


def ga_raw(address: str) -> int:
    main, middle, sub = (int(part) for part in address.split("/"))
    return (main << 11) | (middle << 8) | sub


def flag(flags: str, letter: str) -> str:
    return "Enabled" if letter in flags else "Disabled"


def base_project() -> Project:
    gas = [
        GA("GA-1", "1/0/1", "Wohnzimmer Licht Schalten", "DPST-1-1"),
        GA("GA-2", "1/0/2", "Wohnzimmer Licht Status", "DPST-1-1"),
        GA("GA-3", "1/1/1", "Esszimmer Licht Schalten", "DPST-1-1"),
        GA("GA-4", "1/1/2", "Esszimmer Licht Status", "DPST-1-1"),
        GA("GA-5", "1/1/3", "Esszimmer Licht Helligkeit", "DPST-5-1"),
        GA("GA-6", "1/1/4", "Esszimmer Licht Helligkeit Status", "DPST-5-1"),
        GA("GA-7", "1/1/5", "Esszimmer Licht Dimmen", "DPST-3-7"),
        GA("GA-8", "2/0/1", "Büro Jalousie Auf/Ab", "DPST-1-8"),
        GA("GA-9", "2/0/2", "Büro Jalousie Stop", "DPST-1-17"),
        GA("GA-10", "2/0/3", "Büro Jalousie Position", "DPST-5-1"),
        GA("GA-11", "2/0/4", "Büro Jalousie Position Status", "DPST-5-1"),
        GA("GA-12", "3/0/1", "Wohnzimmer Temperatur", "DPST-9-1"),
        GA("GA-13", "3/0/2", "Wohnzimmer Luftfeuchte", "DPST-9-7"),
        GA("GA-14", "3/0/3", "Flur Präsenz", "DPST-1-18"),
        GA("GA-15", "4/0/1", "Wohnzimmer Szene", "DPST-18-1"),
        GA("GA-16", "5/0/1", "Uhrzeit", "DPST-10-1"),
        GA("GA-17", "5/0/2", "Datum", "DPST-11-1"),
        GA("GA-18", "1/0/9", "Reserve", "DPST-1-1"),
    ]
    devices = [
        Device(
            "DI-1", 1, "Schaltaktor", "0010-11-AAAA", "AKS-0416",
            [
                CO(0, "Kanal A", "Schalten", "DPST-1-1", "W", "1 Bit", ["GA-1"]),
                CO(1, "Kanal A", "Status", "DPST-1-1", "RT", "1 Bit", ["GA-2"]),
                CO(10, "Kanal B", "Schalten", "DPST-1-1", "W", "1 Bit", ["GA-18"]),
            ],
        ),
        Device(
            "DI-2", 2, "Dimmaktor", "0020-12-BBBB", "AKD-0401",
            [
                CO(0, "Kanal A", "Schalten", "DPST-1-1", "W", "1 Bit", ["GA-3"]),
                CO(1, "Kanal A", "Dimmen relativ", "DPST-3-7", "W", "4 Bit", ["GA-7"]),
                CO(2, "Kanal A", "Helligkeitswert", "DPST-5-1", "W", "1 Byte", ["GA-5"]),
                CO(3, "Kanal A", "Status An/Aus", "DPST-1-1", "RT", "1 Bit", ["GA-4"]),
                CO(4, "Kanal A", "Status Helligkeitswert", "DPST-5-1", "RT", "1 Byte", ["GA-6"]),
            ],
        ),
        Device(
            "DI-3", 3, "Jalousieaktor", "0030-13-CCCC", "JAL-0410",
            [
                CO(0, "Kanal A", "Auf/Ab", "DPST-1-8", "W", "1 Bit", ["GA-8"]),
                CO(1, "Kanal A", "Stop", "DPST-1-17", "W", "1 Bit", ["GA-9"]),
                CO(2, "Kanal A", "Position", "DPST-5-1", "W", "1 Byte", ["GA-10"]),
                CO(3, "Kanal A", "Status Position", "DPST-5-1", "RT", "1 Byte", ["GA-11"]),
            ],
        ),
        Device(
            "DI-4", 4, "Raumsensor", "0040-14-DDDD", "SCN-RS",
            [
                CO(0, "Temperatur", "Messwert", "DPST-9-1", "RT", "2 Bytes", ["GA-12"]),
                CO(1, "Luftfeuchte", "Messwert", "DPST-9-7", "RT", "2 Bytes", ["GA-13"]),
                CO(2, "Präsenz", "Ausgang", "DPST-1-18", "RT", "1 Bit", ["GA-14"]),
            ],
        ),
        Device(
            "DI-5", 5, "Taster", "0050-15-EEEE", "BE-TA55",
            [
                CO(0, "Taste 1", "Szene", "DPST-18-1", "WT", "1 Byte", ["GA-15"]),
                CO(1, "Taste 2", "Schalten", "DPST-1-1", "WT", "1 Bit", ["GA-1", "GA-2"]),
            ],
        ),
        Device(
            "DI-6", 6, "Zeitgeber", "0060-16-FFFF", "GPS-01",
            [
                CO(0, "Uhrzeit", "Senden", "DPST-10-1", "RT", "3 Bytes", ["GA-16"]),
                CO(1, "Datum", "Senden", "DPST-11-1", "RT", "3 Bytes", ["GA-17"]),
            ],
        ),
    ]
    return Project("Musterhaus", gas, devices)


def revised_project() -> Project:
    """Second revision of the same project, as it would come out of ETS later."""
    project = copy.deepcopy(base_project())
    gas = {ga.ga_id: ga for ga in project.group_addresses}
    # renamed in ETS
    gas["GA-1"].name = "Wohnzimmer Deckenlicht Schalten"
    gas["GA-2"].name = "Wohnzimmer Deckenlicht Status"
    # re-addressed in ETS (same ETS id, new address)
    gas["GA-12"].address = "3/1/1"
    # time sender removed from the project
    project.devices = [d for d in project.devices if d.di_id != "DI-6"]
    del gas["GA-16"], gas["GA-17"]
    # new CO2 sensor
    gas["GA-19"] = GA("GA-19", "3/0/4", "Wohnzimmer CO2", "DPST-9-8")
    project.devices.append(
        Device(
            "DI-7", 7, "CO2 Sensor", "0070-17-ABCD", "SCN-CO2",
            [CO(0, "CO2", "Messwert", "DPST-9-8", "RT", "2 Bytes", ["GA-19"])],
        )
    )
    project.group_addresses = list(gas.values())
    return project


def overrides_project() -> Project:
    """v1 where ETS application/instance data overrides the plain ComObject attributes."""
    project = copy.deepcopy(base_project())
    devices = {d.di_id: d for d in project.devices}
    # application program renames the function on the ComObjectRef
    devices["DI-2"].com_objects[2].ref_attrs["FunctionText"] = "Helligkeit absolut"
    # application program gives the status object its own text (= ETS channel grouping by text)
    devices["DI-1"].com_objects[1].ref_attrs["Text"] = "Kanal A Rückmeldung"
    # DPT only refined on the ComObjectRef (ComObject says 1.001, ref says 1.002)
    devices["DI-5"].com_objects[1].ref_attrs["DatapointType"] = "DPST-1-2"
    # user changed the object text of one instance in ETS
    devices["DI-4"].com_objects[0].instance_attrs["Text"] = "Temperatur Wohnzimmer"
    return project


def protected_project() -> Project:
    project = copy.deepcopy(base_project())
    project.password = PROTECTED_PASSWORD
    return project


def attrs(values: dict[str, str]) -> str:
    return "".join(f" {key}={quoteattr(value)}" for key, value in values.items())


def knx_master() -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<KNX xmlns="{NS}" CreatedBy="ETS6" ToolVersion="6.2.0">
  <MasterData Version="0" Signature="">
    <Manufacturers>
      <Manufacturer Id="{MANUFACTURER}" Name="Musterfirma" KnxManufacturerId="131" />
    </Manufacturers>
    <ProductLanguages>
      <Language Identifier="de-DE" />
    </ProductLanguages>
  </MasterData>
</KNX>
"""


def project_meta(project: Project) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<KNX xmlns="{NS}" CreatedBy="ETS6" ToolVersion="6.2.0">
  <Project Id="{PROJECT_ID}">
    <ProjectInformation Name={quoteattr(project.name)} GroupAddressStyle="ThreeLevel" LastModified="2024-01-01T00:00:00Z" Guid="6f1c2d3e-0000-4000-8000-0a1b0a1b0a1b" />
  </Project>
</KNX>
"""


def project_0(project: Project) -> str:
    devices = []
    for dev in project.devices:
        refs = []
        for co in dev.com_objects:
            if not co.links:
                continue
            links = " ".join(co.links)
            refs.append(
                f'          <ComObjectInstanceRef RefId="O-{co.number}_R-{co.number + 1}"{attrs(co.instance_attrs)} Links="{links}" />'
            )
        devices.append(
            f"""        <DeviceInstance Id="{PROJECT_ID}-0_{dev.di_id}" Name={quoteattr(dev.name)} Address="{dev.address}" ProductRefId="{MANUFACTURER}_H-{dev.hardware}_P-{dev.hardware}" Hardware2ProgramRefId="{MANUFACTURER}_H-{dev.hardware}_HP-{dev.app}" Puid="{100 + dev.address}">
          <ComObjectInstanceRefs>
{chr(10).join(refs)}
          </ComObjectInstanceRefs>
        </DeviceInstance>"""
        )

    by_main: dict[int, dict[int, list[GA]]] = {}
    for ga in sorted(project.group_addresses, key=lambda g: ga_raw(g.address)):
        main, middle, _ = (int(p) for p in ga.address.split("/"))
        by_main.setdefault(main, {}).setdefault(middle, []).append(ga)

    ranges = []
    for main, middles in by_main.items():
        middle_xml = []
        for middle, gas in middles.items():
            start = (main << 11) | (middle << 8)
            items = "\n".join(
                f'              <GroupAddress Id="{PROJECT_ID}-0_{ga.ga_id}" Address="{ga_raw(ga.address)}" Name={quoteattr(ga.name)}'
                + (f' DatapointType="{ga.dpt}"' if ga.dpt else "")
                + f' Puid="{1000 + int(ga.ga_id.split("-")[1])}" />'
                for ga in gas
            )
            middle_xml.append(
                f"""            <GroupRange Id="{PROJECT_ID}-0_GR-{main}-{middle}" RangeStart="{start}" RangeEnd="{start + 255}" Name="Mitte {main}/{middle}">
{items}
            </GroupRange>"""
            )
        start = main << 11
        ranges.append(
            f"""          <GroupRange Id="{PROJECT_ID}-0_GR-{main}" RangeStart="{start}" RangeEnd="{start + 2047}" Name="Haupt {main}">
{chr(10).join(middle_xml)}
          </GroupRange>"""
        )

    return f"""<?xml version="1.0" encoding="utf-8"?>
<KNX xmlns="{NS}" CreatedBy="ETS6" ToolVersion="6.2.0">
  <Project Id="{PROJECT_ID}">
    <Installations>
      <Installation Name="" InstallationId="0">
        <Topology>
          <Area Id="{PROJECT_ID}-0_A-1" Name="Bereich 1" Address="1">
            <Line Id="{PROJECT_ID}-0_L-1" Name="Linie 1" Address="1">
              <Segment Id="{PROJECT_ID}-0_S-1" Name="Segment 1" Number="0" MediumTypeRefId="MT-0">
{chr(10).join(devices)}
              </Segment>
            </Line>
          </Area>
        </Topology>
        <GroupAddresses>
          <GroupRanges>
{chr(10).join(ranges)}
          </GroupRanges>
        </GroupAddresses>
      </Installation>
    </Installations>
  </Project>
</KNX>
"""


def hardware(project: Project) -> str:
    items = []
    for dev in project.devices:
        hw = f"{MANUFACTURER}_H-{dev.hardware}"
        items.append(
            f"""        <Hardware Id="{hw}" Name={quoteattr(dev.name)} SerialNumber="{dev.hardware}" VersionNumber="1">
          <Products>
            <Product Id="{hw}_P-{dev.hardware}" Text={quoteattr(dev.name)} OrderNumber="{dev.hardware}" />
          </Products>
          <Hardware2Programs>
            <Hardware2Program Id="{hw}_HP-{dev.app}" MediumTypes="MT-0">
              <ApplicationProgramRef RefId="{MANUFACTURER}_A-{dev.app}" />
            </Hardware2Program>
          </Hardware2Programs>
        </Hardware>"""
        )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<KNX xmlns="{NS}" CreatedBy="ETS6" ToolVersion="6.2.0">
  <ManufacturerData>
    <Manufacturer RefId="{MANUFACTURER}">
      <Hardware>
{chr(10).join(items)}
      </Hardware>
    </Manufacturer>
  </ManufacturerData>
</KNX>
"""


def application(dev: Device) -> str:
    app_id = f"{MANUFACTURER}_A-{dev.app}"
    objects = []
    refs = []
    for co in dev.com_objects:
        objects.append(
            f'              <ComObject Id="{app_id}_O-{co.number}" Name="Obj{co.number}" Text={quoteattr(co.text)} FunctionText={quoteattr(co.function_text)}'
            f' Number="{co.number}" ObjectSize="{co.size}" DatapointType="{co.dpt}"'
            f' ReadFlag="{flag(co.flags, "R")}" WriteFlag="{flag(co.flags, "W")}" CommunicationFlag="Enabled"'
            f' TransmitFlag="{flag(co.flags, "T")}" UpdateFlag="{flag(co.flags, "U")}" ReadOnInitFlag="Disabled" />'
        )
        refs.append(
            f'              <ComObjectRef Id="{app_id}_O-{co.number}_R-{co.number + 1}" RefId="{app_id}_O-{co.number}"{attrs(co.ref_attrs)} />'
        )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<KNX xmlns="{NS}" CreatedBy="ETS6" ToolVersion="6.2.0">
  <ManufacturerData>
    <Manufacturer RefId="{MANUFACTURER}">
      <ApplicationPrograms>
        <ApplicationProgram Id="{app_id}" Name={quoteattr(dev.name)} ApplicationNumber="1" ApplicationVersion="1" ProgramType="ApplicationProgram" MaskVersion="MV-07B0">
          <Static>
            <ComObjectTable>
{chr(10).join(objects)}
            </ComObjectTable>
            <ComObjectRefs>
{chr(10).join(refs)}
            </ComObjectRefs>
          </Static>
        </ApplicationProgram>
      </ApplicationPrograms>
    </Manufacturer>
  </ManufacturerData>
</KNX>
"""


# fixed timestamps keep the plain archives byte-for-byte reproducible
STAMP = (2024, 1, 1, 0, 0, 0)


def ets6_zip_password(password: str) -> bytes:
    """Password of the inner project archive of protected ETS6 exports."""
    return base64.b64encode(
        hashlib.pbkdf2_hmac("sha256", password.encode("utf-16-le"), b"21.project.ets.knx.org", 65536, 32)
    )


def protected_archive(files: dict[str, str], password: str) -> bytes:
    """ETS6 stores the project folder as AES encrypted P-XXXX.zip (files at its root)."""
    buffer = io.BytesIO()
    with pyzipper.AESZipFile(
        buffer, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES
    ) as archive:
        archive.setpassword(ets6_zip_password(password))
        for name, content in files.items():
            archive.writestr(name, content.encode("utf-8"))  # AES salt is random anyway
    return buffer.getvalue()


def build(project: Project) -> bytes:
    project_files = {
        "project.xml": project_meta(project),
        "0.xml": project_0(project),
    }
    files: dict[str, str | bytes] = {
        "knx_master.xml": knx_master(),
        f"{PROJECT_ID}.signature": "",
        f"{MANUFACTURER}/Hardware.xml": hardware(project),
    }
    if project.password:
        files[f"{PROJECT_ID}.zip"] = protected_archive(project_files, project.password)
    else:
        files.update({f"{PROJECT_ID}/{name}": content for name, content in project_files.items()})
    for dev in project.devices:
        files[f"{MANUFACTURER}/{MANUFACTURER}_A-{dev.app}.xml"] = application(dev)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            data = content.encode("utf-8") if isinstance(content, str) else content
            archive.writestr(zipfile.ZipInfo(name, STAMP), data)
    return buffer.getvalue()


FIXTURES = {
    "musterhaus_v1": base_project,
    "musterhaus_v2": revised_project,
    "musterhaus_overrides": overrides_project,
    "musterhaus_protected": protected_project,
}

# Passwords of the protected fixtures, used by the reference generator and the tests.
PASSWORDS = {"musterhaus_protected": PROTECTED_PASSWORD}


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[2] / "tests" / "fixtures"
    out.mkdir(parents=True, exist_ok=True)
    for name, factory in FIXTURES.items():
        path = out / f"{name}.knxproj"
        path.write_bytes(build(factory()))
        print(f"wrote {path}")
    (out / "passwords.json").write_text(json.dumps(PASSWORDS, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
