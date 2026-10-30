import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lingua.storage_setup")

async def setup_storage():
    logger.info("Configurando bucket de audio en Supabase Storage...")
    async with engine.begin() as conn:
        # 1. Crear el bucket 'lingua-audios' en storage.buckets si no existe
        await conn.execute(text("""
            INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
            VALUES (
                'lingua-audios',
                'lingua-audios',
                false,
                52428800,
                ARRAY['audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3', 'audio/ogg', 'audio/webm', 'audio/m4a', 'audio/x-m4a']
            )
            ON CONFLICT (id) DO UPDATE SET
                allowed_mime_types = EXCLUDED.allowed_mime_types,
                file_size_limit = EXCLUDED.file_size_limit;
        """))

        # 2. Configurar políticas de RLS para el bucket 'lingua-audios'
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies 
                    WHERE schemaname = 'storage' AND tablename = 'objects' AND policyname = 'Allow access to lingua-audios'
                ) THEN
                    CREATE POLICY "Allow access to lingua-audios"
                    ON storage.objects FOR ALL
                    TO authenticated, anon, service_role
                    USING (bucket_id = 'lingua-audios')
                    WITH CHECK (bucket_id = 'lingua-audios');
                END IF;
            END $$;
        """))

        res = await conn.execute(text("SELECT id, name, public, file_size_limit FROM storage.buckets WHERE id = 'lingua-audios';"))
        row = res.fetchone()
        logger.info(f"Bucket configurado exitosamente: {row}")

if __name__ == "__main__":
    asyncio.run(setup_storage())
