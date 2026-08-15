
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('talent', 'organization')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS talent (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    display_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(100),
    country VARCHAR(100) NOT NULL DEFAULT 'Tanzania',
    city VARCHAR(100),
    bio TEXT,
    showcase_url TEXT,
    social_url TEXT,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    organization_type VARCHAR(100),
    country VARCHAR(100) NOT NULL DEFAULT 'Tanzania',
    city VARCHAR(100),
    website TEXT,
    social_url TEXT,
    description TEXT,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS opportunities (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(250) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(100),
    opportunity_type VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'Tanzania',
    city VARCHAR(100),
    age_category VARCHAR(100),
    description TEXT NOT NULL,
    requirements TEXT,
    application_url TEXT,
    contact_email VARCHAR(255),
    deadline DATE,
    status VARCHAR(30) NOT NULL DEFAULT 'published'
        CHECK (status IN ('draft', 'published', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_talent_category
    ON talent(category);

CREATE INDEX IF NOT EXISTS idx_talent_created_at
    ON talent(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_opportunities_category
    ON opportunities(category);

CREATE INDEX IF NOT EXISTS idx_opportunities_status
    ON opportunities(status);

CREATE INDEX IF NOT EXISTS idx_opportunities_created_at
    ON opportunities(created_at DESC);
