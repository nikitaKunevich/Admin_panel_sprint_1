-- Создаем отдельную от внутренних таблиц джанго схему.
CREATE SCHEMA IF NOT EXISTS content;

-- Категории для основных сущностей
CREATE TYPE movie_type AS ENUM ('film', 'tv_show', 'series');
CREATE TYPE movie_team_role AS ENUM ('director', 'actor', 'writer', 'producer', 'editor');

-- Основные сущности
CREATE TABLE content.movie
(
    id            UUID PRIMARY KEY,
    title         TEXT NOT NULL,
    description   TEXT

    creation_date DATE,
    imdb_rating   REAL,
    type          movie_type
);

CREATE TABLE content.person
(
    id        uuid PRIMARY KEY,
    full_name TEXT NOT NULL,
    birthdate DATE
);

CREATE TABLE content.genre
(
    id          UUID PRIMARY KEY,
    name        varchar(50) NOT NULL,
    description TEXT
);

-- M2M таблицы
CREATE TABLE content.movie_team
(
    id        UUID PRIMARY KEY,
    movie_id  UUID REFERENCES content.movie (id),
    person_id UUID REFERENCES content.person (id),
    role      movie_team_role,
    UNIQUE (movie_id, person_id, role)
);

CREATE TABLE content.movie_genre
(
    id       UUID PRIMARY KEY,
    movie_id UUID REFERENCES content.movie (id),
    genre_id UUID REFERENCES content.genre (id),
    UNIQUE (movie_id, genre_id)
);