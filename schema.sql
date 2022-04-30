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
	user_id INTEGER REFERENCES users
);

CREATE TABLE genres (
	song_id INTEGER REFERENCES compositions,
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

CREATE TABLE links (
	song_id INTEGER REFERENCES compositions,
	link TEXT,
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