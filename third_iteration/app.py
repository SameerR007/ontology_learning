from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
from loguru import logger

load_dotenv() 


def build_graph():

    class GenerateOntologyState(TypedDict):
        report: str
        report_num : int
        thinking_trace: str
        guidelines: str
        generated_ontology: str
        updated_guidelines: str

    llm = ChatOllama(
    model="gpt-oss:120b",
    base_url="https://core-llmtest.med.uni-muenchen.de/ollama",
    # Enable thinking/reasoning
    # For gpt-oss models, you can use "low", "medium", or "high"
    reasoning="medium",
    temperature=0.3, 
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {os.environ['OLLAMA_TOKEN']}"
            }
        }
    )

    def is_first_report(state: GenerateOntologyState):


        if state["report_num"]==1:
            logger.debug(f"This is report number {state['report_num']}")
            return "generate_first_ontology"
        else:
            logger.debug(f"This is report number {state['report_num']}")
            return "read_ontology_creation_guidelines"

    def read_ontology_creation_guidelines(state: GenerateOntologyState):
        
        with open(f"guidelines/ontology_guidelines_v_{(state['report_num']-1)}.md", "r", encoding="utf-8") as f:
            guidelines = f.read()
        
        logger.debug(f"Ontology guidelines read")

        return {"guidelines": guidelines}

    def generate_first_ontology(state: GenerateOntologyState):
        
        report = state["report"]

        with open("prompts/generate_first_ontology_prompt.txt", "r", encoding="utf-8") as f:
            prompt = f.read()

        prompt = [
            SystemMessage(content=prompt),
            HumanMessage(content=report)
        ]
        
        logger.debug(f"Generating first ontology...")

        response = llm.invoke(prompt)
        
        with open("ontologies/ontology_v_1.txt", "w", encoding="utf-8") as f:
            f.write(response.content)

        with open("thinking_traces/thinking_trace_ontology_v_1.txt", "w", encoding="utf-8") as f:
            f.write(response.additional_kwargs.get("reasoning_content"))

        
        logger.debug(f"First ontology generated")
        logger.debug(f"ontology_v_{state['report_num']} saved")
        logger.debug(f"thinking_trace_ontology_v_{state['report_num']} saved")

        return {"thinking_trace":response.additional_kwargs.get("reasoning_content"), "generated_ontology": response.content}

    def extend_ontology(state: GenerateOntologyState):
        
        with open("prompts/extend_ontology_prompt.txt", "r", encoding="utf-8") as f:
            prompt = f.read()

        with open(f"ontologies/ontology_v_{(state['report_num']-1)}.txt", "r", encoding="utf-8") as f:
            existing_ontology = f.read()

        logger.debug(f"Generating ontology...")

        response = llm.invoke(prompt.format(report=state["report"], existing_ontology=existing_ontology, guidelines=state["guidelines"]))
        
        with open(f"ontologies/ontology_v_{state['report_num']}.txt", "w", encoding="utf-8") as f:
            f.write(response.content)

        with open(f"thinking_traces/thinking_trace_ontology_v_{state['report_num']}.txt", "w", encoding="utf-8") as f:
            f.write(response.additional_kwargs.get("reasoning_content"))
        
        logger.debug(f"Ontology Generated")
        logger.debug(f"ontology_v_{state['report_num']} saved")
        logger.debug(f"thinking_trace_ontology_v_{state['report_num']} saved")

        return {"thinking_trace":response.additional_kwargs.get("reasoning_content"), "generated_ontology": response.content}

    def create_first_ontology_guidelines(state: GenerateOntologyState):

        with open("prompts/create_first_ontology_guidelines_prompt.txt", "r", encoding="utf-8") as f:
            prompt = f.read()

        logger.debug(f"Generating first ontology guidelines...")

        response = llm.invoke(prompt.format(report=state["report"], thinking_trace=state["thinking_trace"], generated_ontology=state["generated_ontology"]))
        
        logger.debug(f"First ontology guidelines generated")

        return {"updated_guidelines": response.content}
    
    def create_subsequent_ontology_guidelines(state: GenerateOntologyState):

        with open("prompts/create_subsequent_ontology_guidelines_prompt.txt", "r", encoding="utf-8") as f:
            prompt = f.read()

        with open(f"ontologies/ontology_v_{(state['report_num']-1)}.txt", "r", encoding="utf-8") as f:
            previous_ontology = f.read()

        logger.debug("Updating ontology guidelines...")

        response = llm.invoke(prompt.format(guidelines=state["guidelines"], report=state["report"], thinking_trace=state["thinking_trace"], previous_ontology=previous_ontology, updated_ontology=state["generated_ontology"]))
        
        logger.debug("Ontology guidelines updated")

        return {"updated_guidelines": response.content}


    def save_ontology_guidelines(state: GenerateOntologyState):
        with open(f"guidelines/ontology_guidelines_v_{state['report_num']}.md", "w", encoding="utf-8") as f:
            f.write(state["updated_guidelines"])

        logger.debug(f"Ontology guidelines saved")


    # Build the Graph
    workflow = StateGraph(GenerateOntologyState)
    
    workflow.add_node("generate_first_ontology", generate_first_ontology)
    workflow.add_node("create_first_ontology_guidelines", create_first_ontology_guidelines)
    workflow.add_node("read_ontology_creation_guidelines", read_ontology_creation_guidelines)
    workflow.add_node("extend_ontology", extend_ontology)
    workflow.add_node("create_subsequent_ontology_guidelines", create_subsequent_ontology_guidelines)
    workflow.add_node("save_ontology_guidelines", save_ontology_guidelines)
    
    workflow.add_conditional_edges(START, is_first_report, ["generate_first_ontology", "read_ontology_creation_guidelines"])

    workflow.add_edge("generate_first_ontology", "create_first_ontology_guidelines")
    workflow.add_edge("create_first_ontology_guidelines", "save_ontology_guidelines")
    workflow.add_edge("save_ontology_guidelines", END)

    workflow.add_edge("read_ontology_creation_guidelines", "extend_ontology")
    workflow.add_edge("extend_ontology", "create_subsequent_ontology_guidelines")
    workflow.add_edge("create_subsequent_ontology_guidelines", "save_ontology_guidelines" )

    return(workflow.compile())

graph=build_graph()

from pathlib import Path
from json2graph import generate_save_graph

input_dir = Path("reports_en")
files = [str(f.name) for f in input_dir.glob("*.md")]

for i in range(30, 60):
    #print(f"Report number = {i+1}")
    file_path="reports_en/"+files[i]
    
    with open(file_path, "r", encoding="utf-8") as f:
        report = f.read()
    
    graph.invoke({"report":report, "report_num":(i+1)})

    logger.debug(f"Report number {i+1} Completed")

    #generate_save_graph(f"ontologies/ontology_v_{i+1}.txt", f"ontology_graphs/ontology_graph_v_{i+1}.html")