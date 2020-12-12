from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict
from uuid import uuid4, UUID


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