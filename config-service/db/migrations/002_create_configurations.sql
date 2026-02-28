CREATE TABLE IF NOT EXISTS configurations (
    id              VARCHAR(26)  PRIMARY KEY,
    application_id  VARCHAR(26)  NOT NULL REFERENCES applications(id),
    name            VARCHAR(255) NOT NULL,
    comments        TEXT,
    config          JSONB        NOT NULL DEFAULT '{}'
);
