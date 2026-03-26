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
import json
from extend_ontology import update_ontology
load_dotenv() 
import csv

def build_graph():

    class GenerateOntologyState(TypedDict):
        report: str
        report_num : int
        use_case_questions: list
        question_gen_time: float
        ontology_gen_time: float

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

    def generate_use_case_questions(state: GenerateOntologyState):
        
        start=time.time()

        with open("prompts/use_case_questions_generation.txt", "r", encoding="utf-8") as f:
            prompt = f.read()
        
        report = state["report"]

        prompt = [
            SystemMessage(content=prompt),
            HumanMessage(content=report)
        ]

        logger.debug(f"Generating use case questions...")
        response = llm.invoke(prompt)
        
        folder_path = Path("use_case_questions")
        folder_path.mkdir(exist_ok=True)

        with open(f"use_case_questions/report_{state['report_num']}.txt", "w", encoding="utf-8") as f:
            f.write(response.content)


        folder_path2 = Path("thinking_traces/use_case_questions")
        folder_path2.mkdir(parents=True, exist_ok=True)

        with open(f"thinking_traces/use_case_questions/report_{state['report_num']}.txt", "w", encoding="utf-8") as f:
            f.write(response.additional_kwargs.get("reasoning_content"))

        logger.debug(f"Use case questions generated")
        
        end=time.time()

        return{"use_case_questions":json.loads(response.content)[0]["use_case_questions"], "question_gen_time": (end-start)}

    def extend_ontology(state: GenerateOntologyState):
        
        start_report = time.time()

        questions = state["use_case_questions"]
        
        # Initialize a list to hold the timing data for this specific report
        timing_data = []

        for i in range(len(questions)):

            if state["report_num"]==1 and i == 0:
                existing_ontology= '[{"Ontology": {"Labels": [], "RelationshipTypes": [], "SchemaMap": []}}]'
                
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
            
            folder_path4 = Path(f"ontologies_diffs/report_{state['report_num']}")
            folder_path4.mkdir(parents=True, exist_ok=True)

            elapsed = end - start
            logger.debug(
                f"Generated ontology for use case question {i+1}/{len(state['use_case_questions'])} "
                f"in {elapsed:.2f} seconds")
            
            timing_data.append([state['report_num'], f"{i+1}", f"{elapsed:.2f}"])
            
            with open(f"ontologies_diffs/report_{state['report_num']}/ontology_diffs_v_{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(response.content)
            
            
    
            folder_path5 = Path(f"thinking_traces/ontologies_diffs/report_{state['report_num']}")
            folder_path5.mkdir(parents=True, exist_ok=True)

            with open(f"thinking_traces/ontologies_diffs/report_{state['report_num']}/ontology_diffs_v_{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(response.additional_kwargs.get("reasoning_content"))
            
            folder_path3 = Path(f"ontologies/report_{state['report_num']}")
            folder_path3.mkdir(parents=True, exist_ok=True)

            update_ontology(existing_data=json.loads(existing_ontology), diff_data=json.loads(response.content), output_file_path=f"ontologies/report_{state['report_num']}/ontology_v_{i+1}.txt")
                
            
            folder_path6 = Path(f"ontology_graphs/report_{state['report_num']}")
            folder_path6.mkdir(parents=True, exist_ok=True)

            generate_save_graph(f"ontologies/report_{state['report_num']}/ontology_v_{i+1}.txt", f"ontology_graphs/report_{state['report_num']}/ontology_graph_v_{i+1}.html")
        
        
        end_report = time.time()
        
        elapsed_report = end_report - start_report
        
        csv_file = "CQ_execution_times.csv"
        file_exists = os.path.isfile(csv_file)
        
        with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write header if the file is being created for the first time
            if not file_exists:
                writer.writerow(["Report Number", "Question Number", "Time (Seconds)"])
            writer.writerows(timing_data)

        logger.debug(
            f"Report {state['report_num']} processed"
            f" in {elapsed_report:.2f} seconds")
        
        return {
            "ontology_gen_time": elapsed_report # Save to state
        }


    # Build the Graph
    workflow = StateGraph(GenerateOntologyState)
    
    workflow.add_node("generate_use_case_questions", generate_use_case_questions)
    workflow.add_node("extend_ontology", extend_ontology)

    workflow.add_edge(START, "generate_use_case_questions")
    workflow.add_edge("generate_use_case_questions", "extend_ontology")
    workflow.add_edge("extend_ontology", END)

    
    return(workflow.compile())

graph=build_graph()

from pathlib import Path

csv_file = "execution_times.csv"

file_exists = os.path.isfile(csv_file)
with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["Report num", "use case question gen time", "all ontology generation time", "total time"])

input_dir = Path("reports_en")
files = [str(f.name) for f in input_dir.glob("*.md")]

for i in range(10, 20):
    logger.debug(f"Report number = {i+1}")
    file_path="reports_en/"+files[i]
    
    with open(file_path, "r", encoding="utf-8") as f:
        report = f.read()
    
    final_state=graph.invoke({"report":report, "report_num":(i+1)})

    # Extract times from the state
    q_gen_time = final_state.get("question_gen_time", 0.0)
    o_gen_time = final_state.get("ontology_gen_time", 0.0)
    with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            i+1, 
            f"{q_gen_time:.2f}", 
            f"{o_gen_time:.2f}", 
            f"{(q_gen_time+o_gen_time):.2f}"
        ])

    logger.debug(f"Report number {i+1} Completed")
    

"""
with open("graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())"""