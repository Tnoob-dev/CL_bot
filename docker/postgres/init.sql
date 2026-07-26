-- Runs once on first boot of the dev Postgres container.
-- POSTGRES_DB already creates "clbot_users"; create the posts DB too.
CREATE DATABASE clbot_posts OWNER clbot;
