#!/usr/bin/env python3
"""Erzeugt das Velocity-Egg (Performance) aus scripts/velocity/install.sh."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
install_script = (ROOT / "scripts" / "velocity" / "install.sh").read_text().replace("\r\n", "\n")

BRAND = "craftinghosting.free"
BRAND_RULE = "regex:/craftinghosting\\.free/i"
DEFAULT_MOTD = "<#09add3>craftinghosting.free <gray>- Minecraft Proxy"

# Von Velocity empfohlene JVM-Flags (G1, Pre-Touch), Heap relativ zum Container-RAM
startup = (
    f"if [ -f velocity.toml ] && ! grep -qiE '^motd = .*craftinghosting\\.free' velocity.toml; then "
    f"sed -i 's|^motd = .*|motd = \"{DEFAULT_MOTD}\"|' velocity.toml; "
    f"echo 'MOTD muss craftinghosting.free enthalten - Standard-MOTD gesetzt.'; fi; "
    "java -XX:InitialRAMPercentage={{RAM_PERCENT}} -XX:MaxRAMPercentage={{RAM_PERCENT}} "
    "-XX:+UseG1GC -XX:G1HeapRegionSize=4M -XX:+UnlockExperimentalVMOptions "
    "-XX:+ParallelRefProcEnabled -XX:+AlwaysPreTouch -XX:MaxInlineLevel=15 "
    "-XX:+UseStringDeduplication -XX:+DisableExplicitGC "
    "-Dvelocity.packet-decode-logging=false -Dfile.encoding=UTF-8 "
    "-jar velocity.jar"
)

config_files = {
    "velocity.toml": {
        "parser": "file",
        "find": {
            "bind": "bind = \"0.0.0.0:{{server.build.default.port}}\"",
            "motd": "motd = \"{{server.build.env.MOTD}}\"",
            "show-max-players": "show-max-players = {{server.build.env.MAX_PLAYERS}}",
            "online-mode": "online-mode = {{server.build.env.ONLINE_MODE}}",
            "force-key-authentication": "force-key-authentication = {{server.build.env.FORCE_KEY_AUTH}}",
            "prevent-client-proxy-connections": "prevent-client-proxy-connections = {{server.build.env.PREVENT_PROXY_CONNECTIONS}}",
            "player-info-forwarding-mode": "player-info-forwarding-mode = \"{{server.build.env.FORWARDING_MODE}}\"",
            "kick-existing-players": "kick-existing-players = {{server.build.env.KICK_EXISTING}}",
            "lobby": "lobby = \"{{server.build.env.LOBBY_SERVER}}\"",
            "compression-threshold": "compression-threshold = {{server.build.env.COMPRESSION_THRESHOLD}}",
            "compression-level": "compression-level = {{server.build.env.COMPRESSION_LEVEL}}",
            "login-ratelimit": "login-ratelimit = {{server.build.env.LOGIN_RATELIMIT}}",
            "haproxy-protocol": "haproxy-protocol = {{server.build.env.HAPROXY}}",
            "tcp-fast-open": "tcp-fast-open = {{server.build.env.TCP_FAST_OPEN}}",
            "enable-reuse-port": "enable-reuse-port = {{server.build.env.REUSE_PORT}}",
            "log-player-connections": "log-player-connections = {{server.build.env.LOG_CONNECTIONS}}",
            "log-command-executions": "log-command-executions = {{server.build.env.LOG_COMMANDS}}",
            "accepts-transfers": "accepts-transfers = {{server.build.env.ACCEPTS_TRANSFERS}}",
            "enabled": "enabled = {{server.build.env.QUERY_ENABLED}}",
            "port": "port = {{server.build.default.port}}",
        },
    }
}


def var(name, env, default, desc, rules):
    return {
        "name": name, "description": desc, "env_variable": env, "default_value": default,
        "user_viewable": True, "user_editable": True, "rules": rules, "field_type": "text",
    }


BOOL = "required|string|in:true,false"

variables = [
    var("Velocity Version", "VELOCITY_VERSION", "latest",
        "'latest' (neueste stabile Version) oder eine feste Version wie 4.3.1 oder 3.5.1. "
        "Velocity 4.x braucht das Docker-Image Java 25. Update = Server neu installieren.",
        "required|string|max:30"),
    var("MOTD", "MOTD", DEFAULT_MOTD,
        "Beschreibung in der Serverliste (MiniMessage-Format, z.B. <aqua>Text). "
        "Pflicht: muss 'craftinghosting.free' enthalten. Keine Anfuehrungszeichen oder Backslashes.",
        f"required|string|max:300|{BRAND_RULE}|not_regex:/[\"\\\\]/"),
    var("Angezeigte max. Spieler", "MAX_PLAYERS", "500",
        "Maximale Spielerzahl, die in der Serverliste angezeigt wird.", "required|integer|between:0,100000"),
    var("Online-Modus", "ONLINE_MODE", "true",
        "Spieler muessen ein gekauftes Minecraft-Konto haben (true/false).", BOOL),
    var("Forwarding-Modus", "FORWARDING_MODE", "MODERN",
        "Wie Spielerdaten an die Unterserver gehen: MODERN (empfohlen, Paper/Fabric), "
        "BUNGEEGUARD, LEGACY (alte Server/Spigot) oder NONE. Das Secret steht in forwarding.secret.",
        "required|string|in:NONE,LEGACY,BUNGEEGUARD,MODERN"),
    var("Lobby-Server", "LOBBY_SERVER", "127.0.0.1:30066",
        "Adresse (IP:Port) des Lobby-Servers, auf den Spieler zuerst geleitet werden. "
        "Weitere Server in velocity.toml unter [servers] eintragen.",
        "required|string|max:100"),
    var("Key-Authentifizierung erzwingen", "FORCE_KEY_AUTH", "true",
        "Erzwingt signierte Chat-Schluessel (true/false). Bei Problemen mit Plugins auf false.", BOOL),
    var("Bestehende Spieler kicken", "KICK_EXISTING", "false",
        "Bei doppeltem Login den bereits verbundenen Spieler kicken (true/false).", BOOL),
    var("Proxy-Clients verhindern", "PREVENT_PROXY_CONNECTIONS", "false",
        "Verhindert Verbindungen ueber Client-Proxys/VPN-Proxys (true/false).", BOOL),
    var("Kompressions-Schwelle", "COMPRESSION_THRESHOLD", "256",
        "Pakete ab dieser Groesse (Byte) werden komprimiert. -1 = aus.", "required|integer|between:-1,65535"),
    var("Kompressions-Level", "COMPRESSION_LEVEL", "4",
        "zlib-Level 1-9 (-1 = Standard 6). Niedriger = weniger CPU, etwas mehr Bandbreite.",
        "required|integer|between:-1,9"),
    var("Login-Ratelimit (ms)", "LOGIN_RATELIMIT", "3000",
        "Mindestabstand zwischen Logins derselben IP in Millisekunden (Schutz vor Bot-Angriffen).",
        "required|integer|between:0,600000"),
    var("TCP Fast Open", "TCP_FAST_OPEN", "true",
        "Schnellerer Verbindungsaufbau unter Linux (true/false).", BOOL),
    var("Reuse-Port", "REUSE_PORT", "true",
        "Mehrere Threads nehmen Verbindungen an - bessere Performance unter Linux (true/false).", BOOL),
    var("HAProxy-Protokoll", "HAPROXY", "false",
        "Nur aktivieren, wenn ein HAProxy/TCPShield davor sitzt (true/false).", BOOL),
    var("Verbindungen loggen", "LOG_CONNECTIONS", "true",
        "Beitritte/Wechsel/Abgaenge in der Konsole (true/false).", BOOL),
    var("Befehle loggen", "LOG_COMMANDS", "false",
        "Von Spielern ausgefuehrte Proxy-Befehle in der Konsole (true/false).", BOOL),
    var("Transfers akzeptieren", "ACCEPTS_TRANSFERS", "false",
        "Transfer-Pakete von anderen Servern annehmen (true/false).", BOOL),
    var("Query aktivieren", "QUERY_ENABLED", "false",
        "GS4-Query auf dem Proxy-Port fuer Statusseiten (true/false).", BOOL),
    var("RAM-Anteil fuer Java (%)", "RAM_PERCENT", "75",
        "Wie viel Prozent des Panel-RAM-Limits Java als Heap nutzt. Rest bleibt fuer Netzwerk-Puffer.",
        "required|integer|between:30,90"),
]

egg = {
    "_comment": "Velocity Proxy Egg fuer Pterodactyl",
    "meta": {"version": "PTDL_v2", "update_url": None},
    "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    "name": "Velocity (Performance)",
    "author": "contact@pixelcst.tech",
    "description": "Velocity - schneller, moderner Proxy fuer Minecraft Java Edition. Laedt Velocity direkt "
                   "von PaperMC (mit Pruefsumme), optimierte JVM-Flags, sparsame Kompression, TCP Fast Open. "
                   "Die MOTD muss craftinghosting.free enthalten.",
    "features": None,
    "docker_images": {
        "Java 25 (Velocity 4.x)": "ghcr.io/pterodactyl/yolks:java_25",
        "Java 21 (Velocity 3.x)": "ghcr.io/pterodactyl/yolks:java_21",
    },
    "file_denylist": [],
    "startup": startup,
    "config": {
        "files": json.dumps(config_files, indent=4),
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
