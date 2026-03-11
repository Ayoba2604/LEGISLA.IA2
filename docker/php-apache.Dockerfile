FROM php:8.2-apache

RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*
RUN docker-php-ext-install pdo pdo_pgsql pdo_mysql
RUN a2enmod rewrite
WORKDIR /var/www/html

