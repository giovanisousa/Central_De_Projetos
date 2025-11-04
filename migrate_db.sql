-- Migração: Adicionar e popular coluna status_id
-- Executar via: railway run python -c "import os, subprocess; subprocess.run(['psql', os.environ['DATABASE_URL'], '-f', 'migrate_db.sql'])"

-- 1. Adicionar coluna status_id
ALTER TABLE projects ADD COLUMN IF NOT EXISTS status_id VARCHAR;

-- 2. Popular status_id a partir do full_data_json
UPDATE projects 
SET status_id = (full_data_json::json->'status'->>'id') 
WHERE full_data_json IS NOT NULL 
  AND (status_id IS NULL OR status_id = '');

-- 3. Popular tags quando vazias
UPDATE projects 
SET tags = (full_data_json::json->'tags')::text 
WHERE (tags IS NULL OR trim(tags) = '') 
  AND full_data_json IS NOT NULL;

-- 4. Verificar projeto específico
SELECT 'Verificando projeto 2376502000002326783:' as info;
SELECT id, status_id, status_atual, substring(tags, 1, 100) as tags 
FROM projects 
WHERE id = '2376502000002326783';

-- 5. Estatísticas gerais
SELECT 'Estatísticas gerais:' as info;
SELECT 
  COUNT(*) FILTER (WHERE status_id IS NULL OR status_id = '') as sem_status_id,
  COUNT(*) FILTER (WHERE tags IS NULL OR trim(tags) = '') as sem_tags,
  COUNT(*) as total
FROM projects;
