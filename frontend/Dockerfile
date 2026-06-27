# Geliştirme amaçlı imaj (Vite dev server). Prod için ileride nginx'li çok
# aşamalı build eklenecek (bkz. PLAN §2 Altyapı).
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
