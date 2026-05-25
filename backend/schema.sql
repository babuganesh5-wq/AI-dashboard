-- database/schema.sql
-- Antigravity AI Relational Identity Resolution Map & Long-Term Semantic Vector Memory Schema
-- Adapted specifically for Rhythm Academy Business Operations & Automated Flows

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgvector;

-- Master CRM Prospect Table
CREATE TABLE IF NOT EXISTS CRM_Prospects (
    prospect_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email_hashed VARCHAR(64) UNIQUE,
    phone_hashed VARCHAR(64) UNIQUE,
    lead_score NUMERIC(3, 2) DEFAULT 0.00,
    current_funnel_stage VARCHAR(50) DEFAULT 'INQUIRY', -- INQUIRY, QUALIFIED, OPPORTUNITY, CUSTOMER
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Identity Resolution Map for Social Handles
-- Resolves multiple platforms comments & messaging to a single unified prospect
CREATE TABLE IF NOT EXISTS Platform_Identities (
    identity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prospect_id UUID REFERENCES CRM_Prospects(prospect_id) ON DELETE CASCADE,
    platform_name VARCHAR(50) NOT NULL, -- 'INSTAGRAM', 'FACEBOOK', 'WHATSAPP', 'YOUTUBE', 'TELEGRAM'
    external_platform_id VARCHAR(255) NOT NULL, -- external ID (e.g. Meta PSID, Channel ID, Telegram Chat ID)
    handle_name VARCHAR(150),
    attribution_gclid VARCHAR(255),
    attribution_fbclid VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_name, external_platform_id)
);

-- Comment trigger registration table
-- Matches high-engagement comment keywords to targeted automated actions
CREATE TABLE IF NOT EXISTS Comment_Triggers (
    trigger_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform_name VARCHAR(50) NOT NULL, -- 'INSTAGRAM', 'YOUTUBE'
    keyword VARCHAR(100) NOT NULL, -- e.g. 'GROWTH', 'LEAD', 'SCALE'
    workflow_id VARCHAR(100) NOT NULL, -- target workflow block to trigger
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_name, keyword)
);

-- Deep Semantic Interaction Long-Term Memory
-- Cosine-similarity vector memories matching interaction snippets
CREATE TABLE IF NOT EXISTS Multi_Agent_Conversation_Memory (
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prospect_id UUID REFERENCES CRM_Prospects(prospect_id) ON DELETE CASCADE,
    speaker_role VARCHAR(20) NOT NULL, -- 'PROSPECT', 'AGENT'
    message_body TEXT NOT NULL,
    embedding VECTOR(1536), -- Created by text-embedding-3 for deep semantic RAG context mapping
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- IVFFlat index for fast cosine-similarity search
CREATE INDEX IF NOT EXISTS idx_memory_embedding 
ON Multi_Agent_Conversation_Memory 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- =========================================================================
-- RHYTHM ACADEMY SPECIALIZED SCHEMAS
-- Track course programs enrollment, installments ledgers, batches, and faculty
-- =========================================================================

-- Safe creation of ENUM types
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rhythm_course_program') THEN
        CREATE TYPE rhythm_course_program AS ENUM ('3M_PRODUCTION', '6M_PRODUCTION', 'DIPLOMA', 'MUSIC_SCHOOL');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_installment_status') THEN
        CREATE TYPE payment_installment_status AS ENUM ('PAID', 'PENDING', 'OVERDUE');
    END IF;
END $$;

-- Specialized leads table for course enrollment and WhatsApp routing
CREATE TABLE IF NOT EXISTS Rhythm_Academy_Leads (
    lead_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prospect_id UUID REFERENCES CRM_Prospects(prospect_id) ON DELETE CASCADE,
    student_name VARCHAR(200) NOT NULL,
    whatsapp_number VARCHAR(20) NOT NULL,
    target_program rhythm_course_program DEFAULT '6M_PRODUCTION',
    lead_source VARCHAR(100) DEFAULT 'META_ADS', -- META_ADS, ORGANIC, REFERRAL
    is_qualified BOOLEAN DEFAULT FALSE,
    studio_visit_scheduled TIMESTAMP WITH TIME ZONE,
    studio_visit_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Relational split installments ledger for ₹15,000 recovery and follow-ups
CREATE TABLE IF NOT EXISTS Rhythm_Installments_Ledger (
    installment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES Rhythm_Academy_Leads(lead_id) ON DELETE CASCADE,
    installment_number INT NOT NULL, -- 1 or 2 (split installments)
    amount NUMERIC(10, 2) NOT NULL DEFAULT 15000.00, -- ₹15,000 standard split payment
    status payment_installment_status DEFAULT 'PENDING',
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    payment_date TIMESTAMP WITH TIME ZONE,
    reminder_sent_count INT DEFAULT 0,
    last_reminder_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Batch scheduler database table supporting double simultaneous batches and faculty tracking
CREATE TABLE IF NOT EXISTS Rhythm_Batches_Faculty (
    batch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_name VARCHAR(100) NOT NULL, -- e.g. 'Batch Alpha', 'Batch Beta'
    program_type rhythm_course_program DEFAULT '6M_PRODUCTION',
    assigned_faculty_name VARCHAR(150) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    scheduled_slots VARCHAR(100), -- e.g. 'Mon/Wed 10:00-12:00'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
