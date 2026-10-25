# Import und Update (Schritte 4–6)

## Ablauf

```
.knxproj (Upload, Datei, oder Projekt aus dem KNX-Panel)
  └─ xknxproject ──> mapping/ (Port von knx2home) ──> Manifest (Entities mit stabilen Schlüsseln)
                                                        │
       letzter Import (.storage/knx_project_sync) ─────┤
       eigene knx:-YAML (configuration.yaml) ───────────┼─> Plan (plan.py) ──> Vorschau im Dialog
       Einstellungen + KNX-Schema von HA ───────────────┘          │
                                                                   ▼  Absenden
  1. Entity-Registry: unique_ids umziehen (GA umadressiert → gleiche entity_id)
  2. packages/knx_project_sync.yaml schreiben (atomar) + knx.reload
  3. entfernte Entities aus der Registry löschen (oder behalten)
  4. optional: ETS-Räume → HA-Bereiche (nur Entities ohne Bereich)
  5. Stand speichern, Sensor „Letzter Import“ aktualisieren, Event knx_project_sync_imported
```

## Voraussetzungen

- Die **KNX-Integration** ist eingerichtet.
- Die Paket-Datei wird geladen. In der `configuration.yaml` steht:

  ```yaml
  homeassistant:
    packages: !include_dir_named packages
  ```

  Fehlt das, erscheint nach dem Import ein Repair-Hinweis. Eine eigene `knx:`-YAML (z. B. in der `configuration.yaml`) darf parallel bestehen bleiben, HA führt beide zusammen.

## Status im Plan

| Status | Bedeutung | in YAML |
|---|---|---|
| `new` | neu im Projekt | ✔ |
| `changed` | Name oder Adressen geändert (auch: GA in ETS gelöscht und mit gleicher Adresse neu angelegt) | ✔ |
| `unchanged` | wie beim letzten Import | ✔ |
| `kept` | nicht mehr im Projekt, Einstellung „Behalten“ | ✔ |
| `removed` | nicht mehr im Projekt (oder Typ abgewählt), Einstellung „Löschen“ → Entity wird gelöscht | – |
| `conflict` | gleiche unique_id existiert schon in deiner **eigenen KNX-YAML**. Deine Definition gewinnt, nichts wird doppelt angelegt | – |
| `invalid` | vom KNX-YAML-Schema der installierten HA-Version abgelehnt (z. B. Szene ohne Nummer) | – |
| `duplicate` | GA schon von einer anderen Entity belegt (knx2home erzeugt z. B. Licht *und* Schalter auf derselben GA, dann gewinnt das Licht) | – |
| `excluded` | Entity-Typ in den Einstellungen abgewählt | – |

Entities, die im KNX-Panel per UI angelegt wurden, haben zufällige unique_ids und werden nicht als Konflikt erkannt. Bitte nicht dieselben GAs zusätzlich über das KNX-UI anlegen.

## Was erhalten bleibt

- **entity_id, Name in HA, Bereich, Dashboards, Automationen, Verlauf.** Die KNX-Integration identifiziert YAML-Entities über eine unique_id aus ihrer Gruppenadresse (Licht/Schalter: `address`, Sensor: `state_address`, Jalousie: `move_long_address_position_address`, …). Wird eine GA umadressiert, zieht der Import den Registry-Eintrag *vor* dem Reload auf die neue unique_id um.
- Namen, die du in HA geändert hast, liegen in der Registry und werden nie überschrieben. Der Name aus der ETS ist nur der Standardname.
- Bereiche werden nur bei Entities ohne Bereich gesetzt.

## Wiedererkennung über Importe hinweg

1. Über den stabilen Schlüssel `<domain>:<GA-Id>` ([manifest-v1.md](manifest-v1.md)). Er übersteht Umbenennen und Umadressieren in der ETS.
2. Sonst über die unique_id (gleiche Domain und Adresse), z. B. wenn die GA in der ETS gelöscht und neu angelegt wurde.

## Einstellungen

| Einstellung | Standard |
|---|---|
| Entity-Typen | alle |
| Entities, die im Projekt fehlen | Löschen |
| Bereiche aus ETS-Räumen | aus |
| Paket-Datei | `packages/knx_project_sync.yaml` |

Änderbar unter *Einstellungen → Geräte & Dienste → KNX Project Sync → Konfigurieren → Nur Einstellungen ändern*. Dabei wird der zuletzt importierte Projektstand neu angewendet, ohne die Datei erneut hochzuladen.

## Service

```yaml
action: knx_project_sync.import_project
data:
  file: knx/musterhaus.knxproj   # relativ zum Konfigurationsordner
  password: !secret knx_projekt  # optional
  dry_run: true                  # nur Plan zurückgeben
```

`source: knx_project` verwendet stattdessen das im KNX-Panel hochgeladene Projekt. Die Antwort enthält die Zusammenfassung, bei `dry_run` zusätzlich den Status jeder Entity.

## Deinstallation

Beim Entfernen der Integration wird die Paket-Datei gelöscht und KNX neu geladen. Die importierten Entities verschwinden, deine eigene KNX-YAML bleibt unberührt.
