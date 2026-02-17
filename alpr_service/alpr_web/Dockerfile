FROM node:20-alpine AS builder

WORKDIR /app

# Build arguments for NEXT_PUBLIC_ variables
ARG NEXT_PUBLIC_BASE_API_GATE_WAY_URL=http://35.187.233.205/api/general
ARG NEXT_PUBLIC_API_UPLOAD_IMAGE=http://35.187.233.205/api/image
ARG NEXT_PUBLIC_WEBSOCKET_VIDEO_HANLER=ws://35.187.233.205/ws/video

# Set as environment variables for Next.js build
ENV NEXT_PUBLIC_BASE_API_GATE_WAY_URL=$NEXT_PUBLIC_BASE_API_GATE_WAY_URL
ENV NEXT_PUBLIC_API_UPLOAD_IMAGE=$NEXT_PUBLIC_API_UPLOAD_IMAGE
ENV NEXT_PUBLIC_WEBSOCKET_VIDEO_HANLER=$NEXT_PUBLIC_WEBSOCKET_VIDEO_HANLER

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
