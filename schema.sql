CREATE TABLE users (
	id SERIAL PRIMARY KEY,
	username TEXT,
	password TEXT
);

CREATE TABLE compositions (
	id SERIAL PRIMARY KEY,
	title TEXT,
	filename TEXT,
	composer TEXT,
	instrumentcount INTEGER,
	views INTEGER,
	notation TEXT,
	genre TEXT,
	user_id INTEGER REFERENCES users
);

CREATE TABLE tags (
	song_id INTEGER REFERENCES compositions,
	tag TEXT,
	user_id INTEGER REFERENCES users
);

CREATE TABLE ratings (
	song_id INTEGER REFERENCES compositions,
	rating INTEGER,
	user_id INTEGER REFERENCES users
);

CREATE TABLE notes (
	song_id INTEGER REFERENCES compositions,
	note TEXT,
	user_id INTEGER REFERENCES users
);

CREATE TABLE difficultyratings (
	song_id INTEGER REFERENCES compositions,
	difficulty INTEGER,
	user_id INTEGER REFERENCES users
);