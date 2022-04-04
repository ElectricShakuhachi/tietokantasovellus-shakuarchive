CREATE TABLE users (id SERIAL PRIMARY KEY, username TEXT, password TEXT);
CREATE TABLE compositions (id SERIAL PRIMARY KEY, title TEXT, filename TEXT, difficulty INTEGER, composer TEXT, genre TEXT, instrumentcount INTEGER, views INTEGER, uploader TEXT, notation TEXT);
CREATE TABLE genres (id SERIAL PRIMARY KEY, title TEXT);