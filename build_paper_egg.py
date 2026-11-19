#!/usr/bin/env python3
"""Erzeugt das Paper-Egg (Performance) aus scripts/paper/install.sh und scripts/paper/configs/*."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
CFG = ROOT / "scripts" / "paper" / "configs"


def cfg(name):
    return (CFG / name).read_text().replace("\r\n", "\n").rstrip("\n")


install_script = (ROOT / "scripts" / "paper" / "install.sh").read_text().replace("\r\n", "\n")
install_script = (install_script
                  .replace("__PAPER_WORLD_DEFAULTS__", cfg("paper-world-defaults.yml"))
                  .replace("__SPIGOT__", cfg("spigot.yml"))
                  .replace("__BUKKIT__", cfg("bukkit.yml")))

# Hinweis: Pterodactyl fuehrt den Startbefehl ueber "echo ${STARTUP}" + eval aus.
# Mehrfache Leerzeichen werden dabei zu einem - deshalb keine Einrueckungen in Mustern.
AIKAR = (
    "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions "
    "-XX:+DisableExplicitGC -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M "
    "-XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 "
    "-XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 "
    "-XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem "
    "-XX:MaxTenuringThreshold=1 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true"
)

startup = (
    # Pflicht-MOTD
    'if [ -f server.properties ] && ! grep -qiE "^motd=.*craftinghosting\\.free" server.properties; then '
    'sed -i "/^motd=/d" server.properties; echo "motd=craftinghosting.free" >> server.properties; fi; '
    # Velocity-Forwarding (Secret aus dem Panel)
    'VS="{{VELOCITY_SECRET}}"; PG=config/paper-global.yml; '
    'if [ -n "$VS" ]; then sed -i "s/^online-mode=.*/online-mode=false/" server.properties; '
    'if [ -f $PG ]; then sed -i -e "/^ \\{2\\}velocity:/,/^ \\{0,2\\}[^ ]/{s/^\\( \\{4\\}\\)enabled:.*/\\1enabled: true/;'
    "s/^\\( \\{4\\}\\)secret:.*/\\1secret: '$VS'/}\" $PG; fi; "
    'elif [ -f $PG ]; then sed -i "/^ \\{2\\}velocity:/,/^ \\{0,2\\}[^ ]/s/^\\( \\{4\\}\\)enabled:.*/\\1enabled: false/" $PG; fi; '
    # Speicher: wie bisher 90 % des Panel-Limits, bei "unbegrenzt" 85 % des Container-RAMs
    'if [ "{{SERVER_MEMORY}}" -gt 0 ] 2>/dev/null; then MEM="-Xms256M -Xmx$(({{SERVER_MEMORY}} - ({{SERVER_MEMORY}}/10)))M"; '
    'else MEM="-Xms256M -XX:MaxRAMPercentage=85"; fi; '
    "java -XX:+IgnoreUnrecognizedVMOptions $MEM " + AIKAR +
    " -XX:+UseCompactObjectHeaders {{CUSTOM_STARTUP}} -jar {{SERVER_JARFILE}} nogui"
)

config_files = {
    "server.properties": {
        "parser": "properties",
        "find": {
            "server-ip": "0.0.0.0",
            "server-port": "{{server.build.default.port}}",
            "query.port": "{{server.build.default.port}}",
            "motd": "{{server.build.env.MOTD}}",
            "max-players": "{{server.build.env.MAX_PLAYERS}}",
            "view-distance": "{{server.build.env.VIEW_DISTANCE}}",
            "simulation-distance": "{{server.build.env.SIMULATION_DISTANCE}}",
            "online-mode": "{{server.build.env.ONLINE_MODE}}",
            "white-list": "{{server.build.env.WHITELIST}}",
            "difficulty": "{{server.build.env.DIFFICULTY}}",
            "gamemode": "{{server.build.env.GAMEMODE}}",
            "pvp": "{{server.build.env.PVP}}",
            "network-compression-threshold": "{{server.build.env.COMPRESSION_THRESHOLD}}",
            "sync-chunk-writes": "false",
        },
    }
}


def var(name, env, default, desc, rules, viewable=True, editable=True):
    return {"name": name, "description": desc, "env_variable": env, "default_value": default,
            "user_viewable": viewable, "user_editable": editable, "rules": rules, "field_type": "text"}


BOOL = "required|string|in:true,false"

variables = [
    # --- aus dem bisherigen Egg uebernommen ---
    var("Minecraft Version", "MINECRAFT_VERSION", "latest",
        "Minecraft-Version, z.B. 26.3 oder 1.21.11. 'latest' = neueste stabile Version. "
        "Ungueltige Versionen fallen auf latest zurueck.", "nullable|string|max:20"),
    var("Server Jar File", "SERVER_JARFILE", "server.jar",
        "Dateiname der Server-JAR.", "required|regex:/^([\\w\\d._-]+)(\\.jar)$/"),
    var("Download Path", "DL_PATH", "",
        "Eigene Download-URL statt PaperMC. Nicht fuer Nutzer sichtbar.", "nullable|string", False, False),
    var("Build Number", "BUILD_NUMBER", "latest",
        "Paper-Build. 'latest' = neuester Build. Ungueltige Builds fallen auf latest zurueck.",
        "required|string|max:20"),
    # --- neu ---
    var("Zusaetzliche JVM-Flags", "CUSTOM_STARTUP", "",
        "Weitere Java-Parameter (nur Admin). Beispiel: -Dpaper.disableChannelLimit=true",
        "nullable|string|max:512", True, False),
    var("MOTD", "MOTD", "craftinghosting.free",
        "Beschreibung in der Serverliste. Pflicht: muss 'craftinghosting.free' enthalten.",
        "required|string|max:150|regex:/craftinghosting\\.free/i"),
    var("Maximale Spieler", "MAX_PLAYERS", "20", "Maximale Anzahl Spieler.", "required|integer|between:1,1000"),
    var("Sichtweite", "VIEW_DISTANCE", "8",
        "Sichtweite in Chunks (Vanilla: 10). Groesster Hebel fuer RAM/CPU.", "required|integer|between:2,32"),
    var("Simulationsdistanz", "SIMULATION_DISTANCE", "6",
        "In wie vielen Chunks um Spieler Mobs/Redstone/Pflanzen berechnet werden (Vanilla: 10).",
        "required|integer|between:2,32"),
    var("Online-Modus", "ONLINE_MODE", "true",
        "Nur gekaufte Minecraft-Konten (true/false). Wird bei Velocity automatisch auf false gesetzt.", BOOL),
    var("Whitelist", "WHITELIST", "false", "Nur Spieler auf der Whitelist (true/false).", BOOL),
    var("Schwierigkeit", "DIFFICULTY", "easy", "peaceful, easy, normal oder hard.",
        "required|string|in:peaceful,easy,normal,hard"),
    var("Spielmodus", "GAMEMODE", "survival", "survival, creative, adventure oder spectator.",
        "required|string|in:survival,creative,adventure,spectator"),
    var("PvP", "PVP", "true", "Spieler koennen sich angreifen (true/false).", BOOL),
    var("Kompressions-Schwelle", "COMPRESSION_THRESHOLD", "256",
        "Pakete ab dieser Groesse (Byte) werden komprimiert. Hinter Velocity auf -1 setzen.",
        "required|integer|between:-1,65535"),
    var("Velocity-Secret", "VELOCITY_SECRET", "",
        "Inhalt der forwarding.secret des Velocity-Proxys. Gesetzt = Velocity-Modern-Forwarding an "
        "und online-mode aus. Leer = aus.", "nullable|string|max:128|regex:/^[A-Za-z0-9]*$/"),
    var("Optimierte Konfiguration", "OPTIMIZE_CONFIGS", "true",
        "Bei der Installation optimierte paper-world-defaults.yml, spigot.yml und bukkit.yml anlegen "
        "(nur wenn noch nicht vorhanden).", BOOL),
]

egg = {
    "_comment": "Paper Egg fuer Pterodactyl (Performance)",
    "meta": {"version": "PTDL_v2", "update_url": None},
    "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    "name": "Paper",
    "author": "contact@pixelcst.tech",
    "description": "Paper - performanter Minecraft-Java-Server. Aikar-Flags plus Compact Object Headers, "
                   "optimierte Paper/Spigot/Bukkit-Konfiguration, Velocity-Forwarding per Panel. "
                   "Die MOTD muss craftinghosting.free enthalten.",
    "features": ["eula", "java_version", "pid_limit"],
    "docker_images": {
        "Java 25": "ghcr.io/pterodactyl/yolks:java_25",
        "Java 21": "ghcr.io/pterodactyl/yolks:java_21",
        "Java 17": "ghcr.io/pterodactyl/yolks:java_17",
        "Java 16": "ghcr.io/pterodactyl/yolks:java_16",
        "Java 11": "ghcr.io/pterodactyl/yolks:java_11",
        "Java 8": "ghcr.io/pterodactyl/yolks:java_8",
    },
    "file_denylist": [],
    "startup": startup,
    "config": {
        "files": json.dumps(config_files, indent=4),
        "startup": json.dumps({"done": ")! For help, type "}, indent=4),
        "logs": "{}",
        "stop": "stop",
    },
    "scripts": {
        "installation": {
            "script": install_script,
            "container": "ghcr.io/pterodactyl/installers:alpine",
            "entrypoint": "ash",
        }
    },
    "variables": variables,
}

out = ROOT / "egg-paper-performance.json"
out.write_text(json.dumps(egg, indent=4, ensure_ascii=False) + "\n")
print(f"geschrieben: {out}")
