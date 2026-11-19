#!/bin/ash
# Paper - Installations-/Update-Skript fuer Pterodactyl (Performance)
# Laeuft im Installer-Container (ghcr.io/pterodactyl/installers:alpine) unter /mnt/server

PROJECT=paper
API="https://fill.papermc.io/v3/projects/${PROJECT}"
USER_AGENT="craftinghosting-egg/1.0"
SERVER_DIR="${SERVER_DIR:-/mnt/server}"
SERVER_JARFILE="${SERVER_JARFILE:-server.jar}"

if ! command -v jq >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
    apk add --no-cache curl jq >/dev/null 2>&1 || true
fi

mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}" || exit 1

if [ -n "${DL_PATH}" ]; then
    echo ">> Nutze eigene Download-URL: ${DL_PATH}"
    DOWNLOAD_URL=$(eval echo "$(echo "${DL_PATH}" | sed -e 's/{{/${/g' -e 's/}}/}/g')")
    DOWNLOAD_SHA=""
else
    PROJECT_JSON=$(curl -fsSL -m 30 -A "${USER_AGENT}" "${API}")
    if [ -z "${PROJECT_JSON}" ]; then
        echo "!! PaperMC-API nicht erreichbar."
        exit 1
    fi
    # Neueste stabile Version (ohne -rc / -pre / Snapshots)
    LATEST_VERSION=$(printf "%s\n" "${PROJECT_JSON}" | jq -r '[.versions[][]] | map(select(test("(?i)(rc|pre|snapshot|beta|alpha)") | not)) | first')

    if [ -z "${MINECRAFT_VERSION}" ] || [ "${MINECRAFT_VERSION}" = "latest" ]; then
        MINECRAFT_VERSION="${LATEST_VERSION}"
    elif [ "$(printf "%s\n" "${PROJECT_JSON}" | jq -r --arg V "${MINECRAFT_VERSION}" '[.versions[][]] | index($V) != null')" != "true" ]; then
        echo ">> Version ${MINECRAFT_VERSION} nicht gefunden - nutze neueste Version ${LATEST_VERSION}"
        MINECRAFT_VERSION="${LATEST_VERSION}"
    fi

    if [ -z "${BUILD_NUMBER}" ] || [ "${BUILD_NUMBER}" = "latest" ]; then
        BUILD_JSON=$(curl -fsSL -m 30 -A "${USER_AGENT}" "${API}/versions/${MINECRAFT_VERSION}/builds/latest")
    else
        BUILD_JSON=$(curl -fsSL -m 30 -A "${USER_AGENT}" "${API}/versions/${MINECRAFT_VERSION}/builds/${BUILD_NUMBER}" || true)
        if [ -z "${BUILD_JSON}" ] || [ "$(printf "%s\n" "${BUILD_JSON}" | jq -r '.id // empty')" = "" ]; then
            echo ">> Build ${BUILD_NUMBER} nicht gefunden - nutze neuesten Build"
            BUILD_JSON=$(curl -fsSL -m 30 -A "${USER_AGENT}" "${API}/versions/${MINECRAFT_VERSION}/builds/latest")
        fi
    fi
    BUILD_NUMBER=$(printf "%s\n" "${BUILD_JSON}" | jq -r '.id')
    DOWNLOAD_URL=$(printf "%s\n" "${BUILD_JSON}" | jq -r '.downloads."server:default".url')
    DOWNLOAD_SHA=$(printf "%s\n" "${BUILD_JSON}" | jq -r '.downloads."server:default".checksums.sha256 // empty')

    echo ">> Projekt:    ${PROJECT}"
    echo ">> MC-Version: ${MINECRAFT_VERSION}"
    echo ">> Build:      ${BUILD_NUMBER} ($(printf "%s\n" "${BUILD_JSON}" | jq -r '.channel'))"
fi

if [ -z "${DOWNLOAD_URL}" ] || [ "${DOWNLOAD_URL}" = "null" ]; then
    echo "!! Keine Download-URL gefunden."
    exit 1
fi

echo ">> Lade ${DOWNLOAD_URL}"
if ! curl -fsSL --retry 3 -m 600 -A "${USER_AGENT}" -o "${SERVER_JARFILE}.new" "${DOWNLOAD_URL}"; then
    rm -f "${SERVER_JARFILE}.new"
    echo "!! Download fehlgeschlagen."
    exit 1
fi
if [ -n "${DOWNLOAD_SHA}" ] && [ "$(sha256sum "${SERVER_JARFILE}.new" | cut -d' ' -f1)" != "${DOWNLOAD_SHA}" ]; then
    rm -f "${SERVER_JARFILE}.new"
    echo "!! Pruefsumme stimmt nicht - Download beschaedigt."
    exit 1
fi
if [ -f "${SERVER_JARFILE}" ]; then
    mv -f "${SERVER_JARFILE}" "${SERVER_JARFILE}.old"
fi
mv -f "${SERVER_JARFILE}.new" "${SERVER_JARFILE}"

if [ ! -f server.properties ]; then
    echo ">> Lade Standard-server.properties"
    curl -fsSL -m 30 -A "${USER_AGENT}" -o server.properties https://raw.githubusercontent.com/pterodactyl/game-eggs/main/minecraft/java/server.properties || touch server.properties
fi

# Performance-Konfiguration nur bei Neuinstallation (bestehende Dateien bleiben unangetastet)
if [ "${OPTIMIZE_CONFIGS:-true}" = "true" ]; then
    mkdir -p config
    if [ ! -f config/paper-world-defaults.yml ]; then
        echo ">> Lege optimierte config/paper-world-defaults.yml an"
        cat > config/paper-world-defaults.yml <<'YML'
__PAPER_WORLD_DEFAULTS__
YML
    fi
    if [ ! -f spigot.yml ]; then
        echo ">> Lege optimierte spigot.yml an"
        cat > spigot.yml <<'YML'
__SPIGOT__
YML
    fi
    if [ ! -f bukkit.yml ]; then
        echo ">> Lege optimierte bukkit.yml an"
        cat > bukkit.yml <<'YML'
__BUKKIT__
YML
    fi
fi

# Velocity-Block vorbereiten, damit er beim Start gesetzt werden kann
mkdir -p config
if [ ! -f config/paper-global.yml ]; then
    cat > config/paper-global.yml <<'YML'
# Paper ergaenzt fehlende Werte selbst. Velocity wird ueber das Panel gesteuert.
proxies:
  velocity:
    enabled: false
    online-mode: true
    secret: ''
YML
fi

echo ">> Installation abgeschlossen."
