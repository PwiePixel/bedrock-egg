#!/bin/bash
# Minecraft Bedrock Dedicated Server - Installations-/Update-Skript fuer Pterodactyl
# Laeuft im Installer-Container (ghcr.io/parkervcp/installers:debian) unter /mnt/server

set -e

SERVER_DIR="${SERVER_DIR:-/mnt/server}"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
API_URL="https://net-secondary.web.minecraft-services.net/api/v1.0/download/links"

if ! command -v jq >/dev/null 2>&1 || ! command -v unzip >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
    apt-get update -y && apt-get install -y curl jq unzip ca-certificates
fi

mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

VERSION="${BEDROCK_VERSION:-latest}"
VERSION="$(echo "${VERSION}" | tr '[:upper:]' '[:lower:]' | xargs)"
[ -z "${VERSION}" ] && VERSION="latest"

get_api_link() {
    curl -fsSL -m 30 -H "User-Agent: ${UA}" -H "Accept: application/json" "${API_URL}" \
        | jq -r --arg t "$1" '.result.links[] | select(.downloadType==$t) | .downloadUrl' 2>/dev/null | head -n1
}

get_page_link() {
    curl -fsSL -m 30 -H "User-Agent: ${UA}" -H "Accept-Language: en-US,en;q=0.9" \
        "https://www.minecraft.net/en-us/download/server/bedrock" \
        | grep -oE "https://[^\"']*/$1/bedrock-server-[0-9.]+\.zip" | head -n1
}

DOWNLOAD_URL=""
case "${VERSION}" in
    latest)
        echo ">> Suche aktuelle Bedrock-Version ..."
        DOWNLOAD_URL="$(get_api_link serverBedrockLinux || true)"
        [ -z "${DOWNLOAD_URL}" ] && DOWNLOAD_URL="$(get_page_link bin-linux || true)"
        ;;
    preview)
        echo ">> Suche aktuelle Bedrock-Preview-Version ..."
        DOWNLOAD_URL="$(get_api_link serverBedrockPreviewLinux || true)"
        [ -z "${DOWNLOAD_URL}" ] && DOWNLOAD_URL="$(get_page_link bin-linux-preview || true)"
        ;;
    *)
        if ! echo "${VERSION}" | grep -qE '^[0-9]+(\.[0-9]+){2,3}$'; then
            echo "!! Ungueltige Version '${VERSION}'. Erlaubt: latest, preview oder z.B. 1.21.50.10"
            exit 1
        fi
        DOWNLOAD_URL="https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-${VERSION}.zip"
        ;;
esac

if [ -z "${DOWNLOAD_URL}" ] || [ "${DOWNLOAD_URL}" = "null" ]; then
    echo "!! Konnte keinen Download-Link ermitteln. Bitte spaeter erneut versuchen oder eine feste Version angeben."
    exit 1
fi

echo ">> Download: ${DOWNLOAD_URL}"
rm -f bedrock-server.zip
if ! curl -fsSL --retry 3 -m 600 -H "User-Agent: ${UA}" -o bedrock-server.zip "${DOWNLOAD_URL}"; then
    echo "!! Download fehlgeschlagen (Version vorhanden?)."
    exit 1
fi
unzip -tq bedrock-server.zip >/dev/null || { echo "!! Heruntergeladene Datei ist kein gueltiges ZIP."; exit 1; }

# Bei Updates eigene Konfiguration behalten
BACKUP_DIR="$(mktemp -d)"
for f in server.properties permissions.json allowlist.json whitelist.json; do
    if [ -f "$f" ]; then cp -a "$f" "${BACKUP_DIR}/"; fi
done

echo ">> Entpacke Server ..."
unzip -oq bedrock-server.zip
rm -f bedrock-server.zip

# Neue Standard-server.properties merken, um fehlende Eintraege zu ergaenzen
cp -a server.properties "${BACKUP_DIR}/server.properties.new"

for f in server.properties permissions.json allowlist.json whitelist.json; do
    if [ -f "${BACKUP_DIR}/$f" ]; then cp -af "${BACKUP_DIR}/$f" "./$f"; fi
done

# Alle Eintraege, die in der behaltenen server.properties fehlen, aus der neuen Version uebernehmen
ADDED=0
while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|'#'*) continue ;; esac
    key="${line%%=*}"
    if ! grep -q "^${key}=" server.properties; then
        echo "$line" >> server.properties
        ADDED=$((ADDED+1))
    fi
done < "${BACKUP_DIR}/server.properties.new"
[ "${ADDED}" -gt 0 ] && echo ">> ${ADDED} fehlende Eintraege in server.properties ergaenzt"
rm -rf "${BACKUP_DIR}"

# Server-Telemetrie standardmaessig aktivieren
TELEMETRY="${TELEMETRY:-true}"
if grep -q "^emit-server-telemetry=" server.properties; then
    sed -i "s/^emit-server-telemetry=.*/emit-server-telemetry=${TELEMETRY}/" server.properties
else
    echo "emit-server-telemetry=${TELEMETRY}" >> server.properties
fi

chmod +x bedrock_server

# ---------------------------------------------------------------------------
# Grundeinstellungen fuer neue Welten (werden beim Start zusaetzlich vom Panel gesetzt)
# ---------------------------------------------------------------------------
set_prop() {
    grep -v "^$1=" server.properties > server.properties.tmp || true
    echo "$1=$2" >> server.properties.tmp
    mv server.properties.tmp server.properties
}
[ -n "${LEVEL_NAME}" ] && set_prop level-name "${LEVEL_NAME}"
[ -n "${LEVEL_SEED}" ] && set_prop level-seed "${LEVEL_SEED}"
[ -n "${GAMEMODE}" ] && set_prop gamemode "${GAMEMODE}"
[ -n "${DIFFICULTY}" ] && set_prop difficulty "${DIFFICULTY}"

# ---------------------------------------------------------------------------
# Chat-Log: Behavior-Pack, das Chatnachrichten und Tode in die Konsole schreibt
# ---------------------------------------------------------------------------
PACK_UUID="5d1e7c3a-8b2f-4c6d-9e0a-1b2c3d4e5f60"
PACK_DIR="behavior_packs/konsolen_chatlog"
LEVEL="$(grep '^level-name=' server.properties | cut -d= -f2-)"
[ -z "${LEVEL}" ] && LEVEL="Bedrock level"
WORLD_DIR="worlds/${LEVEL}"

run_probe() {
    rm -f "$1"
    (
        for _ in $(seq 1 150); do
            sleep 1
            if grep -qE "Server started|Exiting program" "$1" 2>/dev/null; then break; fi
        done
        sleep 2
        if [ -n "$2" ]; then echo "$2"; sleep 3; fi
        echo stop
    ) | LD_LIBRARY_PATH=. timeout 200 ./bedrock_server > "$1" 2>&1 || true
}

update_world_packs() {
    # $1 = add | remove
    python3 - "$WORLD_DIR/world_behavior_packs.json" "$PACK_UUID" "$1" <<'PY'
import json, os, sys
path, uuid, mode = sys.argv[1], sys.argv[2], sys.argv[3]
packs = []
if os.path.exists(path):
    try:
        packs = json.load(open(path))
    except Exception:
        packs = []
packs = [p for p in packs if p.get("pack_id") != uuid]
if mode == "add":
    packs.append({"pack_id": uuid, "version": [1, 0, 0]})
if packs or os.path.exists(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(packs, open(path, "w"), indent=2)
PY
}

write_pack() {
    # $1 = @minecraft/server Version
    mkdir -p "${PACK_DIR}/scripts"
    cat > "${PACK_DIR}/manifest.json" <<JSON
{
  "format_version": 2,
  "header": {
    "name": "Konsolen-Chatlog",
    "description": "Schreibt Chatnachrichten und Tode in die Server-Konsole",
    "uuid": "${PACK_UUID}",
    "version": [1, 0, 0],
    "min_engine_version": [1, 21, 0]
  },
  "modules": [
    {
      "type": "script",
      "language": "javascript",
      "uuid": "9c4b2a1d-6e5f-4a3b-8c7d-0e1f2a3b4c5d",
      "version": [1, 0, 0],
      "entry": "scripts/main.js"
    }
  ],
  "dependencies": [
    { "module_name": "@minecraft/server", "version": "$1" }
  ]
}
JSON
    cat > "${PACK_DIR}/scripts/main.js" <<'JS'
import { world } from "@minecraft/server";

world.afterEvents.chatSend.subscribe((ev) => {
    console.log(`[Chat] <${ev.sender.name}> ${ev.message}`);
});

world.afterEvents.entityDie.subscribe((ev) => {
    const dead = ev.deadEntity;
    if (dead.typeId !== "minecraft:player") return;
    const src = ev.damageSource;
    let by = src.cause;
    if (src.damagingEntity) {
        by = src.damagingEntity.typeId === "minecraft:player"
            ? src.damagingEntity.name
            : src.damagingEntity.typeId.replace("minecraft:", "");
    }
    console.log(`[Tod] ${dead.name} ist gestorben (${by})`);
});
JS
}

CHAT_LOG="${CHAT_LOG:-true}"
if [ "${CHAT_LOG}" = "true" ]; then
    echo ">> Richte Chat-Log ein ..."
    if ! command -v python3 >/dev/null 2>&1; then
        apt-get update -y >/dev/null 2>&1 && apt-get install -y python3 >/dev/null 2>&1 || true
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        echo "!! python3 nicht verfuegbar - Chat-Log wird uebersprungen."
    else
        cat > /tmp/enable_beta_api.py <<'PY'
__ENABLE_BETA_PY__
PY
        set_prop content-log-console-output-enabled true
        if [ ! -f "${WORLD_DIR}/level.dat" ]; then
            echo ">> Erzeuge Welt '${LEVEL}' ..."
            run_probe /tmp/bds_probe1.log
        fi
        if [ -f "${WORLD_DIR}/level.dat" ] && python3 /tmp/enable_beta_api.py "${WORLD_DIR}/level.dat"; then
            write_pack "99.0.0-beta"
            update_world_packs add
            echo ">> Ermittle Script-API-Version ..."
            run_probe /tmp/bds_probe2.log
            API_VERSION="$(grep -oE 'Current \[beta\] version is \[[^]]+\]' /tmp/bds_probe2.log | head -n1 | sed -E 's/.*\[([^]]+)\]$/\1/')"
            if [ -n "${API_VERSION}" ]; then
                write_pack "${API_VERSION}"
                echo ">> Chat-Log aktiv (Script-API ${API_VERSION})"
            else
                echo "!! Script-API-Version nicht ermittelbar - Chat-Log deaktiviert."
                update_world_packs remove
                rm -rf "${PACK_DIR}"
            fi
        else
            echo "!! Welt konnte nicht vorbereitet werden - Chat-Log wird uebersprungen."
        fi
        rm -f /tmp/bds_probe1.log /tmp/bds_probe2.log /tmp/enable_beta_api.py
    fi
else
    update_world_packs remove 2>/dev/null || true
    rm -rf "${PACK_DIR}"
fi

# ---------------------------------------------------------------------------
# Server-Identitaet dauerhaft speichern, damit Spieler nicht bei jedem Neustart
# erneut gefragt werden, ob sie dem Server vertrauen
# ---------------------------------------------------------------------------
if [ -f keys/server_identity_key.pem ]; then
    echo ">> Gespeicherte Server-Identitaet vorhanden (keys/server_identity_key.pem)"
else
    echo ">> Speichere Server-Identitaet ..."
    run_probe /tmp/bds_probe3.log "serveridentity save"
    if [ -f keys/server_identity_key.pem ]; then
        echo ">> Server-Identitaet gespeichert (keys/server_identity_key.pem)"
    else
        echo "!! Server-Identitaet konnte nicht gespeichert werden. Bitte einmal in der Konsole: serveridentity save"
    fi
    rm -f /tmp/bds_probe3.log
fi

echo "${DOWNLOAD_URL##*/}" | sed -e 's/^bedrock-server-//' -e 's/\.zip$//' > .bedrock_version

echo ">> Installation abgeschlossen: Version $(cat .bedrock_version)"
