# ==========================================
# HAV — Cloud Architecture Technologies
# Static site served by Nginx
# ==========================================

FROM nginx:1.27-alpine

# Видаляємо дефолтну конфігурацію Nginx
RUN rm -f /etc/nginx/conf.d/default.conf

# Копіюємо власну конфігурацію
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копіюємо статичні файли сайту
COPY index.html erp.html bas.html odoo.html /usr/share/nginx/html/
COPY content.json /usr/share/nginx/html/content.json
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

# Відкриваємо порт 80
EXPOSE 80

# Healthcheck (Coolify використовує його для перевірки)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

# Запуск Nginx у foreground
CMD ["nginx", "-g", "daemon off;"]
