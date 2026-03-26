from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
from loguru import logger
from pathlib import Path
from json2graph import generate_save_graph
import time

load_dotenv() 


def build_graph():

    class GenerateOntologyState(TypedDict):
        report: str
        report_num : int
        use_case_questions: list
        next_use_case_num: int

    """llm_non_thinking = ChatOllama(
    model="gpt-oss:120b",
    base_url="https://core-llmtest.med.uni-muenchen.de/ollama",
    temperature=0.3, 
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {os.environ['OLLAMA_TOKEN']}"
            }
        }
    )"""

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

    
    def extend_ontology(state: GenerateOntologyState):
        
        start_report = time.time()

        
        for i in range((state["next_use_case_num"]-1),len(state["use_case_questions"])):

            if state["report_num"]==1 and i == 0:
                existing_ontology=[] 
                
            elif state["report_num"]!=1 and i==0:
                

                def get_version_number(path):
                    # Extracts the number from filenames like ontology_v_5.txt
                    return int(path.stem.split("_")[-1])

                report_dir = Path("ontologies") / f"report_{state['report_num']-1}"
                ontology_files = list(report_dir.glob("ontology_v_*.txt"))

                if ontology_files:
                    latest_file = max(ontology_files, key=get_version_number)

                    with latest_file.open("r", encoding="utf-8") as f:
                        existing_ontology = f.read()
            

            else:

                with open(f"ontologies/report_{state['report_num']}/ontology_v_{i}.txt", "r", encoding="utf-8") as f:
                    existing_ontology = f.read()


            with open("prompts/extend_ontology1.txt", "r", encoding="utf-8") as f:
                prompt1 = f.read()
            with open("prompts/extend_ontology2.txt", "r", encoding="utf-8") as f:
                prompt2 = f.read()

            prompt = [
            SystemMessage(content=prompt1),
            HumanMessage(content=prompt2.format(existing_ontology=existing_ontology, question=questions[i]))
            ]
            
            start = time.time()
            logger.debug(f"Generating ontology for use case question {i+1}/{len(state['use_case_questions'])}...")
        
            response = llm.invoke(prompt)
            end = time.time()
            folder_path3 = Path(f"ontologies/report_{state['report_num']}")
            folder_path3.mkdir(parents=True, exist_ok=True)
            elapsed = end - start
            logger.debug(
                f"Generated ontology for use case question {i+1}/{len(state['use_case_questions'])} "
                f"in {elapsed:.2f} seconds")
            
            with open(f"ontologies/report_{state['report_num']}/ontology_v_{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(response.content)
            
            
    
            folder_path4 = Path(f"thinking_traces/ontologies/report_{state['report_num']}")
            folder_path4.mkdir(parents=True, exist_ok=True)

            with open(f"thinking_traces/ontologies/report_{state['report_num']}/ontology_v_{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(response.additional_kwargs.get("reasoning_content"))
            
            
            folder_path5 = Path(f"ontology_graphs/report_{state['report_num']}")
            folder_path5.mkdir(parents=True, exist_ok=True)

            generate_save_graph(f"ontologies/report_{state['report_num']}/ontology_v_{i+1}.txt", f"ontology_graphs/report_{state['report_num']}/ontology_graph_v_{i+1}.html")
        
        
        end_report = time.time()
        elapsed_report = end_report - start_report
        
        logger.debug(
            f"Report {state['report_num']} processed"
            f" in {elapsed_report:.2f} seconds")


    # Build the Graph
    workflow = StateGraph(GenerateOntologyState)
    
    workflow.add_node("extend_ontology", extend_ontology)

    workflow.add_edge(START, "extend_ontology")
    workflow.add_edge("extend_ontology", END)

    
    return(workflow.compile())

graph=build_graph()

from pathlib import Path

input_dir = Path("reports_en")
files = [str(f.name) for f in input_dir.glob("*.md")]

cr=10
nu=6
logger.debug(f"Report number = {cr}")
file_path="reports_en/"+files[cr-1]

with open(file_path, "r", encoding="utf-8") as f:
    report = f.read()

use_case_file_path=f"use_case_questions/report_{cr}.txt"

import json

with open(use_case_file_path, "r", encoding="utf-8") as f:
    questions = json.loads(f.read())[0]["use_case_questions"]

graph.invoke({"report":report, "report_num":cr, "next_use_case_num": nu, "use_case_questions":questions})

logger.debug(f"Report number {cr} Completed")
    

"""
with open("graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())"""