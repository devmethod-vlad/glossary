CREATE EXTENSION pg_trgm;

CREATE FUNCTION modified_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$BEGIN
            NEW.modified_at := NOW();
            RETURN NEW;
        END;$$;

CREATE TABLE glossary_element (
    id UUID PRIMARY KEY,
    abbreviation VARCHAR(500) NOT NULL DEFAULT '',
    term TEXT NOT NULL DEFAULT '',
    definition TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TRIGGER modified_trigger BEFORE UPDATE ON glossary_element FOR EACH ROW EXECUTE FUNCTION modified_trigger();

CREATE INDEX ix_abbreviation_trgm ON glossary_element USING gin (abbreviation gin_trgm_ops);
CREATE INDEX ix_term_trgm ON glossary_element USING gin (term gin_trgm_ops);
CREATE INDEX ix_definition_trgm ON glossary_element USING gin (definition gin_trgm_ops);

CREATE MATERIALIZED VIEW ge_splitted AS
SELECT *
FROM glossary_element
CROSS JOIN LATERAL
    regexp_split_to_table(glossary_element.abbreviation, %(abbreviation_delimeter)s || ' *')
    AS abbreviation_splitted
CROSS JOIN LATERAL
    regexp_split_to_table(glossary_element.term, %(term_delimeter)s || ' *')
    AS term_splitted;

CREATE OR REPLACE FUNCTION refresh_glossary_view() RETURNS TRIGGER
    LANGUAGE plpgsql
    AS $$ BEGIN
        REFRESH MATERIALIZED VIEW ge_splitted;
        RETURN NULL;
    END $$;

CREATE TRIGGER trig_refresh_glossary
AFTER INSERT OR DELETE OR UPDATE ON glossary_element
FOR EACH STATEMENT EXECUTE PROCEDURE refresh_glossary_view();
