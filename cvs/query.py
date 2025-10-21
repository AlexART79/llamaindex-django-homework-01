from django.conf import settings
import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

def _index(collection: str = "cvs") -> VectorStoreIndex:
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    col = client.get_or_create_collection(collection)
    vs = ChromaVectorStore(chroma_collection=col)
    return VectorStoreIndex.from_vector_store(vs)

def search_cvs(question: str, top_k: int | None = None):
    from llama_index.llms.openai import OpenAI

    llm = OpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    idx = _index("cvs")
    qe = idx.as_query_engine(
        llm=llm,
        similarity_top_k=top_k or settings.LLM_INDEX_SIM_TOP_K
    )
    resp = qe.query(question)

    matches = []
    for sn in resp.source_nodes:
        md = sn.node.metadata or {}
        matches.append({
            "score": float(sn.score or 0.0),
            "cv_id": md.get("cv_id"),
            "name": md.get("name"),
            "job_title": md.get("job_title"),
            "years_of_experience": md.get("years_of_experience"),
            "snippet": sn.node.get_text()[:400],
        })

    return {"answer": str(resp), "matches": matches}
