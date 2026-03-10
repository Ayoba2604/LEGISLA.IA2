FROM php:8.2-apache

RUN docker-php-ext-install pdo pdo_pgsql pdo_mysql
RUN a2enmod rewrite
RUN sed -ri -e 's!/var/www/html!/var/www/html/public!g' /etc/apache2/sites-available/*.conf /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

WORKDIR /var/www/html

