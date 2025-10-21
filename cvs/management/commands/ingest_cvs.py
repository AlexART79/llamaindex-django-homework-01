from django.core.management.base import BaseCommand
from django.conf import settings

# from chromadb import PersistentClient
import chromadb
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.storage_context import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from cvs.models import CV

def cv_to_text(cv: CV) -> str:
    return "\n".join([
        f"CV ID: {cv.id}",
        f"Name: {cv.name}",
        f"Job Title: {cv.job_title.name}",
        f"Years of Experience: {cv.years_of_experience}",
        f"Skills: {cv.skills}",
        f"Education: {cv.education}",
        "Past experience:",
        cv.past_experience,
    ])

def cv_to_document(cv: CV) -> Document:
    return Document(
        text=cv_to_text(cv),
        metadata={
            "cv_id": cv.id,
            "name": cv.name,
            "job_title": cv.job_title.name,
            "years_of_experience": cv.years_of_experience,
        },
        doc_id=f"cv-{cv.id}",  # stable upsert key
    )

class Command(BaseCommand):
    help = "Ingest CVs into a persistent Chroma collection"

    def add_arguments(self, parser):
        parser.add_argument("--collection", type=str, default="cvs")
        parser.add_argument("--rebuild", action="store_true")

    def handle(self, *args, **opts):
        # LlamaIndex minimal config: OpenAI embeddings only
        Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
        Settings.node_parser = SentenceSplitter(chunk_size=800, chunk_overlap=100)

        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        if opts["rebuild"]:
            try:
                client.delete_collection(opts["collection"])
            except Exception:
                pass

        collection = client.get_or_create_collection(opts["collection"])
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage = StorageContext.from_defaults(vector_store=vector_store)

        qs = CV.objects.select_related("job_title").all()
        docs = [cv_to_document(cv) for cv in qs]

        if not docs:
            self.stdout.write(self.style.WARNING("No CVs found."))
            return

        VectorStoreIndex.from_documents(docs, storage_context=storage, show_progress=True)
        self.stdout.write(self.style.SUCCESS(f"✅ Ingested {len(docs)} CVs into '{opts['collection']}'"))
