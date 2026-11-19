# Minecraft Bedrock Egg für Pterodactyl

Ein funktionierendes Egg für den offiziellen **Minecraft Bedrock Dedicated Server** (Linux).
Getestet mit Bedrock **1.26.66.1**, also auch mit dem neuen Netzwerk-Transport *NetherNet*.

## Import

1. Lade die Datei [`egg-minecraft-bedrock.json`](egg-minecraft-bedrock.json) herunter.
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
| `PUBLIC_IP` | *(leer)* | Öffentliche IP für NetherNet. `auto` ermittelt sie beim Start |

## Fehlerbehebung

- **Spieler bleiben beim Beitreten hängen (NetherNet):** Setze `PUBLIC_IP` auf die öffentliche IP des Servers oder auf `auto`.
  Prüfe außerdem, dass der Port in der Firewall des Hosts für **TCP und UDP** offen ist.
- **`Port [...] may be in use` mit `raknet`:** Meist fehlt IPv6 im Container. Stelle `TRANSPORT` auf `nethernet`.
- **Update:** Unter *Settings → Reinstall Server* neu installieren.

## Entwicklung

Die JSON-Datei wird aus `scripts/install.sh` erzeugt:

```bash
python3 build_egg.py
```
