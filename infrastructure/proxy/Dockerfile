FROM caddy:2-alpine

# Copy Caddyfile configuration
COPY infrastructure/proxy/Caddyfile /etc/caddy/Caddyfile

# Expose HTTP and HTTPS ports
EXPOSE 80 443

# Caddy uses /data for certificates and /config for configuration
VOLUME /data
VOLUME /config
