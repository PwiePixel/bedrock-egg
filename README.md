# Minecraft Bedrock Egg für Pterodactyl

Ein funktionierendes Egg für den offiziellen **Minecraft Bedrock Dedicated Server** (Linux).
Getestet mit Bedrock **1.26.66.1**, also auch mit dem neuen Netzwerk-Transport *NetherNet*.

## Zwei Varianten

| Datei | Für wen | Unterschied |
|---|---|---|
| [`egg-minecraft-bedrock.json`](egg-minecraft-bedrock.json) | Normaler Server | Mojang-Standardwerte (Sichtweite 32, 8 Threads) |
| [`egg-minecraft-bedrock-performance.json`](egg-minecraft-bedrock-performance.json) | Wenig CPU/RAM | Sichtweite 10, 4 Threads, Kompression `snappy` ab 256 Byte, Chunk-Aufbau beim Client, LAN-Suche aus |

Beide Varianten können parallel im selben Nest liegen. Sichtweite, Tick-Distanz und Threads lassen sich bei beiden pro Server über Variablen anpassen.

## Chat-Log in der Konsole

Der Bedrock-Server schreibt Chatnachrichten normalerweise nicht in die Konsole. Das Egg installiert deshalb ein kleines Behavior-Pack (`behavior_packs/konsolen_chatlog`), das diese Zeilen ausgibt:

```
[Scripting] [Chat] <Spielername> Hallo zusammen
[Scripting] [Tod] Spielername ist gestorben (zombie)
```

Beitritte und Abgänge (`Player connected` / `Player disconnected`) protokolliert der Server ohnehin selbst.

**Wichtig:** Das Chat-Event gibt es nur in der Beta-Script-API. Die Installation aktiviert dafür in der Welt das Experiment **„Beta APIs“** und sichert die alte Datei als `level.dat.bak`. Das Experiment lässt sich in einer Welt nicht wieder abschalten. Wer das nicht möchte, setzt `CHAT_LOG=false` vor der ersten Installation.
Die passende Script-API-Version ermittelt die Installation selbst. Nach einem Bedrock-Update reicht deshalb eine Neuinstallation.

## Import

1. Lade eine der beiden JSON-Dateien herunter (oder beide).
2. Im Panel: **Admin → Nests → (Nest auswählen oder neu anlegen) → Import Egg**.
3. Die JSON-Datei auswählen und importieren.
4. Neuen Server mit dem Egg **Minecraft Bedrock** erstellen.
   Port zum Beispiel `19132`. Pterodactyl gibt den Port automatisch für **TCP und UDP** frei.

## Was ist anders als bei anderen Eggs?

- **Download über die offizielle Mojang-API.** Ältere Eggs lesen die Download-Seite von minecraft.net aus.
  Das klappt nicht mehr, weil die Seite Bots blockiert und sich geändert hat. Die alte Methode bleibt nur als Notlösung drin.
- **Unterstützung für Bedrock ab 1.26:** Seit dieser Version nutzt Bedrock standardmäßig `transport=nethernet`
  (TCP-Signalisierung + UDP). Das Egg setzt `server-port` **und** `server-udp-ports` auf den zugewiesenen Port.
- **Kein Absturz ohne IPv6:** Im alten Modus `raknet` beendet sich der Server, wenn der Container kein IPv6 hat.
  `nethernet` fällt dann sauber auf IPv4 zurück. `server-portv6` wird automatisch auf *Port+1* gesetzt.
- **Allowlist standardmäßig aus:** Neue Bedrock-Versionen schalten die Allowlist ein, dann kann niemand beitreten.
  Im Egg ist sie per Variable aus. Du kannst sie bei Bedarf einschalten.
- **Updates ohne Datenverlust:** Mit *Reinstall* lädt das Egg die neueste Version.
  Welten, `server.properties`, `permissions.json` und `allowlist.json` bleiben erhalten.

## Variablen

| Variable | Standard | Bedeutung |
|---|---|---|
| `BEDROCK_VERSION` | `latest` | `latest`, `preview` oder feste Version (z. B. `1.21.50.10`) |
| `SERVERNAME` | `Bedrock Server` | Name in der Serverliste |
| `GAMEMODE` | `survival` | `survival` / `creative` / `adventure` |
| `DIFFICULTY` | `easy` | `peaceful` / `easy` / `normal` / `hard` |
| `MAX_PLAYERS` | `10` | Maximale Spieleranzahl |
| `LEVEL_NAME` | `Bedrock level` | Weltordner |
| `LEVEL_SEED` | *(leer)* | Seed für neue Welten |
| `ALLOW_CHEATS` | `false` | Cheats erlauben |
| `ONLINE_MODE` | `true` | Xbox-Anmeldung erforderlich |
| `ALLOW_LIST` | `false` | Allowlist aktiv |
| `TRANSPORT` | `nethernet` | `nethernet` (empfohlen) oder `raknet` |
| `PUBLIC_IP` | `auto` | IP, die den Spielern für NetherNet mitgeteilt wird: `auto`, feste IP oder `off` |
| `TELEMETRY` | `true` | `emit-server-telemetry` (Telemetrie an Mojang) |
| `VIEW_DISTANCE` | `32` / `10` | Sichtweite in Chunks (normal / Performance) |
| `TICK_DISTANCE` | `4` | Aktiv berechnete Chunks um Spieler (4–12) |
| `MAX_THREADS` | `8` / `4` | CPU-Threads (0 = unbegrenzt) |
| `CHAT_LOG` | `true` | Chat und Tode in der Konsole (wirksam nach Neuinstallation) |

## Fehlerbehebung

- **Server ist online, aber Beitritt scheitert** (z. B. „Persona konnte nicht installiert werden“, Fehlercode „Terracotta“):
  Bei NetherNet läuft nur die Serverliste über TCP, das Spiel selbst über UDP. Ohne öffentliche IP teilt der Server
  den Spielern die interne Docker-IP (172.x.x.x) mit, und die ist von außen nicht erreichbar.
  `PUBLIC_IP=auto` (Standard) ermittelt die richtige IP. Beim Start steht in der Konsole `NetherNet: oeffentliche Adresse …`.
  Prüfe zusätzlich, dass der Port in der Firewall des Hosts für **TCP und UDP** offen ist.
- **Heimserver / Spielen im LAN:** Trage bei `PUBLIC_IP` die LAN-IP des Hosts ein (z. B. `192.168.1.50`).
  Für Spieler aus dem Internet trägst du die öffentliche IP ein und richtest im Router eine Portweiterleitung für TCP **und** UDP ein.
- **Hilft das alles nicht:** Stelle `TRANSPORT` auf `raknet`. Das klappt nur, wenn der Docker-Container IPv6 hat.
- **`Port [...] may be in use` mit `raknet`:** Meist fehlt IPv6 im Container. Stelle `TRANSPORT` auf `nethernet`.
- **Update:** Unter *Settings → Reinstall Server* neu installieren.

## Entwicklung

Beide JSON-Dateien werden aus `scripts/install.sh` und `scripts/enable_beta_api.py` erzeugt:

```bash
python3 build_egg.py
```
