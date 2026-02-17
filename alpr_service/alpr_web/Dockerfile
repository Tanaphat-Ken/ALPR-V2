FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install --legacy-peer-deps

COPY . .

RUN npm run build

FROM node:20-alpine as deploy

WORKDIR /app

COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/package-lock.json /app/package-lock.json
COPY --from=builder /app/.next /app/.next

RUN npm install --production --legacy-peer-deps

EXPOSE 3000

CMD ["npm", "start"]
