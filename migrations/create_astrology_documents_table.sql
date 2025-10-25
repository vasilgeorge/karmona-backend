-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create astrology_documents table for vector storage
CREATE TABLE IF NOT EXISTS astrology_documents (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(1024),  -- Amazon Titan v2 produces 1024-dimensional embeddings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on embedding for faster similarity search
CREATE INDEX IF NOT EXISTS astrology_documents_embedding_idx
ON astrology_documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index on metadata for filtering
CREATE INDEX IF NOT EXISTS astrology_documents_metadata_idx
ON astrology_documents
USING GIN (metadata);

-- Create index on created_at for date-based queries
CREATE INDEX IF NOT EXISTS astrology_documents_created_at_idx
ON astrology_documents (created_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_astrology_documents_updated_at ON astrology_documents;
CREATE TRIGGER update_astrology_documents_updated_at
    BEFORE UPDATE ON astrology_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function for semantic search
CREATE OR REPLACE FUNCTION match_astrology_documents(
    query_embedding vector(1024),
    match_threshold float DEFAULT 0.3,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    metadata JSONB,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        astrology_documents.id,
        astrology_documents.content,
        astrology_documents.metadata,
        1 - (astrology_documents.embedding <=> query_embedding) AS similarity
    FROM astrology_documents
    WHERE 1 - (astrology_documents.embedding <=> query_embedding) > match_threshold
    ORDER BY astrology_documents.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Grant permissions (adjust based on your Supabase setup)
GRANT ALL ON astrology_documents TO service_role;
GRANT SELECT ON astrology_documents TO anon;
GRANT SELECT ON astrology_documents TO authenticated;
