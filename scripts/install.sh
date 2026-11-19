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

for f in server.properties permissions.json allowlist.json whitelist.json; do
    if [ -f "${BACKUP_DIR}/$f" ]; then cp -af "${BACKUP_DIR}/$f" "./$f"; fi
done
rm -rf "${BACKUP_DIR}"

# Server-Telemetrie standardmaessig aktivieren
TELEMETRY="${TELEMETRY:-true}"
if grep -q "^emit-server-telemetry=" server.properties; then
    sed -i "s/^emit-server-telemetry=.*/emit-server-telemetry=${TELEMETRY}/" server.properties
else
    echo "emit-server-telemetry=${TELEMETRY}" >> server.properties
fi

chmod +x bedrock_server
echo "${DOWNLOAD_URL##*/}" | sed -e 's/^bedrock-server-//' -e 's/\.zip$//' > .bedrock_version

echo ">> Installation abgeschlossen: Version $(cat .bedrock_version)"
