#!/bin/bash
# PocketMine-MP - Installations-/Update-Skript fuer Pterodactyl
# Laeuft im Installer-Container (ghcr.io/parkervcp/installers:debian) unter /mnt/server

set -e

SERVER_DIR="${SERVER_DIR:-/mnt/server}"

if ! command -v curl >/dev/null 2>&1 || ! command -v tar >/dev/null 2>&1; then
    apt-get update -y && apt-get install -y curl tar ca-certificates
fi

mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

PM_VERSION="$(echo "${PM_VERSION:-latest}" | tr -d '[:space:]')"
[ -z "${PM_VERSION}" ] && PM_VERSION="latest"
PHP_VERSION="$(echo "${PHP_VERSION:-8.2}" | tr -d '[:space:]')"

if [ "${PM_VERSION}" = "latest" ]; then
    PHAR_URL="https://github.com/pmmp/PocketMine-MP/releases/latest/download/PocketMine-MP.phar"
else
    if ! echo "${PM_VERSION}" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+([-.][A-Za-z0-9.]+)?$'; then
        echo "!! Ungueltige PocketMine-Version '${PM_VERSION}'. Erlaubt: latest oder z.B. 5.44.3"
        exit 1
    fi
    PHAR_URL="https://github.com/pmmp/PocketMine-MP/releases/download/${PM_VERSION}/PocketMine-MP.phar"
fi

PM_MAJOR="5"
if [ "${PM_VERSION}" != "latest" ]; then PM_MAJOR="${PM_VERSION%%.*}"; fi
PHP_URL="https://github.com/pmmp/PHP-Binaries/releases/download/pm${PM_MAJOR}-php-${PHP_VERSION}-latest/PHP-${PHP_VERSION}-Linux-x86_64-PM${PM_MAJOR}.tar.gz"

echo ">> Lade PocketMine-MP (${PM_VERSION}) ..."
if ! curl -fsSL --retry 3 -m 300 -o PocketMine-MP.phar.new "${PHAR_URL}"; then
    rm -f PocketMine-MP.phar.new
    echo "!! Download fehlgeschlagen: ${PHAR_URL}"
    exit 1
fi
if [ "$(stat -c %s PocketMine-MP.phar.new)" -lt 500000 ]; then
    rm -f PocketMine-MP.phar.new
    echo "!! Heruntergeladene PocketMine-MP.phar ist unvollstaendig."
    exit 1
fi
mv -f PocketMine-MP.phar.new PocketMine-MP.phar

echo ">> Lade PHP ${PHP_VERSION} fuer PocketMine-MP ${PM_MAJOR} ..."
if ! curl -fsSL --retry 3 -m 600 -o php.tar.gz "${PHP_URL}"; then
    rm -f php.tar.gz
    echo "!! PHP-Download fehlgeschlagen: ${PHP_URL}"
    exit 1
fi
rm -rf bin
tar -xzf php.tar.gz
rm -f php.tar.gz

# opcache mit absolutem Pfad laden (wird beim Start zusaetzlich korrigiert)
EXT_DIR="$(ls -d "${SERVER_DIR}"/bin/php7/lib/php/extensions/no-debug-zts-* 2>/dev/null | head -n1)"
if [ -n "${EXT_DIR}" ]; then
    EXT_DIR="/home/container${EXT_DIR#"${SERVER_DIR}"}"
    sed -i "s#^zend_extension=.*opcache.so#zend_extension=${EXT_DIR}/opcache.so#" bin/php7/bin/php.ini
fi
chmod +x bin/php7/bin/php

# server.properties anlegen, damit das Panel die Werte setzen kann
if [ ! -f server.properties ]; then
    cat > server.properties <<PROPS
#Properties Config file
motd=${SERVERNAME:-craftinghosting.free}
server-port=19132
server-portv6=19133
enable-ipv6=false
PROPS
fi

mkdir -p plugins worlds resource_packs

VERSION_LINE="$(./bin/php7/bin/php -d zend_extension= PocketMine-MP.phar --version 2>/dev/null | grep -m1 'for Minecraft' || true)"
echo ">> Installation abgeschlossen: ${VERSION_LINE:-PocketMine-MP} (PHP ${PHP_VERSION})"
