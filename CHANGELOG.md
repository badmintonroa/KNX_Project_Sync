# Changelog

Versionen nach [Semantic Versioning](https://semver.org/lang/de/). Solange die Version mit `0.` beginnt, kann sich noch alles ändern. `-beta.N` sind Vorabversionen, die auf GitHub als Pre-Release erscheinen.

Beim Release wird der Abschnitt der Version zum Text des GitHub-Release. Eine neue Version entsteht so:

1. Version in `custom_components/knx_project_sync/manifest.json`, `const.py` und `frontend/package.json` erhöhen (ein Test prüft, dass alle gleich sind).
2. Hier einen Abschnitt `## <version>` mit den Änderungen ergänzen.
3. Nach dem Merge auf `main` legt der Workflow *Release* Tag und Release an.

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
