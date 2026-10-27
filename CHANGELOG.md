# Changelog

Versionen nach [Semantic Versioning](https://semver.org/lang/de/). Solange die Version mit `0.` beginnt, kann sich noch alles ändern. Versionen mit `-beta.N` sind Vorabversionen, die auf GitHub als Pre-Release erscheinen und in HACS nur mit *Beta-Versionen anzeigen*.

Beim Release wird der Abschnitt der Version zum Text des GitHub-Release. Eine neue Version entsteht so:

1. Version in `custom_components/knx_project_sync/manifest.json`, `const.py` und `frontend/package.json` erhöhen (ein Test prüft, dass alle gleich sind).
2. Hier einen Abschnitt `## <version>` mit den Änderungen ergänzen.
3. Nach dem Merge auf `main` legt der Workflow *Release* Tag und Release an.

## 0.1.2

### Behoben

- Panel: Ein Eintrag, den du nicht angelegt hast (*Neu verfügbar*), nimmt anderen Einträgen nicht mehr die Gruppenadressen oder die unique_id weg. Vorher konnte z. B. ein auf den Schalter „Tag/Nacht“ übernommenes Wetter die echte Wetterstation als *Doppelt* blockieren und deren Sensoren als *GA schon belegt*.
- Wetterstation: Sensoren und Schalter, die schon importiert sind, bleiben beim Einschalten des Typs *Wetter* erhalten (sie würden sonst entfernt).
- Szenen werden nur noch über den DPT (17, 18) und *Szene* im Namen erkannt, nicht mehr über die Adresse `0/1/x`. Vorher wurde jede Gruppenadresse in `0/1/x` zur Szene, auch wenn sie z. B. ein Prozentwert der Jalousien war (5.001), und Schalter in `0/1/x` wurden übersprungen. Wer dort eine DPT-lose Szene hatte, findet sie jetzt unter *Nicht zugeordnet* und kann sie im Panel als Szene anlegen.

## 0.1.1

### Behoben

- Wetterstation: Ihre Gruppenadressen (Temperatur, Wind, Sonne, Tag/Nacht, Windalarm) werden nicht mehr zusätzlich als einzelne Sensoren und Schalter vorgeschlagen, solange der Typ *Wetter* aktiv ist. Vorher erschien z. B. Tag/Nacht als Schalter oder Licht in einem Raum, und die Wetterstation selbst stand als *Doppelt* da.
- Namen von Gruppenadressen und Objekttexte mit Leerzeichen am Anfang oder Ende werden wie in knx2home gekürzt. Vorher hatten die Entities solcher Gruppenadressen ein Leerzeichen am Ende des Namens.

### Intern

- Test mit einem anonymisierten echten ETS6-Projekt (`tests/fixtures/einfamilienhaus.knxproj`: Einfamilienhaus mit 264 Gruppenadressen, 36 Geräten von fünf Herstellern, Räumen und Schaltschränken). Geprüft werden Parität mit knx2home, Erkennung, Räume, Import, erneuter Import und das geschriebene YAML sowie, dass keine Namen, Schlüssel oder Seriennummern im Projekt stehen.
- `tools/fixtures/anonymize_project.py` macht aus einem eigenen Projekt ein solches Fixture: Namen außerhalb von `vocabulary.txt` werden durch erfundene Vornamen ersetzt, Schlüssel, Zertifikate, Benutzernamen und Seriennummern entfallen, die Herstellerprogramme werden auf das gekürzt, was xknxproject liest.
- `importer.py` aufgeteilt, am Verhalten ändert sich nichts:
  - `project.py`: Projekt lesen (Upload, Datei, KNX-Panel) und ETS-Räume zuordnen.
  - `registry.py`: unique_id-Umzug, Entfernen von Entities, Bereiche.
  - `packages.py`: jetzt auch das Prüfen, Eintragen und Zurücknehmen der Paket-Zeile in der `configuration.yaml`, nicht mehr halb in `importer.py`.
  - `errors.py`: `KnxImportError`.
  - `importer.py` behält Speicher, Planen, Übernehmen und Entfernen. `async_apply` liest sich als Folge benannter Schritte.

## 0.1.0

Erste stabile Version, ohne Beta-Zusatz. HACS zeigt sie auch ohne *Beta-Versionen anzeigen*. Gegenüber 0.1.0-beta.3 ändert sich nichts am Verhalten.

### Funktionen (aus den Betas)

- ETS-Projekt hochladen (auch passwortgeschützt) oder das Projekt aus dem KNX-Panel verwenden. Einrichten liest nur ein, angelegt wird erst im Panel.
- Panel: Entities auswählen, umbenennen, Typ ändern (Schalter ↔ Licht, Text ↔ Sensor), Gruppenadressen korrigieren, neue Projektversionen prüfen.
- Updates behalten entity_id, Namen, Bereiche und Verlauf. Neue Entities werden nur vorgeschlagen.
- Eigene KNX-YAML wird erkannt und lässt sich in die App übernehmen.
- Die Paket-Zeile in der `configuration.yaml` wird mit einem Klick eingetragen und beim Löschen der Integration wieder entfernt.

### Intern

- Code lesbarer: Datenformen in `model.py` (Status, Auswahl, letzter Import, eigene YAML, Konflikt), `build_plan` in benannte Schritte zerlegt, toter Code entfernt.
- Die Machbarkeitsprüfung für xknxproject (`tools/spike`) ist entfernt. Der Vergleich der fertigen Entities mit knx2home deckt sie ab.

## 0.1.0-beta.3

### Geändert

- Beim Löschen der Integration wird die Paket-Zeile wieder aus der `configuration.yaml` entfernt, wenn die Integration sie eingetragen hat (mit Sicherung; sie bleibt, wenn andere Pakete sie brauchen). Die Registry-Einträge der erzeugten Entities werden ebenfalls entfernt.

### Doku

- README auf Englisch neu aufgebaut, mit deutscher Fassung `README.de.md`: Installation, angelegte Dateien, unterstützte Entities, Reihenfolge der Erkennung, Deinstallation, Fehlerbehebung, Mithelfen. Screenshots des Panels.
- `CONTRIBUTING.md` für Entwicklung, Tests und Releases.

## 0.1.0-beta.2

### Neu

- Fehlt in der `configuration.yaml` die Paket-Zeile (`homeassistant: packages:`), trägt das Panel oder die Reparatur sie mit einem Klick ein. Vorher wird eine Sicherung angelegt, danach wird geprüft und KNX neu geladen, ohne Neustart. Wer schon einen anderen Paket-Ordner nutzt, bekommt die Datei dorthin verschoben.

### Entfernt

- Übernahme von Test-Installationen unter dem früheren Namen „KNX2HOME Importer“.

## 0.1.0-beta.1

Erste Beta.

### Neu

- ETS-Projekt (`.knxproj`, auch passwortgeschützt) hochladen oder das im KNX-Panel hochgeladene Projekt verwenden. Die Entity-Erkennung ist ein Python-Port von knx2home.
- Panel **KNX Project Sync** in der Seitenleiste:
  - Entities auswählen, umbenennen, Typ ändern (Schalter ↔ Licht, Text ↔ Sensor).
  - Gruppenadressen korrigieren.
  - Neue Projektversionen prüfen.
- Einrichten liest das Projekt nur ein. Angelegt wird erst mit *Übernehmen* im Panel.
- Neue Entities aus einem geänderten Projekt werden nur vorgeschlagen, eine Benachrichtigung weist darauf hin.
- Updates behalten entity_id, Namen, Bereiche und Verlauf, auch bei umadressierten Gruppenadressen.
- Eigene KNX-YAML wird erkannt: gleiche Entity, Schalter ↔ Licht oder eine schon verwendete Gruppenadresse (z. B. die Temperatur eines eigenen Klimas). Solche Einträge lassen sich in die App übernehmen. Die eigene Datei wird dabei gesichert und geprüft.
- „Schon vorhanden“-Markierung, ETS-Räume als Bereiche, Sensor „Letzter Import“, Diagnose, Service `knx_project_sync.import_project`.
- Texte (DPT 16) werden als `text`-Entities angelegt.
