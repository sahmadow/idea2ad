#!/bin/bash
# Generate self-signed SSL certificates for local development
# Required for Facebook OAuth (HTTPS only)

CERT_DIR="certs"
mkdir -p "$CERT_DIR"

if [ -f "$CERT_DIR/cert.pem" ] && [ -f "$CERT_DIR/key.pem" ]; then
    echo "Certificates already exist in $CERT_DIR/"
    echo "Delete them first if you want to regenerate."
    exit 0
fi

echo "Generating self-signed SSL certificates..."
openssl req -x509 -newkey rsa:4096 -nodes \
    -out "$CERT_DIR/cert.pem" \
    -keyout "$CERT_DIR/key.pem" \
    -days 365 \
    -subj '/CN=localhost'

echo "Done! Certificates created in $CERT_DIR/"
echo "Note: You'll need to accept the browser warning when accessing https://localhost"
