from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

def make_qa(vs: FAISS, k:int, prompt, model:str):
    retriever = vs.as_retriever(search_kwargs={"k":k})
    llm = ChatOpenAI(model=model)
    qa = RetrievalQA.from_chain_type(
        llm=llm, retriever=retriever, chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}, return_source_documents=True
    )
    return qa
