"""
Модуль мигрирует данные о фильмах из SQLite в PostgreSQL в новую схему.
"""

# todo: есть невалидные id актеров и писателей (с именами n/a, ''), их надо убрат их всех таблиц.

import json
import sqlite3
from dataclasses import astuple, dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Sequence
from uuid import UUID, uuid4

import psycopg2
import psycopg2.extras


def sqlite_dict_factory(cursor, row):
    """SQLite dict_factory."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def sqlite_dict_connection_factory(*args, **kwargs):
    con = sqlite3.Connection(*args, **kwargs)
    con.row_factory = sqlite_dict_factory
    return con


EMPTY_VALUES = ["N/A", ""]
INVALID_WRITERS_IDS = []


def to_none_if_empty(value):
    if value in EMPTY_VALUES:
        return None
    else:
        return value


# -------------original tables-----------------
@dataclass
class OriginalMovie:
    id: str
    genre: Optional[str]
    director: Optional[str]
    title: str
    plot: Optional[str]
    imdb_rating: Optional[str]
    writers: List[str]

    def get_genres(self) -> List[str]:
        genres = self.genre.split(", ") if self.genre else []
        return list(set(genres))

    def get_directors(self) -> List[str]:
        directors = self.director.split(", ") if self.director else []
        return list(set(directors))

    def to_transformed_movie(self) -> "TransformedMovie":
        return TransformedMovie(
            id=uuid4(),
            title=self.title,
            description=self.plot,
            rating=float(self.imdb_rating) if self.imdb_rating else None,
        )


OriginalId = str
OriginalActorId = int
Name = str
OriginalMovieActors = Dict[OriginalId, List[OriginalActorId]]
OriginalActors = Dict[OriginalActorId, Name]
OriginalWriters = Dict[OriginalId, Name]


@dataclass
class OriginalData:
    movies: List[OriginalMovie]
    movie_actors: OriginalMovieActors
    actor_names: OriginalActors
    writer_names: OriginalWriters


# ------------------ transformed tables ------------------------
@dataclass
class TransformedMovie:
    id: UUID
    title: str
    description: Optional[str] = None
    creation_date: Optional[date] = None
    certificate: Optional[str] = None
    file_path: Optional[str] = None
    rating: Optional[float] = None
    type: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransformedPerson:
    id: UUID
    full_name: str
    birth_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransformedMoviePerson:
    id: UUID
    movie_id: UUID
    person_id: UUID
    role: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransformedGenre:
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransformedMovieGenre:
    id: UUID
    movie_id: UUID
    genre_id: UUID
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransformedData:
    movies: List[TransformedMovie]
    movie_persons: List[TransformedMoviePerson]
    persons: List[TransformedPerson]
    movie_genres: List[TransformedMovieGenre]
    genres: List[TransformedGenre]


def clean_original_movie_fields(movie):
    return OriginalMovie(
        id=movie.id,
        genre=to_none_if_empty(movie.genre),
        director=to_none_if_empty(movie.director),
        title=movie.title,
        plot=to_none_if_empty(movie.plot),
        imdb_rating=to_none_if_empty(movie.imdb_rating),
        writers=to_none_if_empty(movie.writers),
    )


def fetch_sqlite_data(connection) -> OriginalData:
    """Считываем все данные из старой таблицы, убирая невалидные данные (N/A, '')."""

    # noinspection PyTypeChecker
    cursor = connection.cursor()

    cursor.execute("select DISTINCT * from actors")
    invalid_actors_ids = []
    actor_names: OriginalActors = {}

    for id_name in cursor.fetchall():
        if id_name["name"] in EMPTY_VALUES:
            invalid_actors_ids.append(id_name["id"])
        else:
            actor_names[id_name["id"]] = id_name["name"]

    cursor.execute("select DISTINCT * from writers")
    writer_names: OriginalWriters = {}

    for id_name in cursor.fetchall():
        if id_name["name"] in EMPTY_VALUES:
            INVALID_WRITERS_IDS.append(id_name["id"])
        else:
            writer_names[id_name["id"]] = id_name["name"]

    cursor.execute("select DISTINCT * from movie_actors")
    movie_actors: OriginalMovieActors = {}
    for movie_actor in cursor.fetchall():
        actors = movie_actors.setdefault(movie_actor["movie_id"], [])
        actor_id = int(movie_actor["actor_id"])
        if actor_id not in invalid_actors_ids:
            actors.append(actor_id)

    movies: List[OriginalMovie] = []
    cursor.execute("select DISTINCT * from movies")
    for movie in cursor.fetchall():
        if movie["writers"]:
            writers = [item["id"] for item in json.loads(movie["writers"])]
        else:
            writers = [movie["writer"]]
        writers = [writer for writer in writers if writer not in INVALID_WRITERS_IDS]
        unique_writers = list(set(writers))
        processed_movie = OriginalMovie(id=movie["id"], genre=movie["genre"],
                                        director=movie["director"], title=movie["title"],
                                        plot=movie["plot"], imdb_rating=movie["imdb_rating"],
                                        writers=unique_writers)
        movies.append(processed_movie)

    cursor.close()

    return OriginalData(
        movies=movies,
        movie_actors=movie_actors,
        actor_names=actor_names,
        writer_names=writer_names
    )


def migrate_data_to_new_schema(original_data: OriginalData) -> TransformedData:
    """Трансформируем данные из старой схемы в новую схему."""

    cleaned_movies = [clean_original_movie_fields(movie) for movie in original_data.movies]

    # Кэш old_id -> new_id уже созданных объектов.
    added_directors = dict()  # name -> id
    added_genres = dict()  # name -> id
    added_actors = dict()  # old_id -> new_id
    added_writers = dict()  # old_id -> new_id

    transformed_movie_persons: List[TransformedMoviePerson] = []
    transformed_movie_genres: List[TransformedMovieGenre] = []
    transformed_movies: List[TransformedMovie] = []
    transformed_persons: List[TransformedPerson] = []
    transformed_genres: List[TransformedGenre] = []

    for original_movie in cleaned_movies:
        # Преобразуем объект фильма из старой схемы в новую.
        transformed_movie = original_movie.to_transformed_movie()
        transformed_movies.append(transformed_movie)

        # Суть всех циклов ниже одинаковая:
        # Среди всех old_id, для которых я еще не создал новые объекты -> создать новый объект.
        # И добавить для него связь фильм-объект.

        # Создание объектов таблиц genre и movie_genre.
        for genre in original_movie.get_genres():
            if genre not in added_genres:
                genre_id = uuid4()
                added_genres[genre] = genre_id
                transformed_genres.append(TransformedGenre(id=genre_id, name=genre))
            movie_genre = TransformedMovieGenre(uuid4(), transformed_movie.id, added_genres[genre])
            transformed_movie_genres.append(movie_genre)

        # ------------ Создание объектов таблиц person и movie_person. --------------------
        for director in original_movie.get_directors():
            if director not in added_directors:
                person_id = uuid4()
                added_directors[director] = person_id
                transformed_persons.append(TransformedPerson(id=person_id, full_name=director))
            movie_person = TransformedMoviePerson(uuid4(), transformed_movie.id, added_directors[director], "director")
            transformed_movie_persons.append(movie_person)

        for actor_id in original_data.movie_actors[original_movie.id]:
            if actor_id not in added_actors:
                fullname = original_data.actor_names[actor_id]
                person_id = uuid4()
                added_actors[actor_id] = person_id
                transformed_persons.append(TransformedPerson(id=person_id, full_name=fullname))
            movie_person = TransformedMoviePerson(uuid4(), transformed_movie.id, added_actors[actor_id], "actor")
            transformed_movie_persons.append(movie_person)

        for writer_id in original_movie.writers:
            if writer_id not in added_writers:
                fullname = original_data.writer_names[writer_id]
                person_id = uuid4()
                added_writers[writer_id] = person_id
                transformed_persons.append(TransformedPerson(id=person_id, full_name=fullname))
            movie_person = TransformedMoviePerson(uuid4(), transformed_movie.id, added_writers[writer_id], "writer")
            transformed_movie_persons.append(movie_person)

    return TransformedData(
        movies=transformed_movies,
        movie_persons=transformed_movie_persons,
        persons=transformed_persons,
        movie_genres=transformed_movie_genres,
        genres=transformed_genres,
    )


def insert_rows_into_table(cursor, table_name: str, rows: Sequence[Sequence]):
    """
    Генерирует одну длинную строку с значениями для insert с правильным кол-вом параметров в зависимости от количества
    параметров в строке, и исполняет INSERT с этими значениями для заданной таблицы.
    """
    column_count = len(rows[0])
    values_template = "(" + ",".join(("%s",) * column_count) + ")"
    prepared_values = ",".join(cursor.mogrify(values_template, row).decode() for row in rows)
    cursor.execute("insert into %s values %s" % (table_name, prepared_values))


def write_data_to_postgres(transformed_data: TransformedData, connection):
    """Записываем трансформарованные данные в PostgreSQL."""

    psycopg2.extras.register_uuid()  # Для конвертации python UUID в psql ::uuid.

    with connection.cursor() as curs:
        insert_rows_into_table(curs, "content.film_work", [astuple(movie) for movie in transformed_data.movies])
        insert_rows_into_table(curs, "content.genre", [astuple(genre) for genre in transformed_data.genres])
        insert_rows_into_table(
            curs, "content.genre_film_work", [astuple(movie_genre) for movie_genre in transformed_data.movie_genres]
        )
        insert_rows_into_table(curs, "content.person", [astuple(person) for person in transformed_data.persons])
        insert_rows_into_table(
            curs,
            "content.person_film_work",
            [astuple(movie_person) for movie_person in transformed_data.movie_persons],
        )
