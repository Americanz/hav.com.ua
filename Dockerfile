FROM nginx:1.27-alpine

# Конфіг рідше за статику, тому він у попередньому шарі.
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --chown=nginx:nginx \
    index.html erp.html bas.html odoo.html content.json favicon.ico \
    /usr/share/nginx/html/
COPY --chown=nginx:nginx css /usr/share/nginx/html/css
COPY --chown=nginx:nginx js /usr/share/nginx/html/js
COPY --chown=nginx:nginx img /usr/share/nginx/html/img

# Образ не працює від root: порт 80 йому недоступний, тому сайт слухає 8080,
# а pid Nginx пише в /tmp, куди може писати користувач nginx.
RUN sed -i \
        -e 's|^user |#user |' \
        -e 's|/var/run/nginx.pid|/tmp/nginx.pid|' \
        -e 's|/run/nginx.pid|/tmp/nginx.pid|' \
        /etc/nginx/nginx.conf \
    && nginx -t

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["wget", "-q", "--spider", "http://127.0.0.1:8080/"]

CMD ["nginx", "-g", "daemon off;"]
