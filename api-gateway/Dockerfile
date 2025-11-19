# AI Platform API Gateway - NGINX Docker Image
FROM nginx:1.25-alpine

# Install additional tools for debugging and health checks
RUN apk add --no-cache \
    curl \
    jq \
    openssl

# Create directories
RUN mkdir -p /var/cache/nginx \
    /var/log/nginx \
    /etc/nginx/ssl \
    /usr/share/nginx/html/docs

# Copy NGINX configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create common.conf for shared configuration
# Note: In production, you would split this from nginx.conf
RUN echo "" > /etc/nginx/conf.d/common.conf

# Create a simple health check script
RUN echo '#!/bin/sh' > /usr/local/bin/healthcheck.sh && \
    echo 'curl -sf http://localhost/health || exit 1' >> /usr/local/bin/healthcheck.sh && \
    chmod +x /usr/local/bin/healthcheck.sh

# Generate self-signed SSL certificate for development
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=AI Platform/CN=localhost"

# Create default documentation page
RUN echo '<!DOCTYPE html><html><head><title>AI Platform API</title></head><body><h1>AI Platform API Documentation</h1><p>Welcome to the AI Platform API Gateway.</p></body></html>' > /usr/share/nginx/html/docs/index.html

# Set proper permissions
RUN chown -R nginx:nginx /var/cache/nginx \
    /var/log/nginx \
    /usr/share/nginx/html

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Run NGINX
CMD ["nginx", "-g", "daemon off;"]
