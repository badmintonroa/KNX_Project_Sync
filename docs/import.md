# Import und Update (Schritte 4–6)

## Ablauf

```
.knxproj (Upload, Datei, oder Projekt aus dem KNX-Panel)
  └─ xknxproject ──> mapping/ (Port von knx2home) ──> Manifest (Entities mit stabilen Schlüsseln)
                                                        │
       letzter Import (.storage/knx_project_sync) ─────┤
       eigene knx:-YAML (configuration.yaml) ───────────┼─> Plan (plan.py) ──> Panel (Auswahl, Vorschau)
       Einstellungen + KNX-Schema von HA ───────────────┘          │
                                                                   ▼  Übernehmen
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
| `conflict` | gleiche Gruppenadresse existiert schon in deiner **eigenen KNX-YAML**, gleicher Typ oder Schalter ↔ Licht. Deine Definition gewinnt, nichts wird doppelt angelegt. Im Panel per *In App übernehmen* übernehmbar | – |
| `existing` | im Panel als *Schon vorhanden* markiert (z. B. anders definiert, als die Erkennung meint). Wird nicht angelegt | – |
| `invalid` | vom KNX-YAML-Schema der installierten HA-Version abgelehnt (z. B. Szene ohne Nummer) | – |
| `duplicate` | GA schon von einer anderen Entity belegt (knx2home erzeugt z. B. Licht *und* Schalter auf derselben GA, dann gewinnt das Licht) | – |
| `excluded` | Entity-Typ in den Einstellungen abgewählt | – |
| `pending` | neu im Projekt (ab dem zweiten Import), wird nur im Panel angeboten | – |
| `deselected` | im Panel abgewählt. War die Entity schon angelegt, wird sie gelöscht (unabhängig von „Behalten“) | – |

Entities, die im KNX-Panel per UI angelegt wurden, haben zufällige unique_ids und werden nicht als Konflikt erkannt. Bitte nicht dieselben GAs zusätzlich über das KNX-UI anlegen.

## Panel

Das Panel *KNX Project Sync* in der Seitenleiste zeigt alle erkannten Entities mit ihrem Status. Die Auswahl wird pro stabilem Schlüssel (`switch:GA-1`) gespeichert und übersteht damit Umbenennen und Umadressieren in der ETS:

| Wahl | Wirkung |
|---|---|
| anlegen ja/nein | `deselected` bzw. wieder angelegt. Neue Entities ohne Entscheidung sind `pending`. |
| Name | Standardname in der YAML. Ein in HA vergebener Name hat weiter Vorrang. |
| Gruppenadressen | Einzelne Adressen korrigieren, ergänzen (z. B. fehlender Status) oder entfernen. Die Adresse aus der ETS wird daneben angezeigt und lässt sich zurücksetzen. Die Korrektur gilt auch bei späteren Importen, bis du sie zurücksetzt. Ein Tippfehler wird vom KNX-Schema abgelehnt (`invalid`) und löscht nichts. Ändert sich die Haupt-GA, zieht die Entity mit (gleiche entity_id). |
| Typ Schalter ↔ Licht | Nur für reine Ein/Aus-Entities (`address`, `state_address`). Schalter-Optionen wie `respond_to_read` entfallen. Die Entity bekommt eine neue entity_id (`switch.…` → `light.…`), die alte wird gelöscht. |

### Eigene YAML in die App übernehmen

Bei einem Konflikt zeigt das Panel, wo die Entity in deiner YAML steht (Datei und Zeile). *In App übernehmen* verschiebt sie beim nächsten *Übernehmen* in die Paket-Datei:

1. Der Eintrag wird **mit deiner Konfiguration** übernommen (Name, Typ, Optionen wie `invert`), nicht mit der aus dem Projekt. Er bleibt so, bis du im Panel *Auf Projekt zurücksetzen* wählst.
2. Aus deiner Datei wird nur genau dieser Listeneintrag (`- name: …` mit den eingerückten Zeilen) entfernt. Kommentare und der Rest bleiben, eine leere Liste wird zu `[]`. Vorher entsteht eine Sicherung `<datei>.knx_project_sync-<zeit>.bak` daneben.
3. Danach liest der Import die Konfiguration mit dem YAML-Loader von HA neu. Fehlt mehr als dieser eine Eintrag, wird die Sicherung zurückgespielt und nichts übernommen.
4. entity_id, Name, Bereich und Verlauf bleiben, weil die unique_id gleich bleibt.

Nicht automatisch übernehmbar sind Einträge in Kurzschreibweise (`- {name: …}`), mit YAML-Tags oder außerhalb des Konfigurationsordners. Das Panel sagt dann, dass du sie selbst entfernen musst.

### Schon vorhanden

Erkennt das Panel einen Konflikt nicht, z. B. weil deine YAML die GA anders verwendet, kannst du jede Entity als *Schon vorhanden* markieren. Sie wird dann nicht angelegt. Hatte die App sie schon angelegt, wird nur diese eigene Kopie gelöscht, nie eine Entity deiner YAML. Schalter und Licht auf derselben GA werden inzwischen automatisch als Konflikt erkannt.

Alle Änderungen sind ein Entwurf. Erst *Übernehmen* schreibt die Paket-Datei und lädt KNX neu. Eine im Panel geladene Projektversion (Upload oder KNX-Panel) wird ebenfalls erst damit angewendet.

**Neue Entities** aus einem geänderten Projekt werden nicht angelegt, egal ob das Projekt über das Panel, den *Konfigurieren*-Dialog oder den Service kommt. Stattdessen erscheint eine Benachrichtigung mit Link ins Panel. Nur der allererste Import legt alles an.

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

Änderbar unter *Einstellungen → Geräte & Dienste → KNX Project Sync → Konfigurieren → Einstellungen*. Gespeichert wird sofort, angewendet erst im Panel mit *Übernehmen*. Das Panel zeigt vorher, was die neuen Einstellungen ändern.

Einrichten und *Konfigurieren* lesen ein Projekt nur ein, eine neue Datei oder das Projekt aus dem KNX-Panel, und legen nichts an. Eine Benachrichtigung verlinkt ins Panel. Nur der Service `import_project` wendet direkt an, für Automationen.

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
