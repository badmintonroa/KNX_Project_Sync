# KNX Project Sync

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Release](https://img.shields.io/github/v/release/badmintonroa/Knx-has-auto-importer?include_prereleases)](https://github.com/badmintonroa/Knx-has-auto-importer/releases)
[![Tests](https://github.com/badmintonroa/Knx-has-auto-importer/actions/workflows/tests.yaml/badge.svg)](https://github.com/badmintonroa/Knx-has-auto-importer/actions/workflows/tests.yaml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

🇩🇪 [Deutsche Version](README.de.md)

Creates the KNX entities of Home Assistant from your ETS project file (`.knxproj`) and keeps them in sync when the project changes. You choose, rename and correct the entities in a panel before anything is created. Updates keep entity IDs, names, areas and history.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=badmintonroa&repository=Knx-has-auto-importer&category=integration)
[![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=knx_project_sync)

![The KNX Project Sync panel](https://raw.githubusercontent.com/badmintonroa/Knx-has-auto-importer/main/docs/images/panel-en.png)

> [!NOTE]
> Back up your configuration before the first import. Changes are listed in the [changelog](CHANGELOG.md).

## Contents

- [Features](#features)
- [Installation](#installation)
- [What the integration creates](#what-the-integration-creates)
- [Supported entities](#supported-entities)
- [How entities are detected](#how-entities-are-detected)
- [Updating the project](#updating-the-project)
- [Automation](#automation)
- [Removal](#removal)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Features

- Reads ETS 4, 5 and 6 projects, including password protected ones, with [xknxproject](https://github.com/XKNX/xknxproject), the library the official KNX integration uses. You can also use the project you already uploaded in the KNX panel.
- Detects lights, switches, covers, climate, weather stations, sensors, texts, scenes and more (see [Supported entities](#supported-entities)).
- **Panel in the sidebar:** choose which entities to create, rename them, fix wrong group addresses, switch the type (switch ↔ light, text ↔ sensor). Nothing changes until you click *Apply*.
- **Your own KNX YAML is respected:** entities you already configured by hand are recognised and not created twice. You can take them over into the app.
- **Updates without losing anything:** entity IDs, names, areas, dashboards and history stay, even when a group address is re-addressed in ETS. New entities are only suggested, never added on their own.
- ETS rooms become Home Assistant areas.
- Everything runs locally. The project password is only used to open the file and is not stored.

The entity detection is a Python port of [knx2home](https://github.com/badmintonroa/knx2home). Tests check that both produce exactly the same result.

## Installation

### Requirements

- Home Assistant 2025.4 or newer
- The [KNX integration](https://www.home-assistant.io/integrations/knx/), set up and connected
- [HACS](https://hacs.xyz)
- Your ETS project exported as `.knxproj`

### 1. Install

**With HACS (recommended)**

1. Click *Open in HACS* above, or open HACS → ⋮ → *Custom repositories* and add `https://github.com/badmintonroa/Knx-has-auto-importer` with type *Integration*.
2. Download it and restart Home Assistant.

**Manually**

Copy `custom_components/knx_project_sync` from the [latest release](https://github.com/badmintonroa/Knx-has-auto-importer/releases) into `config/custom_components/` and restart Home Assistant.

### 2. Set up

1. *Settings → Devices & services → Add integration → KNX Project Sync* (or click *Add integration* above).
2. Choose the source: upload a `.knxproj` file, or use the project already uploaded in the KNX panel.
3. The project is read and you land in the panel. **Nothing has been created yet.**

### 3. First import

1. In the panel **KNX Project Sync** (sidebar, admins only) all detected entities are selected.
2. Deselect what you don't want, rename entities, fix group addresses or change types.
3. Click **Apply**. The entities are written and the KNX integration is reloaded. No restart is needed.

### The packages line

The entities are written to a file of their own, so your `configuration.yaml` and your own KNX configuration stay untouched. Home Assistant only reads such a file through [packages](https://www.home-assistant.io/docs/configuration/packages/):

```yaml
homeassistant:
  packages: !include_dir_named packages
```

If this line is missing, the panel shows a card and Home Assistant shows a repair, both with a button that adds it. `configuration.yaml` is backed up first. The result is checked with Home Assistant's own YAML loader, and the backup is restored if anything is wrong. If you already load packages from another folder, the file is moved there instead and `configuration.yaml` stays as it is.

## What the integration creates

```
config/
├── configuration.yaml                                  one line, only on your click
├── configuration.yaml.knx_project_sync-<time>.bak      backup before that change
├── packages/
│   └── knx_project_sync.yaml                           all generated entities
├── <your KNX YAML>.knx_project_sync-<time>.bak         backup when you take entities over
└── .storage/
    └── knx_project_sync                                choices, names, corrections, last import
```

| File | Content | Edit by hand? |
|---|---|---|
| `packages/knx_project_sync.yaml` | The `knx:` configuration of all selected entities. Rewritten on every *Apply*. The path can be changed in the settings. | No. Use the panel, your changes would be overwritten. |
| `.storage/knx_project_sync` | The project as read, your choices in the panel, what was applied last. | No |
| `*.knx_project_sync-*.bak` | Backups made before the integration changes one of your files. | Delete them when you no longer need them. |

The package file looks like this:

```yaml
# Automatisch erzeugt von knx_project_sync – nicht von Hand bearbeiten.
# Generated by knx_project_sync – do not edit, changes are overwritten on the next import.
# Projekt / project: Musterhaus
knx:
  light:
    - name: Wohnzimmer Decke
      address: 1/1/10
      state_address: 1/5/10
      brightness_address: 1/3/10
      brightness_state_address: 1/4/10
  sensor:
    - name: Wohnzimmer Temperatur
      state_address: 3/0/1
      type: temperature
```

Inside Home Assistant the integration adds:

- the **KNX Project Sync** panel in the sidebar
- a **Last import** sensor (timestamp; project, source and the counts of the last import as attributes)
- **areas** named after the ETS rooms, for entities that have no area yet (can be turned off)
- notifications when a new project version brings new entities
- [diagnostics](https://www.home-assistant.io/docs/configuration/troubleshooting/#download-diagnostics) for bug reports

The entities themselves belong to the KNX integration. They are normal KNX entities, as if you had written the YAML yourself.

### Settings

*Settings → Devices & services → KNX Project Sync → Configure → Settings*

| Option | Default | Meaning |
|---|---|---|
| Entity types | all | Only these types are created. |
| Entities missing from the project | delete | *Delete* removes them, *Keep* leaves them in place. |
| Assign areas from ETS rooms | on | Only for entities without an area. Areas you set are never changed. |
| Package file | `packages/knx_project_sync.yaml` | Where the entities are written. |

## Supported entities

| Type | Detected from | Fields |
|---|---|---|
| Light | Dimming actuator channels, ETS 6 functions, address pattern, name pattern (see below) | switch, state, brightness, brightness state |
| Switch | DPT 1.001 (also 1.002, 2.001) | address, state address |
| Binary sensor | DPT 1.001 named *status*, 1.005, 1.006, 1.009 | state address |
| Sensor | DPT 5.001, 7.xxx, 8.xxx, 9.xxx, 12.xxx, 20.102, 20.105, or names like *temperature*, *humidity*, *CO2*, *lux* | state address, type |
| Text | DPT 16.000, 16.001 | address, state address |
| Time / Date / Date and time | DPT 10.001 / 11.001 / 19.001 | address |
| Cover | Blind actuator channels, or DPT 1.007, 1.008, 1.010, 5.001, 5.003 with cover names (*blind*, *shutter*, *Jalousie*, …) | up/down, step, stop, position, slat angle, their states |
| Climate | Actuator or room controller channel with actual and target temperature (9.001) | setpoint shift, operation mode, controller mode, heating/cooling, valve, humidity |
| Weather | Weather station device with outdoor temperature and wind or brightness | temperature, brightness N/E/S/W, wind speed and direction, rain/frost/wind alarm, day/night, air pressure, humidity |
| Scene | DPT 17.001, 18.001, names with *scene* | address, scene number |

Not supported yet: `fan`, `number`, `select`, `button`, `expose`, `notify`. Known gaps of the detection:

- DPT 14.xxx (e.g. power 14.056) is not detected.
- DPT 1.018 (presence) and 1.024 (day/night) on their own are not detected as binary sensors.
- Scenes without a number in the name cannot be created, Home Assistant needs `scene_number`. The panel shows them as *not possible*.
- Group addresses are always written in three levels (`1/2/3`), also for projects with two-level or free addressing.

Group addresses that fit no type are listed in the panel under *No type*. If a type is wrong, change it in the panel (see the tip below).

## How entities are detected

Each group address ends up in at most one entity. The steps run in this order, and a group address used by an earlier step is not used again:

1. **Lights**, from five sources:
   1. channels of dimming actuators (switching, dimming and brightness objects of one channel)
   2. ETS 6 functions (the group addresses of one function)
   3. the address pattern `1/<middle>/<n>`: middle group 1 = switch, 2 = dim, 3 = brightness, 4 = brightness state, 5 = state, joined by the same `<n>`
   4. names starting with `LA<number>`
   5. names ending in ` s` (switch), ` d` (dim), ` w` (value) or ` status`

   If several sources find the same switch address, they are merged into one light, and the source with the most fields wins.
2. **Switches**: DPT 1.001 grouped by name. A name with *status* becomes the state address. Switch outputs of dimming actuators are lights, not switches. Addresses `1/7/x` are skipped.
3. **Covers**: first from the channels of blind actuators, then from cover names among the remaining group addresses.
4. **Climate**: per actuator or room controller channel.
5. **Weather**: per weather station device.
6. **Everything else, one group address at a time:**
   1. A type in square brackets in the ETS name wins: `[switch]`, `[light]`, `[cover]`, `[sensor]`, `[binary_sensor]`, `[scene]`. This only applies here, to group addresses that no earlier step used.
   2. Otherwise the DPT decides, and for ambiguous DPTs the name. For example 5.001 is a cover with *blind* in the name, a light with *brightness*, and a sensor otherwise.
   3. Without a DPT only the name counts (*light*, *lamp*, *temp*, *status*, …).
   4. Anything left goes to *No type*.

When you click *Apply*, these rules come on top:

1. **Your choices in the panel win over everything**: selected or not, name, type, corrected addresses.
2. **Your own KNX YAML comes before the project.** An entity with the same unique ID, or one that uses the same group address (for example the temperature of your own climate entity), is marked *Own YAML* and not created twice. You can take it over into the app or mark any entity as *already exists*.
3. **A light beats a switch** on the same group address.
4. **DPT 16 becomes a text entity**, unless it was already applied as a sensor.
5. Everything is checked against the schema of the KNX integration. Invalid entities are shown and skipped.

> [!TIP]
> If an entity is detected with the wrong type, change it in the panel. Your choice is stored per entity and kept with every new project version.

## Updating the project

Export the project from ETS again and upload it in the panel (*Upload project file*), or upload it in the KNX panel and click *Read from KNX panel*. The panel shows what changes:

- **Changed** entities, for example a new name or an extra status address, are updated.
- **Removed** entities are deleted, or kept if you set that in the settings.
- **New** entities are *not* added. They show up as *Newly available*, and a notification tells you about them.
- **Re-addressed** group addresses keep their entity: the entity is moved to the new unique ID before KNX is reloaded, so entity ID, name, area and history stay.

## Automation

The action `knx_project_sync.import_project` runs an import without the panel:

```yaml
action: knx_project_sync.import_project
data:
  source: file              # or knx_project
  file: knx/projekt.knxproj # relative to the config folder
  password: !secret knx_project_password
  dry_run: true             # only return what would change
```

It returns the summary. After every import the event `knx_project_sync_imported` is fired.

## Removal

1. *Settings → Devices & services → KNX Project Sync → ⋮ → Delete*.
2. In HACS: *KNX Project Sync* → ⋮ → *Remove*, then restart Home Assistant.

When the integration is deleted (step 1):

| What | Happens |
|---|---|
| `packages/knx_project_sync.yaml` | deleted, KNX is reloaded |
| Generated entities | removed from Home Assistant, including their entity registry entries. The recorded history stays in the database. |
| Packages line in `configuration.yaml` | taken out again if the integration added it, with a backup. It stays if other files are in `packages/` now. |
| `packages/` folder | deleted if the integration created it and it is empty |
| `.storage/knx_project_sync`, panel, *Last import* sensor | deleted |
| Areas | stay, they may be used by other entities |
| Backups `*.knx_project_sync-*.bak` | stay, delete them by hand |

> [!IMPORTANT]
> Entities you **took over** from your own YAML into the app are deleted with the package file. To keep them, copy them from `packages/knx_project_sync.yaml` into your own configuration before deleting, or restore the backup of your file (`<file>.knx_project_sync-<time>.bak`).

## Troubleshooting

**The entities don't appear.**
Check that the packages line is in `configuration.yaml`. The panel and *Settings → Repairs* offer to add it. Then look at *Settings → System → Logs* for errors of the KNX integration.

**An entity exists twice.**
Probably you also have it in your own KNX YAML with different group addresses. Mark it as *already exists* in the panel, or take it over into the app.

**The project cannot be read.**
Check the password. Projects from very old ETS versions may not be supported by xknxproject.

**Debug log**

```yaml
logger:
  logs:
    custom_components.knx_project_sync: debug
```

## Contributing

Help is welcome, also without programming:

- **Report wrong detection:** open an [issue](https://github.com/badmintonroa/Knx-has-auto-importer/issues) with the group address names, their DPTs and what you expected. Please don't attach your `.knxproj`, it contains your whole installation.
- **Report a bug:** add the version, the [diagnostics](https://www.home-assistant.io/docs/configuration/troubleshooting/#download-diagnostics) of the integration and the debug log.
- **Translations:** the panel texts are in [`frontend/src/strings.ts`](frontend/src/strings.ts), the rest in [`translations/`](custom_components/knx_project_sync/translations/).
- **Code:** see [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests and the release process.

## License

[MIT](LICENSE). The entity detection is based on [knx2home](https://github.com/badmintonroa/knx2home).

This is not an official project of Home Assistant or the KNX Association. KNX and ETS are trademarks of the KNX Association.
