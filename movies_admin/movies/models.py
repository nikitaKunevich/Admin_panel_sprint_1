import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.fields import AutoLastModifiedField, AutoCreatedField


class Genre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(_('название'), max_length=255)
    description = models.TextField(_('описание'), blank=True)
    created_at = AutoCreatedField(_('время создания'))
    updated_at = AutoLastModifiedField(_('время последнего изменения'))

    class Meta:
        db_table = 'genre'
        verbose_name = _('жанр')
        verbose_name_plural = _('жанры')

    def __str__(self):
        return self.name


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    full_name = models.CharField(_('полное имя'), max_length=255)
    birth_date = models.DateField(_('дата рождения'))

    created_at = AutoCreatedField(_('время создания'))
    updated_at = AutoLastModifiedField(_('время последнего изменения'))

    class Meta:
        db_table = 'person'
        verbose_name = _('персона')
        verbose_name_plural = _('персоны')

    def __str__(self):
        return f"{self.full_name}, {self.birth_date}"


class FilmworkType(models.TextChoices):
    MOVIE = 'movie', _('фильм')
    SERIES = 'series', _('сериал')
    TV_SHOW = 'tv_show', _('шоу')


class MPAA_AgeRatingType(models.TextChoices):
    G = 'general', _('без ограничений')
    PG = 'parental_guidance', _('рекомендовано смотреть с родителями')
    PG_13 = 'parental_guidance_strong', _('просмотр не желателен детям до 13 лет')
    R = 'restricted', _('до 17 в сопровождении родителей')
    NC_17 = 'no_one_17_under', _('только с 18')


class FilmWork(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(_('название'), max_length=255)
    description = models.TextField(_('описание'), blank=True)
    type = models.CharField(_('тип'), max_length=20, choices=FilmworkType.choices, blank=True)
    genres = models.ManyToManyField(Genre, blank=True, db_table='genre_film_work', related_name='film_works')
    persons = models.ManyToManyField(Person, blank=True, through='FilmWorkPerson', related_name='film_works')
    rating = models.FloatField(_('рейтинг'), validators=[MinValueValidator(0)], blank=True, null=True)
    mpaa_age_rating = models.CharField(_('возрастной рейтинг'), choices=MPAA_AgeRatingType.choices, null=True,
                                       max_length=50)

    certificate = models.TextField(_('сертификат'), blank=True, null=True)
    file_path = models.FileField(_('файл'), upload_to='film_works/', blank=True, null=True)

    creation_date = models.DateField(_('дата создания фильма'), blank=True, null=True)

    created_at = AutoCreatedField(_('время создания'))
    updated_at = AutoLastModifiedField(_('время последнего изменения'))

    class Meta:
        db_table = 'film_work'
        verbose_name = _('кинопроизведение')
        verbose_name_plural = _('кинопроизведения')

    def __str__(self):
        return self.title


class FilmWorkPerson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    role = models.CharField(_('профессия'), max_length=255)
    film_work = models.ForeignKey(FilmWork, on_delete=models.deletion.CASCADE, verbose_name=_('фильм'),
                                  related_name='film_work_team')
    person = models.ForeignKey(Person, on_delete=models.deletion.CASCADE, verbose_name=_('человек'),
                               related_name='worked_on_titles')

    created_at = AutoCreatedField(_('время создания'))

    def __str__(self):
        return f"{self.person} in {self.film_work} as {self.role}"

    class Meta:
        db_table = 'person_film_work'
        verbose_name = _('участник фильма')
        verbose_name_plural = _('участники фильмов')
        unique_together = (('film_work', 'person', 'role'),)
