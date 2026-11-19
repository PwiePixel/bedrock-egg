# Minecraft Eggs für Pterodactyl – craftinghosting.free

Eggs für **Minecraft Bedrock**, **PocketMine-MP**, **Paper** (Java) und den Java-Proxy **Velocity**.

## Übersicht

| Datei | Software | Variante |
|---|---|---|
| [`egg-minecraft-bedrock.json`](egg-minecraft-bedrock.json) | Bedrock Dedicated Server | Normal |
| [`egg-minecraft-bedrock-performance.json`](egg-minecraft-bedrock-performance.json) | Bedrock Dedicated Server | Performance |
| [`egg-pocketmine-mp.json`](egg-pocketmine-mp.json) | PocketMine-MP | Normal |
| [`egg-pocketmine-mp-performance.json`](egg-pocketmine-mp-performance.json) | PocketMine-MP | Performance |
| [`egg-velocity-performance.json`](egg-velocity-performance.json) | Velocity (Java-Proxy) | Performance |
| [`egg-paper-performance.json`](egg-paper-performance.json) | Paper (Java-Server) | Performance |

### Branding: `craftinghosting.free` ist Pflicht

In **allen** Eggs muss der Servername bzw. die MOTD `craftinghosting.free` enthalten (Groß-/Kleinschreibung egal).
Standardwert ist jeweils `craftinghosting.free`.

1. **Panel-Prüfung:** Die Variable hat die Regel `regex:/craftinghosting\.free/i`. Ein Name ohne den Text lässt sich nicht speichern.
2. **Prüfung beim Start:** Fehlt der Text trotzdem (z. B. durch Bearbeiten der Datei), setzt der Startbefehl automatisch den Standardnamen.


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
- **Gespeicherte Server-Identität:** Die Installation führt einmal `serveridentity save` aus (`keys/server_identity_key.pem`).
  So behält der Server bei jedem Neustart dieselbe Identität, und Spieler werden nicht jedes Mal gefragt, ob sie dem Server vertrauen.
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

## PocketMine-MP

PocketMine-MP ist eine Bedrock-Server-Software in PHP mit Plugin-Unterstützung (Plugins: [Poggit](https://poggit.pmmp.io/plugins)).

| Datei | Für wen | Unterschied |
|---|---|---|
| [`egg-pocketmine-mp.json`](egg-pocketmine-mp.json) | Normaler Server | PHP 8.2 (offiziell), Sichtweite 16, PocketMine-Standardwerte |
| [`egg-pocketmine-mp-performance.json`](egg-pocketmine-mp-performance.json) | Wenig CPU/RAM | PHP 8.4, Sichtweite 8, Tick-Radius 2, 3 Chunks/Tick, Kompression Level 4 asynchron, 2 Worker, weiches Speicherlimit (75 %) |

**Was das Egg macht:**
- Lädt `PocketMine-MP.phar` (`latest` oder feste Version) und die passenden PHP-Binaries von den offiziellen Releases.
- Startet ohne Einrichtungsassistent. Die „Fertig“-Meldung wird in jeder Sprache erkannt.
- **IPv6 ist standardmäßig aus**, weil PocketMine sonst in Containern ohne IPv6 beim Start abstürzt.
- Das Speicherlimit richtet sich automatisch nach dem RAM-Limit im Panel (`MEMORY_LIMIT=auto` → 85 %).
- Der automatische Updater ist aus. Updates laufen über *Reinstall*, Welten, Plugins und Einstellungen bleiben erhalten.
- Chat schreibt PocketMine von Haus aus in die Konsole.

**Einstellbar im Panel:** Version, PHP-Version, MOTD, max. Spieler, Sprache, Whitelist, Xbox-Anmeldung, Query, IPv6,
Spielmodus (auch erzwingen), Schwierigkeit, Hardcore, PvP, Weltname/-seed/-typ, Autosave und Intervall,
Sichtweite, Chunks pro Tick, Tick-Radius, Kompressions-Level, asynchrone Kompression, Async-Worker, Speicherlimit, Debug.

**Hinweis:** PocketMine-MP unterstützt immer nur bestimmte Bedrock-Versionen (5.44.3 → Bedrock 26.30) und nutzt RakNet (UDP).
Ist die Minecraft-App neuer als die unterstützte Version, kann man erst beitreten, wenn PocketMine ein Update herausbringt.
Danach reicht eine Neuinstallation.

## Velocity (Minecraft Java Proxy)

[`egg-velocity-performance.json`](egg-velocity-performance.json) – auf Performance getrimmt:

- Lädt Velocity direkt über die PaperMC-API (`latest` = neueste **stabile** Version, oder fest z. B. `4.3.1` / `3.5.1`) und prüft die SHA-256-Prüfsumme.
- Docker-Image **Java 25** (für Velocity 4.x) oder **Java 21** (für 3.x) wählbar.
- JVM-Flags nach Velocity-Empfehlung: G1GC, 4M-Regionen, AlwaysPreTouch, MaxInlineLevel=15, String-Deduplizierung. Der Heap richtet sich automatisch nach dem Panel-RAM (`RAM_PERCENT`, Standard 75 %).
- Netzwerk: Kompression ab 256 Byte mit Level 4 (weniger CPU), **TCP Fast Open** und **Reuse-Port** (mehrere Accept-Threads) aktiv.
- `velocity.toml` wird bei der Installation aus der JAR erzeugt (ohne Beispiel-Server). So stimmt der Port schon beim ersten Start.
- Stoppen mit `end`.

**Im Panel einstellbar:** Version, MOTD (Pflicht: `craftinghosting.free`), angezeigte max. Spieler, Online-Modus, Forwarding-Modus
(`MODERN`/`BUNGEEGUARD`/`LEGACY`/`NONE`), Lobby-Server, Key-Authentifizierung, doppelte Logins kicken, Client-Proxys verhindern,
Kompressions-Schwelle/-Level, Login-Ratelimit, TCP Fast Open, Reuse-Port, HAProxy-Protokoll, Verbindungen/Befehle loggen,
Transfers, Query, RAM-Anteil.

**Unterserver anbinden (MODERN-Forwarding):**
1. In Paper (`config/paper-global.yml`): `proxies.velocity.enabled: true`, `online-mode: true`, `secret:` = Inhalt von `forwarding.secret` aus dem Velocity-Server.
2. In der `server.properties` des Unterservers `online-mode=false`.
3. Weitere Server in `velocity.toml` unter `[servers]` eintragen. Der Lobby-Server kommt aus der Panel-Variable.

## Paper (Minecraft Java Server)

[`egg-paper-performance.json`](egg-paper-performance.json) basiert auf dem Standard-Paper-Egg. Name („Paper“), Variablen und Aikar-Flags
bleiben gleich, ein bestehendes Egg lässt sich also mit „Update Egg“ ersetzen.

**Verbesserungen gegenüber dem Standard-Egg:**
- **Startbefehl:** Die Aikar-Flags bleiben. Dazu kommen `-XX:+UseCompactObjectHeaders` (von PaperMC für Java 25 empfohlen, spart RAM; auf älterem Java wird der Flag
  dank `-XX:+IgnoreUnrecognizedVMOptions` ignoriert) und `nogui`. Bei „unbegrenztem“ RAM (`SERVER_MEMORY=0`) wird nicht mehr `-Xmx0M` erzeugt,
  sondern 85 % des Container-RAMs genutzt. `{{CUSTOM_STARTUP}}` hat jetzt eine Variable (nur Admin).
- **Installation:** `latest` nimmt nur stabile Versionen (keine `-rc`/`-pre`). Die SHA-256-Prüfsumme wird kontrolliert, ungültige Builds fallen sauber auf den neuesten zurück.
- **Optimierte Konfiguration** (nur bei Neuinstallation, bestehende Dateien bleiben unangetastet):
  - `paper-world-defaults.yml`: Alternate-Current-Redstone, optimierte Explosionen, max. 2 Entity-Kollisionen, 8 Chunks Autosave pro Tick,
    Limits für Pfeile/XP-Orbs pro Chunk, Schatzkarten ohne Lag-Suche, langsamere Gras-/Spawner-Ticks.
  - `spigot.yml`: kleinere Entity-Activation-Ranges, inaktive Dorfbewohner nicht ticken, Item/XP-Merge.
  - `bukkit.yml`: geringere Spawn-Limits, Monster-Spawns alle 4 Ticks.
  - `server.properties`: Sichtweite 8, Simulationsdistanz 6, `sync-chunk-writes=false`.
- **Velocity per Panel:** Den Inhalt der `forwarding.secret` des Velocity-Proxys bei `VELOCITY_SECRET` eintragen. Dann sind Modern-Forwarding
  und `online-mode=false` automatisch gesetzt. Leer = Velocity aus.
- **MOTD-Pflicht** `craftinghosting.free` wie bei allen Eggs.

## Entwicklung

Beide JSON-Dateien werden aus `scripts/install.sh` und `scripts/enable_beta_api.py` erzeugt:

```bash
python3 build_egg.py
python3 build_pocketmine_egg.py
python3 build_velocity_egg.py
python3 build_paper_egg.py
```
