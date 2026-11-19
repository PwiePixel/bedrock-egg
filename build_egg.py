#!/usr/bin/env python3
"""Erzeugt beide Eggs (normal + Performance) aus scripts/install.sh."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
install_script = (ROOT / "scripts" / "install.sh").read_text().replace("\r\n", "\n")
beta_py = (ROOT / "scripts" / "enable_beta_api.py").read_text().replace("\r\n", "\n").rstrip("\n")
install_script = install_script.replace("__ENABLE_BETA_PY__", beta_py)

startup = (
    'if [ -f server.properties ]; then P={{SERVER_PORT}}; U="$P"; IP="{{PUBLIC_IP}}"; '
    'if [ -z "$IP" ] || [ "$IP" = "auto" ]; then IP=""; case "{{SERVER_IP}}" in ""|0.0.0.0|127.*|10.*|192.168.*|172.1[6-9].*|172.2[0-9].*|172.3[0-1].*) ;; *) IP="{{SERVER_IP}}";; esac; '
    'if [ -z "$IP" ]; then IP=$(curl -4 -fsS -m 5 https://api.ipify.org || curl -4 -fsS -m 5 https://ifconfig.me || true); fi; fi; '
    'if [ "$IP" = "off" ]; then IP=""; fi; '
    'if [ -n "$IP" ]; then U="$IP:$P:$P"; echo "NetherNet: oeffentliche Adresse $IP:$P"; fi; '
    'if ! grep -qiE "^server-name=.*craftinghosting\\.free" server.properties; then sed -i "/^server-name=/d" server.properties; echo "server-name=craftinghosting.free" >> server.properties; fi; '
    'for KV in "server-portv6=$((P+1))" "server-udp-ports=$U" "emit-server-telemetry={{TELEMETRY}}"; do '
    'K="${KV%%=*}"; sed -i "/^$K=/d" server.properties; echo "$KV" >> server.properties; done; fi; '
    'LD_LIBRARY_PATH=. ./bedrock_server'
)

VARIANTS = {
    "normal": {
        "file": "egg-minecraft-bedrock.json",
        "name": "Minecraft Bedrock",
        "description": "Offizieller Minecraft Bedrock Dedicated Server (Linux) mit Mojang-Standardwerten. "
                       "Laedt die Version direkt von Mojang, unterstuetzt latest/preview/feste Versionen, "
                       "schreibt Chat und Tode in die Konsole und behaelt beim Update Welten und Einstellungen.",
        "view": "32", "tick": "4", "threads": "8",
        "fixed": {},
    },
    "performance": {
        "file": "egg-minecraft-bedrock-performance.json",
        "name": "Minecraft Bedrock (Performance)",
        "description": "Minecraft Bedrock Dedicated Server, optimiert fuer wenig CPU und RAM: kleinere "
                       "Sichtweite, begrenzte Threads, sparsame Netzwerk-Kompression, Chunk-Aufbau beim "
                       "Client. Schreibt Chat und Tode in die Konsole.",
        "view": "10", "tick": "4", "threads": "4",
        "fixed": {
            "compression-algorithm": "snappy",
            "compression-threshold": "256",
            "client-side-chunk-generation-enabled": "true",
            "enable-lan-visibility": "false",
            "content-log-file-enabled": "false",
        },
    },
}


def config_files(v):
    find = {
        "server-port": "{{server.build.default.port}}",
        "server-name": "{{server.build.env.SERVERNAME}}",
        "gamemode": "{{server.build.env.GAMEMODE}}",
        "difficulty": "{{server.build.env.DIFFICULTY}}",
        "max-players": "{{server.build.env.MAX_PLAYERS}}",
        "level-name": "{{server.build.env.LEVEL_NAME}}",
        "level-seed": "{{server.build.env.LEVEL_SEED}}",
        "allow-cheats": "{{server.build.env.ALLOW_CHEATS}}",
        "online-mode": "{{server.build.env.ONLINE_MODE}}",
        "allow-list": "{{server.build.env.ALLOW_LIST}}",
        "transport": "{{server.build.env.TRANSPORT}}",
        "emit-server-telemetry": "{{server.build.env.TELEMETRY}}",
        "view-distance": "{{server.build.env.VIEW_DISTANCE}}",
        "tick-distance": "{{server.build.env.TICK_DISTANCE}}",
        "max-threads": "{{server.build.env.MAX_THREADS}}",
        "content-log-console-output-enabled": "{{server.build.env.CHAT_LOG}}",
    }
    find.update(v["fixed"])
    return {"server.properties": {"parser": "properties", "find": find}}


def var(name, env, default, desc, rules, editable=True):
    return {
        "name": name,
        "description": desc,
        "env_variable": env,
        "default_value": default,
        "user_viewable": True,
        "user_editable": editable,
        "rules": rules,
        "field_type": "text",
    }


def variables(v):
    return [
        var("Bedrock Version", "BEDROCK_VERSION", "latest",
            "Welche Server-Version installiert wird: 'latest' (aktuelle Version), 'preview' (Vorschau) "
            "oder eine feste Version wie 1.21.50.10. Zum Updaten den Server neu installieren "
            "(Welten und Einstellungen bleiben erhalten).",
            "required|string|max:20"),
        var("Servername", "SERVERNAME", "craftinghosting.free",
            "Der Name, der in der Serverliste angezeigt wird. Pflicht: muss 'craftinghosting.free' enthalten.",
            "required|string|max:64|regex:/craftinghosting\\.free/i"),
        var("Spielmodus", "GAMEMODE", "survival",
            "Standard-Spielmodus: survival, creative oder adventure.",
            "required|string|in:survival,creative,adventure"),
        var("Schwierigkeit", "DIFFICULTY", "easy",
            "Schwierigkeit: peaceful, easy, normal oder hard.",
            "required|string|in:peaceful,easy,normal,hard"),
        var("Maximale Spieler", "MAX_PLAYERS", "10",
            "Maximale Anzahl gleichzeitiger Spieler.", "required|integer|between:1,200"),
        var("Weltname", "LEVEL_NAME", "Bedrock level",
            "Name des Weltordners unter worlds/.", "required|string|max:64"),
        var("Welt-Seed", "LEVEL_SEED", "",
            "Seed fuer neue Welten (leer = zufaellig). Gilt nur beim Erstellen einer neuen Welt.",
            "nullable|string|max:64"),
        var("Cheats erlauben", "ALLOW_CHEATS", "false",
            "Erlaubt Befehle/Cheats (true/false).", "required|string|in:true,false"),
        var("Online-Modus (Xbox-Login)", "ONLINE_MODE", "true",
            "Spieler muessen mit einem Xbox/Microsoft-Konto angemeldet sein (true/false).",
            "required|string|in:true,false"),
        var("Allowlist (Whitelist)", "ALLOW_LIST", "false",
            "Nur Spieler auf der Allowlist duerfen beitreten (true/false). "
            "Spieler hinzufuegen in der Konsole mit: allowlist add <Name>",
            "required|string|in:true,false"),
        var("Netzwerk-Transport", "TRANSPORT", "nethernet",
            "nethernet = neuer Standard ab 1.26 (TCP + UDP auf dem Server-Port, funktioniert auch ohne IPv6). "
            "raknet = klassischer UDP-Modus (benoetigt IPv6 im Container, sonst stuerzt der Server ab).",
            "required|string|in:nethernet,raknet"),
        var("Oeffentliche IP", "PUBLIC_IP", "auto",
            "Nur fuer nethernet: Die IP, ueber die Spieler den Server erreichen. "
            "'auto' = automatisch (Allocation-IP, sonst oeffentliche IP des Hosts), "
            "eine feste IP eintragen (z.B. LAN-IP fuer Heimserver) oder 'off' zum Abschalten. Leer = auto.",
            "nullable|string|max:64"),
        var("Server-Telemetrie", "TELEMETRY", "true",
            "Sendet anonyme Server-Telemetrie an Mojang (emit-server-telemetry, true/false).",
            "required|string|in:true,false"),
        var("Sichtweite", "VIEW_DISTANCE", v["view"],
            "Maximale Sichtweite in Chunks (min. 6). Hoeher = mehr RAM/CPU.",
            "required|integer|between:6,96"),
        var("Tick-Distanz", "TICK_DISTANCE", v["tick"],
            "Wie viele Chunks um Spieler herum aktiv berechnet werden (4-12). Hoeher = mehr CPU.",
            "required|integer|between:4,12"),
        var("Maximale Threads", "MAX_THREADS", v["threads"],
            "Maximale Anzahl CPU-Threads des Servers (0 = so viele wie moeglich).",
            "required|integer|between:0,64"),
        var("Chat-Log in der Konsole", "CHAT_LOG", "true",
            "Schreibt Chatnachrichten und Tode in die Konsole (true/false). Aktiviert dafuer in der Welt "
            "das Experiment 'Beta APIs'. Aenderung wird bei einer Neuinstallation wirksam.",
            "required|string|in:true,false"),
    ]


for v in VARIANTS.values():
    egg = {
        "_comment": "Minecraft Bedrock Dedicated Server Egg fuer Pterodactyl",
        "meta": {"version": "PTDL_v2", "update_url": None},
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "name": v["name"],
        "author": "contact@pixelcst.tech",
        "description": v["description"],
        "features": None,
        "docker_images": {"Debian": "ghcr.io/parkervcp/yolks:debian"},
        "file_denylist": [],
        "startup": startup,
        "config": {
            "files": json.dumps(config_files(v), indent=4),
            "startup": json.dumps({"done": "Server started"}, indent=4),
            "logs": "{}",
            "stop": "stop",
        },
        "scripts": {
            "installation": {
                "script": install_script,
                "container": "ghcr.io/parkervcp/installers:debian",
                "entrypoint": "bash",
            }
        },
        "variables": variables(v),
    }

    out = ROOT / v["file"]
    out.write_text(json.dumps(egg, indent=4, ensure_ascii=False) + "\n")
    print(f"geschrieben: {out}")
