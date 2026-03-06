FROM node:22-alpine

WORKDIR /app

COPY package.json yarn.lock* ./


RUN yarn install --frozen-lockfile || yarn install

# Copy the rest of the app
COPY . .

EXPOSE 3000

# Use shell form to ensure it runs correctly
CMD ["sh", "-c", "yarn install && yarn start"]
