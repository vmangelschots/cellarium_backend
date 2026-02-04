# Copilot Instructions for Cellarium Backend

Purpose: make AI agents effective immediately in this Django + DRF repo by codifying the actual patterns, workflows, and decisions in use.

## Architecture
- Django 5 + DRF app with a single domain app: [winemanager](../winemanager/).
- API is namespaced under `/api` via [project URLs](../cellarium_backend/urls.py) and DRF `DefaultRouter` in [winemanager/urls.py](../winemanager/urls.py).
- Auth: JWT via SimpleJWT endpoints exposed at `/api/auth/token/` and `/api/auth/token/refresh/` in [project URLs](../cellarium_backend/urls.py). Default permission is authenticated.
- DB: SQLite (dev) configured in [settings.py](../cellarium_backend/settings.py). CORS is fully open for development.

## Key Patterns
- ViewSets + Router: Endpoints are implemented as `ModelViewSet`s and registered in [winemanager/urls.py](../winemanager/urls.py) with `DefaultRouter`.
  - Wines: [WineViewSet](../winemanager/views.py) exposes search/order and annotates counts in `get_queryset()` (not in serializer). Region is a ForeignKey to the Region model.
  - Regions: [RegionViewSet](../winemanager/views.py) manages wine regions with CRUD operations. Regions have a name and country, with `unique_together` constraint. Annotates `wine_count` in `get_queryset()`.
  - Bottles: [BottleViewSet](../winemanager/views.py) supports filtering by `wine` and defines idempotent side-effect actions via `@action(detail=True)` (`consume`, `undo_consume`).
  - Stores: [StoreViewSet](../winemanager/views.py) is a standard CRUD set.
- Serialization: [WineSerializer](../winemanager/serializers.py) includes computed, read-only fields `bottle_count` and `in_stock_count`, validates `rating` bounds, and provides nested `region` details (read-only). Accepts `region` as ID for write operations. [RegionSerializer](../winemanager/serializers.py) serializes regions with country codes. Other serializers are straight `ModelSerializer`s.
- Models: See [winemanager/models.py](../winemanager/models.py) for `Wine`, `Region`, `Bottle`, `Store`. `Wine` links to optional `Region` (SET_NULL on delete) and uses ISO Alpha-2 country codes. `Region` has `unique_together = ['name', 'country']` allowing same region names in different countries. `Bottle` links to `Wine` and optional `Store`; `Wine.rating` is a `Decimal` constrained to 0.0–5.0.
- Permissions/Auth: `REST_FRAMEWORK` in [settings.py](../cellarium_backend/settings.py) sets `IsAuthenticated` globally; use JWT Authorization headers on API calls.

## Developer Workflow (Docker-first)
- Build: `docker-compose build`
- Migrate: `docker-compose run web python manage.py migrate`
- Run: `docker-compose up` (serves at http://localhost:8000)
- Admin: http://localhost:8000/admin (create superuser with `docker-compose run web python manage.py createsuperuser`)
- Tests: `docker-compose run web python manage.py test`
- Logs: `docker-compose logs -f`
- Dependencies: edit [requirements.txt](../requirements.txt) then `docker-compose build`.

Required Python deps used in code/settings: `Django`, `djangorestframework`, `django-cors-headers`, `django-countries`, `django-filter`, `djangorestframework-simplejwt`.

## API Usage Examples
- Obtain tokens:
  - POST `/api/auth/token/` with `{"username":"...","password":"..."}` → `{ access, refresh }`
  - POST `/api/auth/token/refresh/` with `{ "refresh": "..." }` → `{ access }`
- Authenticated requests: send `Authorization: Bearer <access>`.
- Wines: GET `/api/wines/?search=FR&ordering=-vintage`
  - Search fields: `name`, `country` (ISO Alpha-2 code), `region__name` (searches region name), `grape_varieties`, `wine_type`
  - Ordering fields: `name`, `vintage`, `country`, `bottle_count`, `in_stock_count`
  - Response includes `bottle_count`, `in_stock_count` (from queryset annotations), and nested `region` object with `{id, name, country}`
  - Country field uses ISO Alpha-2 codes (e.g., 'FR', 'IT', 'US', 'ES')
  - Creating wine: POST `/api/wines/` with `{"name": "Bordeaux", "country": "FR", "region": <region_id>}`
  - Example response: `{"id": 1, "name": "Bordeaux", "region": {"id": 5, "name": "Bordeaux", "country": "FR"}, "country": "FR", ...}`
- Regions: GET `/api/regions/`, POST `/api/regions/` with `{"name": "Napa Valley", "country": "US"}`
  - Search fields: `name`, `country`
  - Ordering fields: `name`, `country`, `wine_count`
  - Response includes `wine_count` annotation showing number of wines from this region
  - Unique constraint: same region name can exist in different countries, but not duplicates within same country
- Bottles: GET `/api/bottles/?wine=<wine_id>`; POST `/api/bottles/<id>/consume/`; POST `/api/bottles/<id>/undo_consume/` (both idempotent).

## Conventions to Follow
- Add new REST resources as `ModelViewSet` with router registration in [winemanager/urls.py](../winemanager/urls.py).
- Prefer queryset annotations (in `get_queryset`) for aggregated or computed list fields, then expose as read-only serializer fields.
- For state-changing, recordable side-effects on a single resource, use `@action(detail=True, methods=["post"])` and keep actions idempotent when feasible.
- Update [admin.py](../winemanager/admin.py) to register new models for quick inspection.
- When changing models, create a migration and run it: `docker-compose run web python manage.py makemigrations && docker-compose run web python manage.py migrate`.

## Where to Look
- Settings and global DRF/CORS/JWT config: [cellarium_backend/settings.py](../cellarium_backend/settings.py)
- Project URLs + JWT endpoints: [cellarium_backend/urls.py](../cellarium_backend/urls.py)
- App routing: [winemanager/urls.py](../winemanager/urls.py)
- Domain logic: [winemanager/models.py](../winemanager/models.py), [winemanager/views.py](../winemanager/views.py), [winemanager/serializers.py](../winemanager/serializers.py)
- Container/dev workflow: [docker-compose.yml](../docker-compose.yml), [Dockerfile](../Dockerfile), [README.md](../README.md)

## Gotchas
- The project enforces auth by default; unauthenticated API calls will fail unless endpoints override permissions.
- Ensure `django-filter`, `django-countries`, and `djangorestframework-simplejwt` are installed to match settings; add them to [requirements.txt](../requirements.txt) if missing and rebuild.
- The `country` field on Wine and Region uses ISO Alpha-2 codes (e.g., 'FR', 'IT', 'US'). Full country names (e.g., 'France') will be rejected.
- When creating a Wine with a region, you must provide `region` as an integer ID of an existing Region object, not a string. The API response will include the full nested region object.
