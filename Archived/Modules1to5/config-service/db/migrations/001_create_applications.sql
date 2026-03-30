CREATE TABLE IF NOT EXISTS applications (
    id          VARCHAR(26)  PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    comments    TEXT
);
