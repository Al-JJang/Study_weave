"""python -m graph.supervisor 또는 python run_graph.py"""

from graph.supervisor import run_pipeline

if __name__ == "__main__":
    result = run_pipeline()
    print("route :", result.get("route"))
    print("status:", result.get("status"))
    print("chunks:", len(result.get("parsed_chunks", [])))
    print("hits  :", len(result.get("retrieved_chunks", [])))
    print("quiz  :", len(result.get("quiz_items", [])))
    print("passed:", getattr(result.get("verification"), "passed", None))
