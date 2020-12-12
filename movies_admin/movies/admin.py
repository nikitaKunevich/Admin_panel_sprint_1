from django.contrib import admin

from movies.models import FilmWork, FilmWorkPerson, Genre, Person


class PersonRoleInline(admin.TabularInline):
    model = FilmWorkPerson
    extra = 0


@admin.register(FilmWork)
class FilmworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'creation_date', 'rating')
    list_filter = ('type', 'rating')
    search_fields = ('title', 'description', 'id')

    fields = ('title', 'type', 'description', 'creation_date', 'certificate',
              'file_path', 'mpaa_age_rating', 'rating', 'genres')

    inlines = [
        PersonRoleInline
    ]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date')
    search_fields = ('full_name',)
