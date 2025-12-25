-- Schema from here: https://docs.openalex.org/download-all-data/upload-to-your-database/load-to-a-relational-database

-- Authors tables
CREATE TABLE authors (
    id TEXT PRIMARY KEY,
    orcid TEXT,
    display_name TEXT,
    display_name_alternatives TEXT, -- Changed from JSON
    works_count INTEGER,
    cited_by_count INTEGER,
    last_known_institution TEXT,
    works_api_url TEXT,
    updated_date TEXT -- Changed from TIMESTAMP
);

CREATE TABLE authors_counts_by_year (
    author_id TEXT,
    year INTEGER,
    works_count INTEGER,
    cited_by_count INTEGER,
    oa_works_count INTEGER,
    PRIMARY KEY (author_id, year)
);

CREATE TABLE authors_ids (
    author_id TEXT PRIMARY KEY,
    openalex TEXT,
    orcid TEXT,
    scopus TEXT,
    twitter TEXT,
    wikipedia TEXT,
    mag INTEGER -- Changed from BIGINT
);

-- Topics table
CREATE TABLE topics (
    id TEXT PRIMARY KEY,
    display_name TEXT,
    subfield_id TEXT,
    subfield_display_name TEXT,
    field_id TEXT,
    field_display_name TEXT,
    domain_id TEXT,
    domain_display_name TEXT,
    description TEXT,
    keywords TEXT,
    works_api_url TEXT,
    wikipedia_id TEXT,
    works_count INTEGER,
    cited_by_count INTEGER,
    updated_date TEXT -- Changed from TIMESTAMP
);

-- Concepts tables
CREATE TABLE concepts (
    id TEXT PRIMARY KEY,
    wikidata TEXT,
    display_name TEXT,
    level INTEGER,
    description TEXT,
    works_count INTEGER,
    cited_by_count INTEGER,
    image_url TEXT,
    image_thumbnail_url TEXT,
    works_api_url TEXT,
    updated_date TEXT -- Changed from TIMESTAMP
);

CREATE TABLE concepts_ancestors (
    concept_id TEXT,
    ancestor_id TEXT
);

CREATE TABLE concepts_counts_by_year (
    concept_id TEXT,
    year INTEGER,
    works_count INTEGER,
    cited_by_count INTEGER,
    oa_works_count INTEGER,
    PRIMARY KEY (concept_id, year)
);

CREATE TABLE concepts_ids (
    concept_id TEXT PRIMARY KEY,
    openalex TEXT,
    wikidata TEXT,
    wikipedia TEXT,
    umls_aui TEXT, -- Changed from JSON
    umls_cui TEXT, -- Changed from JSON
    mag INTEGER -- Changed from BIGINT
);

CREATE TABLE concepts_related_concepts (
    concept_id TEXT,
    related_concept_id TEXT,
    score REAL
);

-- Institutions tables
CREATE TABLE institutions (
    id TEXT PRIMARY KEY,
    ror TEXT,
    display_name TEXT,
    country_code TEXT,
    type TEXT,
    homepage_url TEXT,
    image_url TEXT,
    image_thumbnail_url TEXT,
    display_name_acronyms TEXT, -- Changed from JSON
    display_name_alternatives TEXT, -- Changed from JSON
    works_count INTEGER,
    cited_by_count INTEGER,
    works_api_url TEXT,
    updated_date TEXT -- Changed from TIMESTAMP
);

CREATE TABLE institutions_associated_institutions (
    institution_id TEXT,
    associated_institution_id TEXT,
    relationship TEXT
);

CREATE TABLE institutions_counts_by_year (
    institution_id TEXT,
    year INTEGER,
    works_count INTEGER,
    cited_by_count INTEGER,
    oa_works_count INTEGER,
    PRIMARY KEY (institution_id, year)
);

CREATE TABLE institutions_geo (
    institution_id TEXT PRIMARY KEY,
    city TEXT,
    geonames_city_id TEXT,
    region TEXT,
    country_code TEXT,
    country TEXT,
    latitude REAL,
    longitude REAL
);

CREATE TABLE institutions_ids (
    institution_id TEXT PRIMARY KEY,
    openalex TEXT,
    ror TEXT,
    grid TEXT,
    wikipedia TEXT,
    wikidata TEXT,
    mag INTEGER -- Changed from BIGINT
);

-- Publishers tables
CREATE TABLE publishers (
    id TEXT PRIMARY KEY,
    display_name TEXT,
    alternate_titles TEXT, -- Changed from JSON
    country_codes TEXT, -- Changed from JSON
    hierarchy_level INTEGER,
    parent_publisher TEXT,
    works_count INTEGER,
    cited_by_count INTEGER,
    sources_api_url TEXT,
    updated_date TEXT -- Changed from TIMESTAMP
);

CREATE TABLE publishers_counts_by_year (
    publisher_id TEXT,
    year INTEGER,
    works_count INTEGER,
    cited_by_count INTEGER,
    oa_works_count INTEGER,
    PRIMARY KEY (publisher_id, year)
);

CREATE TABLE publishers_ids (
    publisher_id TEXT,
    openalex TEXT,
    ror TEXT,
    wikidata TEXT
);

-- Sources tables
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    issn_l TEXT,
    issn TEXT, -- Changed from JSON
    display_name TEXT,
    publisher TEXT,
    works_count INTEGER,
    cited_by_count INTEGER,
    is_oa INTEGER, -- Changed from BOOLEAN
    is_in_doaj INTEGER, -- Changed from BOOLEAN
    homepage_url TEXT,
    works_api_url TEXT,
    updated_date TEXT -- Changed from TIMESTAMP
);

CREATE TABLE sources_counts_by_year (
    source_id TEXT,
    year INTEGER,
    works_count INTEGER,
    cited_by_count INTEGER,
    oa_works_count INTEGER,
    PRIMARY KEY (source_id, year)
);

CREATE TABLE sources_ids (
    source_id TEXT,
    openalex TEXT,
    issn_l TEXT,
    issn TEXT, -- Changed from JSON
    mag INTEGER, -- Changed from BIGINT
    wikidata TEXT,
    fatcat TEXT
);

-- Works tables
CREATE TABLE works (
    id TEXT PRIMARY KEY,
    doi TEXT,
    title TEXT,
    display_name TEXT,
    publication_year INTEGER,
    publication_date TEXT,
    type TEXT,
    cited_by_count INTEGER,
    is_retracted INTEGER, -- Changed from BOOLEAN
    is_paratext INTEGER, -- Changed from BOOLEAN
    cited_by_api_url TEXT,
    abstract_inverted_index TEXT, -- Changed from JSON
    language TEXT
);

CREATE TABLE works_primary_locations (
    work_id TEXT,
    source_id TEXT,
    landing_page_url TEXT,
    pdf_url TEXT,
    is_oa INTEGER, -- Changed from BOOLEAN
    version TEXT,
    license TEXT
);

CREATE TABLE works_locations (
    work_id TEXT,
    source_id TEXT,
    landing_page_url TEXT,
    pdf_url TEXT,
    is_oa INTEGER, -- Changed from BOOLEAN
    version TEXT,
    license TEXT
);

CREATE TABLE works_best_oa_locations (
    work_id TEXT,
    source_id TEXT,
    landing_page_url TEXT,
    pdf_url TEXT,
    is_oa INTEGER, -- Changed from BOOLEAN
    version TEXT,
    license TEXT
);

CREATE TABLE works_authorships (
    work_id TEXT,
    author_position TEXT,
    author_id TEXT,
    institution_id TEXT
    -- raw_affiliation_string TEXT # Removed from the schema because it's confusing. Work['authorships'] has authorship['institutions'] and authorship['affiliations']. Omitting this allowed me to use ['institutions'] only.
);

CREATE TABLE works_biblio (
    work_id TEXT PRIMARY KEY,
    volume TEXT,
    issue TEXT,
    first_page TEXT,
    last_page TEXT
);

CREATE TABLE works_topics (
    work_id TEXT,
    topic_id TEXT,
    score REAL
);

CREATE TABLE works_concepts (
    work_id TEXT,
    concept_id TEXT,
    score REAL
);

CREATE TABLE works_ids (
    work_id TEXT PRIMARY KEY,
    openalex TEXT,
    doi TEXT,
    mag INTEGER, -- Changed from BIGINT
    pmid TEXT,
    pmcid TEXT
);

CREATE TABLE works_mesh (
    work_id TEXT,
    descriptor_ui TEXT,
    descriptor_name TEXT,
    qualifier_ui TEXT,
    qualifier_name TEXT,
    is_major_topic INTEGER -- Changed from BOOLEAN
);

CREATE TABLE works_open_access (
    work_id TEXT PRIMARY KEY,
    is_oa INTEGER, -- Changed from BOOLEAN
    oa_status TEXT,
    oa_url TEXT,
    any_repository_has_fulltext INTEGER -- Changed from BOOLEAN
);

CREATE TABLE works_referenced_works (
    work_id TEXT,
    referenced_work_id TEXT
);

CREATE TABLE works_related_works (
    work_id TEXT,
    related_work_id TEXT
);

-- Indexes
CREATE INDEX concepts_ancestors_concept_id_idx ON concepts_ancestors(concept_id);
CREATE INDEX concepts_related_concepts_concept_id_idx ON concepts_related_concepts(concept_id);
CREATE INDEX concepts_related_concepts_related_concept_id_idx ON concepts_related_concepts(related_concept_id);
CREATE INDEX works_primary_locations_work_id_idx ON works_primary_locations(work_id);
CREATE INDEX works_locations_work_id_idx ON works_locations(work_id);
CREATE INDEX works_best_oa_locations_work_id_idx ON works_best_oa_locations(work_id);