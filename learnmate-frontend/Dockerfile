# frontend/Dockerfile

FROM node:16

WORKDIR /app

COPY package.json package-lock.json /app/

RUN npm install

COPY . /app

EXPOSE 4200

CMD ["ng", "serve", "--host", "0.0.0.0"]
