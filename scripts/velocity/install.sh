#!/bin/bash
# Velocity (Minecraft Java Proxy) - Installations-/Update-Skript fuer Pterodactyl
# Laeuft im Installer-Container (ghcr.io/parkervcp/installers:debian) unter /mnt/server

set -e

SERVER_DIR="${SERVER_DIR:-/mnt/server}"
API="https://fill.papermc.io/v3/projects/velocity"
UA="craftinghosting-egg/1.0"

if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1 || ! command -v unzip >/dev/null 2>&1; then
    apt-get update -y && apt-get install -y curl jq unzip ca-certificates
fi

mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

VERSION="$(echo "${VELOCITY_VERSION:-latest}" | tr -d '[:space:]')"
[ -z "${VERSION}" ] && VERSION="latest"

if [ "${VERSION}" = "latest" ]; then
    VERSION="$(curl -fsSL -m 30 -A "${UA}" "${API}" | jq -r '[.versions[][]] | map(select(test("SNAPSHOT") | not)) | first')"
    if [ -z "${VERSION}" ] || [ "${VERSION}" = "null" ]; then
        echo "!! Konnte die neueste Velocity-Version nicht ermitteln."
        exit 1
    fi
fi

echo ">> Velocity-Version: ${VERSION}"
BUILD_JSON="$(curl -fsSL -m 30 -A "${UA}" "${API}/versions/${VERSION}/builds/latest" || true)"
JAR_URL="$(echo "${BUILD_JSON}" | jq -r '.downloads["server:default"].url // empty' 2>/dev/null || true)"
JAR_SHA="$(echo "${BUILD_JSON}" | jq -r '.downloads["server:default"].checksums.sha256 // empty' 2>/dev/null || true)"
BUILD_ID="$(echo "${BUILD_JSON}" | jq -r '.id // empty' 2>/dev/null || true)"
if [ -z "${JAR_URL}" ]; then
    echo "!! Version ${VERSION} wurde nicht gefunden (Beispiele: latest, 4.3.1, 3.5.1)."
    exit 1
fi

echo ">> Lade Velocity ${VERSION} Build ${BUILD_ID} ..."
curl -fsSL --retry 3 -m 300 -A "${UA}" -o velocity.jar.new "${JAR_URL}"
if [ -n "${JAR_SHA}" ] && [ "$(sha256sum velocity.jar.new | cut -d' ' -f1)" != "${JAR_SHA}" ]; then
    rm -f velocity.jar.new
    echo "!! Pruefsumme stimmt nicht - Download beschaedigt."
    exit 1
fi
mv -f velocity.jar.new velocity.jar

# Standard-Konfiguration aus der JAR anlegen, damit das Panel sie schon beim ersten Start setzen kann
if [ ! -f velocity.toml ]; then
    echo ">> Erstelle velocity.toml ..."
    unzip -p velocity.jar default-velocity.toml > velocity.toml
    # Beispiel-Server entfernen, nur 'lobby' bleibt
    sed -i -e '/^factions = /d' -e '/^minigames = /d' velocity.toml
    awk '
        /^\[forced-hosts\]/ { print; infh = 1; next }
        /^\[/ { infh = 0 }
        infh && !/^[[:space:]]*#/ && NF { next }
        { print }
    ' velocity.toml > velocity.toml.tmp && mv velocity.toml.tmp velocity.toml
fi

mkdir -p plugins
echo "${VERSION}-${BUILD_ID}" > .velocity_version
echo ">> Installation abgeschlossen: Velocity ${VERSION} (Build ${BUILD_ID})"
