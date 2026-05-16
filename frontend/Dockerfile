FROM node:20-alpine AS build

WORKDIR /app

# Install corporate CA certificate - Alpine already has ca-certificates installed in node image
# Copy cert and append it to the system CA bundle so both apk and npm trust it
COPY corporate-ca.pem /usr/local/share/ca-certificates/corporate-ca.crt
RUN cat /usr/local/share/ca-certificates/corporate-ca.crt >> /etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

COPY package.json .
RUN npm install

COPY public/ public/
COPY src/ src/

RUN npm run build

# Serve with nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
