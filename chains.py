from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import create_retriever_tool

from config import (
    OPENAI_MODEL_NAME,
    OPENAI_MODEL_TEMPERATURE,
)
from memory import get_session_history
from vectorstore import get_vectorstore
from prompts import contextualize_prompt, qa_prompt, agent_prompt
from weather_tool import get_weather
from agro_weather_tool import get_agro_weather
from commodity_prices_tool import get_commodity_price


def get_rag_chain():
    llm = ChatOpenAI(
        model=OPENAI_MODEL_NAME,
        temperature=OPENAI_MODEL_TEMPERATURE,
    )
    retriever = get_vectorstore().as_retriever()
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_prompt)
    question_answer_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=qa_prompt,
    )
    return create_retrieval_chain(history_aware_retriever, question_answer_chain)

def get_agent_chain():
    llm = ChatOpenAI(
        model=OPENAI_MODEL_NAME,
        temperature=OPENAI_MODEL_TEMPERATURE,
    )

    # Criar tool de retrieval para RAG
    retriever = get_vectorstore().as_retriever()
    retriever_tool = create_retriever_tool(
        retriever,
        "knowledge_base",
        "Busca informações na base de conhecimento. Use para perguntas sobre os documentos armazenados."
    )

    # Lista de tools disponíveis
    tools = [retriever_tool, get_weather, get_agro_weather, get_commodity_price]

    # Criar agente com tools
    agent = create_tool_calling_agent(llm, tools, agent_prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def get_conversational_rag_chain():
    # Usar agente ao invés de RAG simples
    agent_chain = get_agent_chain()
    return RunnableWithMessageHistory(
        runnable=agent_chain,
        get_session_history=get_session_history,
        input_messages_key='input',
        history_messages_key='chat_history',
        output_messages_key='output',
    )
