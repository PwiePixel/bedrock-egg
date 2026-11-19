#!/usr/bin/env python3
"""Erzeugt das Velocity-Egg (Performance) aus scripts/velocity/install.sh.

Alle Einstellungen werden beim Start in velocity.toml geschrieben. Ist eine Variable leer
(z.B. bei Servern, die vor einem Egg-Update angelegt wurden, oder bei automatisch angelegten
Servern), greift der hier festgelegte Standardwert - der Server startet also immer.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
EGG_REVISION = "3"  # bei jeder Aenderung am Startbefehl erhoehen
install_script = (ROOT / "scripts" / "velocity" / "install.sh").read_text().replace("\r\n", "\n")

DEFAULT_MOTD = "<#09add3>craftinghosting.free <gray>- Minecraft Proxy"
BOOL = "nullable|string|in:true,false"

# (toml-Schluessel, Variable, Standardwert, Typ, Panel-Name, Beschreibung, Regeln)
#   Typ "str"  -> Wert wird in Anfuehrungszeichen geschrieben
#   Typ "raw"  -> Zahl / true / false
SETTINGS = [
    ("show-max-players", "MAX_PLAYERS", "500", "raw", "Angezeigte max. Spieler",
     "Maximale Spielerzahl in der Serverliste.", "nullable|integer|between:0,100000"),
    ("online-mode", "ONLINE_MODE", "true", "raw", "Online-Modus",
     "Spieler muessen ein gekauftes Minecraft-Konto haben (true/false).", BOOL),
    ("player-info-forwarding-mode", "FORWARDING_MODE", "MODERN", "str", "Forwarding-Modus",
     "MODERN (empfohlen, Paper/Fabric), BUNGEEGUARD, LEGACY (Spigot/alt) oder NONE. "
     "Das Secret steht in forwarding.secret.", "nullable|string|in:NONE,LEGACY,BUNGEEGUARD,MODERN"),
    ("lobby", "LOBBY_SERVER", "127.0.0.1:30066", "str", "Lobby-Server",
     "Adresse (IP:Port) des Lobby-Servers. Weitere Server in velocity.toml unter [servers].",
     "nullable|string|max:100|regex:/^[A-Za-z0-9.:_-]*$/"),
    ("force-key-authentication", "FORCE_KEY_AUTH", "true", "raw", "Key-Authentifizierung erzwingen",
     "Erzwingt signierte Chat-Schluessel (true/false). Bei Plugin-Problemen auf false.", BOOL),
    ("kick-existing-players", "KICK_EXISTING", "false", "raw", "Bestehende Spieler kicken",
     "Bei doppeltem Login den bereits verbundenen Spieler kicken (true/false).", BOOL),
    ("prevent-client-proxy-connections", "PREVENT_PROXY_CONNECTIONS", "false", "raw", "Proxy-Clients verhindern",
     "Verhindert Verbindungen ueber Client-Proxys (true/false).", BOOL),
    ("compression-threshold", "COMPRESSION_THRESHOLD", "256", "raw", "Kompressions-Schwelle",
     "Pakete ab dieser Groesse (Byte) werden komprimiert. -1 = aus.", "nullable|integer|between:-1,65535"),
    ("compression-level", "COMPRESSION_LEVEL", "4", "raw", "Kompressions-Level",
     "zlib-Level 1-9 (-1 = Standard 6). Niedriger = weniger CPU.", "nullable|integer|between:-1,9"),
    ("login-ratelimit", "LOGIN_RATELIMIT", "3000", "raw", "Login-Ratelimit (ms)",
     "Mindestabstand zwischen Logins derselben IP in Millisekunden.", "nullable|integer|between:0,600000"),
    ("tcp-fast-open", "TCP_FAST_OPEN", "true", "raw", "TCP Fast Open",
     "Schnellerer Verbindungsaufbau unter Linux (true/false).", BOOL),
    ("enable-reuse-port", "REUSE_PORT", "true", "raw", "Reuse-Port",
     "Mehrere Threads nehmen Verbindungen an (true/false).", BOOL),
    ("haproxy-protocol", "HAPROXY", "false", "raw", "HAProxy-Protokoll",
     "Nur aktivieren, wenn ein HAProxy/TCPShield davor sitzt (true/false).", BOOL),
    ("log-player-connections", "LOG_CONNECTIONS", "true", "raw", "Verbindungen loggen",
     "Beitritte/Wechsel/Abgaenge in der Konsole (true/false).", BOOL),
    ("log-command-executions", "LOG_COMMANDS", "false", "raw", "Befehle loggen",
     "Von Spielern ausgefuehrte Proxy-Befehle in der Konsole (true/false).", BOOL),
    ("accepts-transfers", "ACCEPTS_TRANSFERS", "false", "raw", "Transfers akzeptieren",
     "Transfer-Pakete von anderen Servern annehmen (true/false).", BOOL),
    ("enabled", "QUERY_ENABLED", "false", "raw", "Query aktivieren",
     "GS4-Query auf dem Proxy-Port (true/false).", BOOL),
]


def setting_cmd(key, env, default, kind):
    val = f"${{{env}:-{default}}}"
    return f'T {key} "\\"{val}\\""; ' if kind == "str" else f'T {key} "{val}"; '


# Hinweis: Das Java-Image von Pterodactyl (yolks:java_*) wertet den Startbefehl nur mit
# "eval echo" aus und startet das Ergebnis dann OHNE Shell ("exec env ...").
# Deshalb laeuft die gesamte Vorbereitung in einer Befehlsersetzung $( ... ), die nichts
# ausgibt - uebrig bleibt nur der java-Befehl. Funktioniert auch mit Entrypoints, die "eval" nutzen.
# Keine doppelten Leerzeichen verwenden (manche Entrypoints fassen sie zusammen).
startup = (
    '$({ echo "craftinghosting.free Egg Rev. ' + EGG_REVISION + '" >&2; '
    # velocity.toml anlegen, falls sie fehlt (z.B. Installation nie gelaufen)
    'if [ ! -f velocity.toml ] && [ -f velocity.jar ]; then '
    '{ unzip -p velocity.jar default-velocity.toml > velocity.toml 2>/dev/null && [ -s velocity.toml ]; } || '
    '{ rm -f velocity.toml; jar xf velocity.jar default-velocity.toml 2>/dev/null && mv default-velocity.toml velocity.toml; } || '
    # letzte Moeglichkeit: Velocity kurz starten, damit es die Standarddatei selbst schreibt
    '{ rm -f velocity.toml; java -jar velocity.jar < /dev/null > /dev/null 2>&1 & VP=$!; '
    'for i in $(seq 1 60); do [ -s velocity.toml ] && break; sleep 0.5; done; sleep 1; kill $VP 2>/dev/null; wait $VP 2>/dev/null; true; }; fi; '
    # Helfer: Zeile "schluessel = ..." ersetzen (ohne Sonderzeichen-Probleme)
    "T() { K=\"$1\" V=\"$2\" awk 'index($0,ENVIRON[\"K\"]\" =\")==1{print ENVIRON[\"K\"]\" = \"ENVIRON[\"V\"];next}{print}' "
    'velocity.toml > velocity.toml.tmp && mv velocity.toml.tmp velocity.toml; }; '
    'if [ -f velocity.toml ]; then '
    # Pflicht-MOTD: leer oder ohne craftinghosting.free -> Standard; Anfuehrungszeichen/Backslashes entfernen
    f'M="${{MOTD:-{DEFAULT_MOTD}}}"; M=$(printf "%s" "$M" | tr -d "\\"\\\\\\\\"); '
    f'if ! printf "%s" "$M" | grep -qi "craftinghosting\\.free"; then M="{DEFAULT_MOTD}"; '
    'echo "MOTD muss craftinghosting.free enthalten - Standard-MOTD gesetzt." >&2; fi; '
    'T bind "\\"0.0.0.0:${SERVER_PORT:-25565}\\""; T motd "\\"$M\\""; T port "${SERVER_PORT:-25565}"; '
    + "".join(setting_cmd(k, e, d, t) for k, e, d, t, *_ in SETTINGS) +
    'fi; } > /dev/null) '
    "java -XX:InitialRAMPercentage=${RAM_PERCENT:-75} -XX:MaxRAMPercentage=${RAM_PERCENT:-75} "
    "-XX:+UseG1GC -XX:G1HeapRegionSize=4M -XX:+UnlockExperimentalVMOptions "
    "-XX:+ParallelRefProcEnabled -XX:+AlwaysPreTouch -XX:MaxInlineLevel=15 "
    "-XX:+UseStringDeduplication -XX:+DisableExplicitGC "
    "-Dvelocity.packet-decode-logging=false -Dfile.encoding=UTF-8 "
    "-jar velocity.jar"
)


def var(name, env, default, desc, rules):
    return {"name": name, "description": desc, "env_variable": env, "default_value": default,
            "user_viewable": True, "user_editable": True, "rules": rules, "field_type": "text"}


variables = [
    var("Velocity Version", "VELOCITY_VERSION", "latest",
        "'latest' (neueste stabile Version) oder fest, z.B. 4.3.1 oder 3.5.1. Leer = latest. "
        "Velocity 4.x braucht das Docker-Image Java 25. Update = Server neu installieren.",
        "nullable|string|max:30"),
    var("MOTD", "MOTD", DEFAULT_MOTD,
        "Beschreibung in der Serverliste (MiniMessage, z.B. <aqua>Text). Pflicht: muss "
        "'craftinghosting.free' enthalten - sonst/leer wird automatisch die Standard-MOTD genutzt.",
        "nullable|string|max:300|regex:/craftinghosting\\.free/i|not_regex:/[\"\\\\]/"),
]
variables += [var(n, e, d, desc, r) for _, e, d, _, n, desc, r in SETTINGS]
variables.append(var("RAM-Anteil fuer Java (%)", "RAM_PERCENT", "75",
                     "Prozent des Panel-RAM-Limits fuer den Java-Heap. Leer = 75.",
                     "nullable|integer|between:30,90"))

egg = {
    "_comment": "Velocity Proxy Egg fuer Pterodactyl",
    "meta": {"version": "PTDL_v2", "update_url": None},
    "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    "name": "Velocity (Performance) Rev. " + EGG_REVISION,
    "author": "contact@pixelcst.tech",
    "description": "Rev. " + EGG_REVISION + " - Velocity - schneller, moderner Proxy fuer Minecraft Java Edition. Laedt Velocity direkt "
                   "von PaperMC (mit Pruefsumme), optimierte JVM-Flags, sparsame Kompression, TCP Fast Open. "
                   "Alle Variablen haben Standardwerte - der Server startet auch ohne Eingaben. "
                   "Die MOTD muss craftinghosting.free enthalten.",
    "features": None,
    "docker_images": {
        "Java 25 (Velocity 4.x)": "ghcr.io/pterodactyl/yolks:java_25",
        "Java 21 (Velocity 3.x)": "ghcr.io/pterodactyl/yolks:java_21",
    },
    "file_denylist": [],
    "startup": startup,
    "config": {
        "files": "{}",
        "startup": json.dumps({"done": "Done ("}, indent=4),
        "logs": "{}",
        "stop": "end",
    },
    "scripts": {
        "installation": {
            "script": install_script,
            "container": "ghcr.io/parkervcp/installers:debian",
            "entrypoint": "bash",
        }
    },
    "variables": variables,
}

out = ROOT / "egg-velocity-performance.json"
out.write_text(json.dumps(egg, indent=4, ensure_ascii=False) + "\n")
print(f"geschrieben: {out}")
