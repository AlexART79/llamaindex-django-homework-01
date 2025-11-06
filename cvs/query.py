from django.conf import settings
import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.tools import QueryEngineTool, FunctionTool
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.tools.tavily_research import TavilyToolSpec
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.core.workflow import Context
from llama_index.core.agent.workflow import ReActAgent

def _index(collection: str = "cvs") -> VectorStoreIndex:
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    col = client.get_or_create_collection(collection)
    vs = ChromaVectorStore(chroma_collection=col)
    return VectorStoreIndex.from_vector_store(vs)

def search_cvs(question: str, top_k: int = 5):

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

def agent_runner(prompt: str):

    llm = OpenAI(
        model="gpt-4o",
        max_retries=6,
        timeout=120.0,
        # api_key=GEP_API_KEY,
        # api_base=GEP_API_URL,
    )

    # for some reason custom RAG tool works a lot better than built-in query engine tool,
    # based on the same ChromaDB index and query engine...
    # TODO: figure out why?
    #
    # index = _index("cvs")
    # retriever = index.as_retriever(similarity_top_k=5)
    #
    # query_engine = RetrieverQueryEngine.from_args(
    #     retriever=retriever,
    #     llm=llm,
    # )
    #
    # rag_tool = QueryEngineTool.from_defaults(
    #     query_engine=query_engine,
    #     name="rag_tool",
    #     description="Use this tool to answer questions about candidates resumes dataset"
    # )

    rag_tool = FunctionTool.from_defaults(
        fn=search_cvs,
        name="search_cvs",
        description="Use this tool when you need to query CVs DB"
    )

    import os
    TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]

    web_tools = TavilyToolSpec(api_key=TAVILY_API_KEY).to_tool_list()

    def current_date() -> str:
        """
        Return the current date in YYYY-MM-DD format.
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

    current_date_tool = FunctionTool.from_defaults(
        fn=current_date,
        name="current_date",
        description="Use this tool when you need to know current date"
    )

    tools = [*web_tools, rag_tool, current_date_tool]
    tools_info = "\n\n".join([
        f"{t.metadata.name} - {t.metadata.description}" for t in tools
    ])

    agent = ReActAgent(
        llm=llm,
        tools=tools,
        system_prompt=f"""
            You are a helpful assistant that can answer user's questions about:
            - candidates dataset (resumes) using the RAG tool
            - general knowledge questions, using the web to find up-to-date information
            Use chain of thought reasoning to solve complex tasks.
            Use tools to acquire required information.
            You have access to the following tools:
            ----
            {tools_info}
            ----
            DO NOT make up answers! If you don't know the answer, just say you don't know.
        """,
    )
    ctx = Context(agent)

    combined_prompt = f"""
        Classify the user query (it can be either general discussion topic or query about CVs DB). 
        Do not include classification result in the final answer!
        Based on classification results
        1) If it's general discussion topic - response should consists of HTML formatted data with links to the sources:
            <div> 
                response text 
                <div>Sources:</div>
                <ul>
                    <li><a href="http://...">Link text</a></li>
                    ...
                </ul>
            </div>
        2) If it's topic about CVs - retrieve relevant information from DB, including CV ID 
           Format response in valid HTML code with paragraphs, lists etc.
           If response includes candidate's names - you should format them as HTML links to the particular CV like this:
           
           <a href="/cvs/CV_ID/summary/">Candidate Name</a>           
           
           ATTENTION!!! In order link to work "CV_ID" should be replaced with actual CV ID from DB! 
           Do not makeup CV ID!

        DO NOT include ```html and ``` at the beginning and the end of HTML response!

        User query:
        {prompt}
    """

    handler = agent.run(combined_prompt, ctx=ctx)

    return handler