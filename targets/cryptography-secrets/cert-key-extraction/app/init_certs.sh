#!/bin/bash
# Generate self-signed TLS certificate and private key
set -e

CERT_DIR="/app/certs"
mkdir -p "$CERT_DIR"

# Generate RSA private key (2048-bit for the lab)
openssl genrsa -out "$CERT_DIR/server.key" 2048

# Generate self-signed certificate with informative subject
openssl req -new -x509 \
    -key "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.crt" \
    -days 365 \
    -subj "/C=US/ST=California/L=San Jose/O=IronGate Security/OU=Internal Systems/CN=irongate.local/emailAddress=admin@irongate.local"

# Set permissions (intentionally readable for the vulnerability)
chmod 644 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"

echo "TLS certificates generated successfully."
echo "Key: $CERT_DIR/server.key"
echo "Cert: $CERT_DIR/server.crt"
