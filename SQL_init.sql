-- Creating table for countries
CREATE TABLE countries (
    iso_code TEXT PRIMARY KEY,
    iso2_code TEXT UNIQUE,
    name TEXT NOT NULL,
    region TEXT,
    income_level TEXT,
    latitude REAL,
    longitude REAL
);

-- Creating table for indicators
CREATE TABLE indicators (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    unit TEXT,
    description TEXT,
    category TEXT
);

-- Creating table for country_data
CREATE TABLE country_data (
    country_code TEXT,
    indicator_code TEXT,
    year INTEGER NOT NULL,
    value REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (country_code, indicator_code, year),
    CONSTRAINT fk_country_data_country FOREIGN KEY (country_code) REFERENCES countries(iso_code),
    CONSTRAINT fk_country_data_indicator FOREIGN KEY (indicator_code) REFERENCES indicators(code)
);

-- Creating indexes for performance
CREATE INDEX idx_country_data_country_year ON country_data (country_code, year);
CREATE INDEX idx_country_data_indicator_year ON country_data (indicator_code, year);
CREATE INDEX idx_country_data_composite ON country_data (country_code, indicator_code, year);