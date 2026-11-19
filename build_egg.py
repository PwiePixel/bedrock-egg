#!/usr/bin/env python3
"""Erzeugt egg-minecraft-bedrock.json aus scripts/install.sh."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
install_script = (ROOT / "scripts" / "install.sh").read_text().replace("\r\n", "\n")

startup = (
    'if [ -f server.properties ]; then P={{SERVER_PORT}}; U="$P"; IP="{{PUBLIC_IP}}"; '
    'if [ "$IP" = "auto" ]; then IP=$(curl -fsS -m 5 https://api.ipify.org || true); fi; '
    'if [ -n "$IP" ]; then U="$IP:$P:$P"; fi; '
    'sed -i -e "s/^server-portv6=.*/server-portv6=$((P+1))/" -e "s/^server-udp-ports=.*/server-udp-ports=$U/" server.properties; fi; '
    'LD_LIBRARY_PATH=. ./bedrock_server'
)

config_files = {
    "server.properties": {
        "parser": "properties",
        "find": {
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
        },
    }
}


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


variables = [
    var("Bedrock Version", "BEDROCK_VERSION", "latest",
        "Welche Server-Version installiert wird: 'latest' (aktuelle Version), 'preview' (Vorschau) "
        "oder eine feste Version wie 1.21.50.10. Zum Updaten den Server neu installieren "
        "(Welten und Einstellungen bleiben erhalten).",
        "required|string|max:20"),
    var("Servername", "SERVERNAME", "Bedrock Server",
        "Der Name, der in der Serverliste angezeigt wird.", "required|string|max:64"),
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
    var("Oeffentliche IP", "PUBLIC_IP", "",
        "Nur fuer nethernet: Oeffentliche IP des Servers, die den Spielern mitgeteilt wird. "
        "Leer lassen = automatisch durch den Server, 'auto' = IP wird beim Start ermittelt, "
        "oder eine feste IP eintragen. Hilft, wenn Spieler beim Beitreten haengen bleiben.",
        "nullable|string|max:64"),
]

egg = {
    "_comment": "Minecraft Bedrock Dedicated Server Egg fuer Pterodactyl",
    "meta": {"version": "PTDL_v2", "update_url": None},
    "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    "name": "Minecraft Bedrock",
    "author": "contact@pixelcst.tech",
    "description": "Offizieller Minecraft Bedrock Dedicated Server (Linux). Laedt die Version direkt "
                   "von Mojang herunter, unterstuetzt latest/preview/feste Versionen und behaelt beim "
                   "Update Welten und Einstellungen.",
    "features": None,
    "docker_images": {"Debian": "ghcr.io/parkervcp/yolks:debian"},
    "file_denylist": [],
    "startup": startup,
    "config": {
        "files": json.dumps(config_files, indent=4),
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
    "variables": variables,
}

out = ROOT / "egg-minecraft-bedrock.json"
out.write_text(json.dumps(egg, indent=4, ensure_ascii=False) + "\n")
print(f"geschrieben: {out}")
