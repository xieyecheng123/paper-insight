FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --production=false

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"] 