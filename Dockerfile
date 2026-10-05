FROM nginx:1.27-alpine

# Свій головний конфіг: pid і тимчасові файли в /tmp, бо процес не root.
COPY nginx.main.conf /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --chown=nginx:nginx \
    index.html erp.html bas.html odoo.html content.json favicon.ico \
    /usr/share/nginx/html/
COPY --chown=nginx:nginx css /usr/share/nginx/html/css
COPY --chown=nginx:nginx js /usr/share/nginx/html/js
COPY --chown=nginx:nginx img /usr/share/nginx/html/img

RUN mkdir -p \
        /tmp/nginx/client_temp \
        /tmp/nginx/proxy_temp \
        /tmp/nginx/fastcgi_temp \
        /tmp/nginx/uwsgi_temp \
        /tmp/nginx/scgi_temp \
    && chown -R nginx:nginx /tmp/nginx \
    && nginx -t

USER nginx
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["wget", "-q", "--spider", "http://127.0.0.1:8080/"]

ENTRYPOINT ["nginx", "-g", "daemon off;"]
