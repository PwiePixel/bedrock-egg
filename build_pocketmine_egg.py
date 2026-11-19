#!/usr/bin/env python3
"""Erzeugt beide PocketMine-MP-Eggs (normal + Performance) aus scripts/pocketmine/install.sh."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
install_script = (ROOT / "scripts" / "pocketmine" / "install.sh").read_text().replace("\r\n", "\n")

VARIANTS = {
    "normal": {
        "file": "egg-pocketmine-mp.json",
        "name": "PocketMine-MP",
        "description": "PocketMine-MP Server (Minecraft Bedrock, PHP) mit Plugin-Unterstuetzung. "
                       "Laedt PocketMine-MP und die passenden PHP-Binaries direkt von den offiziellen "
                       "Releases. Viele Einstellungen direkt im Panel. Chat wird in der Konsole geloggt.",
        "php": "8.2", "view": "16", "workers": "auto", "per_tick": "4", "tick_radius": "3",
        "compression": "6", "async_compression": "false", "autosave": "6000",
        "global_limit_percent": 0,
    },
    "performance": {
        "file": "egg-pocketmine-mp-performance.json",
        "name": "PocketMine-MP (Performance)",
        "description": "PocketMine-MP Server, optimiert fuer wenig CPU und RAM: PHP 8.4, Sichtweite 8, "
                       "weniger Chunk-Ticking, sparsamere Kompression (asynchron), begrenzte Worker und "
                       "automatisches Speicher-Management. Chat wird in der Konsole geloggt.",
        "php": "8.4", "view": "8", "workers": "2", "per_tick": "3", "tick_radius": "2",
        "compression": "4", "async_compression": "true", "autosave": "6000",
        "global_limit_percent": 75,
    },
}


def startup(v):
    gl = ""
    if v["global_limit_percent"]:
        gl = f'--memory.global-limit=$(( M * {v["global_limit_percent"]} / 100 )) '
    return (
        'if [ -f server.properties ] && ! grep -qiE "^motd=.*craftinghosting\\.free" server.properties; then '
        'sed -i "/^motd=/d" server.properties; echo "motd=craftinghosting.free" >> server.properties; fi; '
        'EXT=$(ls -d $PWD/bin/php7/lib/php/extensions/no-debug-zts-* | head -n 1); '
        'sed -i "s#^zend_extension=.*opcache.so#zend_extension=$EXT/opcache.so#" bin/php7/bin/php.ini; '
        'B() { if [ "$1" = "true" ]; then echo 1; else echo 0; fi; }; '
        'M="{{MEMORY_LIMIT}}"; if [ -z "$M" ] || [ "$M" = "auto" ]; then M=0; '
        'if [ "{{SERVER_MEMORY}}" -gt 0 ] 2>/dev/null; then M=$(( {{SERVER_MEMORY}} * 85 / 100 )); fi; fi; '
        './bin/php7/bin/php ./PocketMine-MP.phar --no-wizard --enable-ansi '
        '--auto-updater.enabled=0 --console.title-tick=0 '
        '--memory.main-hard-limit=$M ' + gl +
        '--settings.async-workers={{ASYNC_WORKERS}} '
        '--chunk-sending.per-tick={{CHUNKS_PER_TICK}} '
        '--chunk-ticking.tick-radius={{TICK_RADIUS}} '
        '--network.compression-level={{COMPRESSION_LEVEL}} '
        '--network.async-compression=$(B {{ASYNC_COMPRESSION}}) '
        '--ticks-per.autosave={{AUTOSAVE_TICKS}} '
        '--debug.level=$(if [ "{{DEBUG}}" = "true" ]; then echo 2; else echo 1; fi)'
    )


def config_files():
    find = {
        "server-port": "{{server.build.default.port}}",
        "server-portv6": "{{server.build.default.port}}",
        "enable-ipv6": "{{server.build.env.ENABLE_IPV6}}",
        "motd": "{{server.build.env.SERVERNAME}}",
        "max-players": "{{server.build.env.MAX_PLAYERS}}",
        "gamemode": "{{server.build.env.GAMEMODE}}",
        "force-gamemode": "{{server.build.env.FORCE_GAMEMODE}}",
        "difficulty": "{{server.build.env.DIFFICULTY}}",
        "hardcore": "{{server.build.env.HARDCORE}}",
        "pvp": "{{server.build.env.PVP}}",
        "level-name": "{{server.build.env.LEVEL_NAME}}",
        "level-seed": "{{server.build.env.LEVEL_SEED}}",
        "level-type": "{{server.build.env.LEVEL_TYPE}}",
        "white-list": "{{server.build.env.WHITELIST}}",
        "xbox-auth": "{{server.build.env.XBOX_AUTH}}",
        "view-distance": "{{server.build.env.VIEW_DISTANCE}}",
        "enable-query": "{{server.build.env.ENABLE_QUERY}}",
        "auto-save": "{{server.build.env.AUTO_SAVE}}",
        "language": "{{server.build.env.LANGUAGE}}",
    }
    return {"server.properties": {"parser": "properties", "find": find}}


def var(name, env, default, desc, rules):
    return {
        "name": name,
        "description": desc,
        "env_variable": env,
        "default_value": default,
        "user_viewable": True,
        "user_editable": True,
        "rules": rules,
        "field_type": "text",
    }


BOOL = "required|string|in:true,false"


def variables(v):
    return [
        # --- Installation ---
        var("PocketMine-MP Version", "PM_VERSION", "latest",
            "'latest' oder eine feste Version wie 5.44.3. Zum Updaten den Server neu installieren "
            "(Welten, Plugins und Einstellungen bleiben erhalten).", "required|string|max:30"),
        var("PHP Version", "PHP_VERSION", v["php"],
            "PHP-Version der offiziellen PocketMine-Binaries (8.2, 8.3, 8.4 oder 8.5). "
            "Aenderung wird bei einer Neuinstallation wirksam.", "required|string|in:8.2,8.3,8.4,8.5"),
        # --- Server ---
        var("Servername (MOTD)", "SERVERNAME", "craftinghosting.free",
            "Name des Servers in der Serverliste. Pflicht: muss 'craftinghosting.free' enthalten.",
            "required|string|max:100|regex:/craftinghosting\\.free/i"),
        var("Maximale Spieler", "MAX_PLAYERS", "20",
            "Maximale Anzahl gleichzeitiger Spieler.", "required|integer|between:1,1000"),
        var("Sprache", "LANGUAGE", "deu",
            "Sprache der Server-Meldungen (z.B. deu, eng, fra, ita, spa, jpn, kor).",
            "required|string|max:5"),
        var("Whitelist", "WHITELIST", "false",
            "Nur Spieler auf der Whitelist duerfen beitreten (true/false). Hinzufuegen: whitelist add <Name>", BOOL),
        var("Xbox-Anmeldung", "XBOX_AUTH", "true",
            "Spieler muessen mit einem Xbox/Microsoft-Konto angemeldet sein (true/false).", BOOL),
        var("Query aktivieren", "ENABLE_QUERY", "true",
            "GS4-Query fuer Serverlisten/Statusseiten (true/false).", BOOL),
        var("IPv6 aktivieren", "ENABLE_IPV6", "false",
            "Nur aktivieren, wenn der Docker-Container IPv6 hat - sonst stuerzt der Server beim Start ab.", BOOL),
        # --- Spiel ---
        var("Spielmodus", "GAMEMODE", "survival",
            "survival, creative, adventure oder spectator.",
            "required|string|in:survival,creative,adventure,spectator"),
        var("Spielmodus erzwingen", "FORCE_GAMEMODE", "false",
            "Spieler erhalten beim Beitritt immer den Standard-Spielmodus (true/false).", BOOL),
        var("Schwierigkeit", "DIFFICULTY", "normal",
            "peaceful, easy, normal oder hard.", "required|string|in:peaceful,easy,normal,hard"),
        var("Hardcore", "HARDCORE", "false", "Hardcore-Modus (true/false).", BOOL),
        var("PvP", "PVP", "true", "Spieler koennen sich gegenseitig angreifen (true/false).", BOOL),
        # --- Welt ---
        var("Weltname", "LEVEL_NAME", "world", "Name der Standardwelt (Ordner unter worlds/).",
            "required|string|max:64"),
        var("Welt-Seed", "LEVEL_SEED", "", "Seed fuer neue Welten (leer = zufaellig).",
            "nullable|string|max:64"),
        var("Welttyp", "LEVEL_TYPE", "DEFAULT", "Generator fuer neue Welten: DEFAULT, FLAT oder NETHER.",
            "required|string|in:DEFAULT,NORMAL,FLAT,NETHER,default,normal,flat,nether"),
        var("Automatisch speichern", "AUTO_SAVE", "true", "Welten automatisch speichern (true/false).", BOOL),
        var("Speicher-Intervall (Ticks)", "AUTOSAVE_TICKS", v["autosave"],
            "Wie oft automatisch gespeichert wird, in Ticks (20 Ticks = 1 Sekunde, 6000 = 5 Minuten).",
            "required|integer|between:200,72000"),
        # --- Performance ---
        var("Sichtweite", "VIEW_DISTANCE", v["view"],
            "Maximale Sichtweite in Chunks. Hoeher = mehr RAM/CPU.", "required|integer|between:2,64"),
        var("Chunks pro Tick", "CHUNKS_PER_TICK", v["per_tick"],
            "Wie viele Chunks pro Tick an Spieler gesendet werden. Niedriger = weniger Lastspitzen.",
            "required|integer|between:1,32"),
        var("Tick-Radius", "TICK_RADIUS", v["tick_radius"],
            "Radius in Chunks um Spieler, in dem Bloecke/Pflanzen aktiv berechnet werden.",
            "required|integer|between:1,10"),
        var("Kompressions-Level", "COMPRESSION_LEVEL", v["compression"],
            "zlib-Level fuer Netzwerkpakete (1-9). Niedriger = weniger CPU, mehr Bandbreite.",
            "required|integer|between:1,9"),
        var("Asynchrone Kompression", "ASYNC_COMPRESSION", v["async_compression"],
            "Grosse Pakete in Hintergrund-Threads komprimieren, entlastet den Hauptthread (true/false).", BOOL),
        var("Async-Worker", "ASYNC_WORKERS", v["workers"],
            "Anzahl Hintergrund-Threads ('auto' oder Zahl). Etwa so viele wie CPU-Kerne.",
            "required|string|max:4"),
        var("Speicherlimit (MB)", "MEMORY_LIMIT", "auto",
            "Hartes Speicherlimit des Hauptthreads in MB. 'auto' = 85 % des Panel-RAM-Limits, 0 = kein Limit.",
            "required|string|max:6"),
        var("Debug-Ausgaben", "DEBUG", "false", "Zusaetzliche Debug-Meldungen in der Konsole (true/false).", BOOL),
    ]


for v in VARIANTS.values():
    egg = {
        "_comment": "PocketMine-MP Egg fuer Pterodactyl",
        "meta": {"version": "PTDL_v2", "update_url": None},
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "name": v["name"],
        "author": "contact@pixelcst.tech",
        "description": v["description"],
        "features": None,
        "docker_images": {"Debian": "ghcr.io/parkervcp/yolks:debian"},
        "file_denylist": [],
        "startup": startup(v),
        "config": {
            "files": json.dumps(config_files(), indent=4),
            "startup": json.dumps({"done": "\"help\""}, indent=4),
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
