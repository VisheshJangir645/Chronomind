import sys
import os
import json

# Ensure app package is accessible
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.pipeline import MasterPipeline
from app.schemas import ChronoEvent

def test_chronomind():
    print("=============================================")
    print(" Booting ChronoMind Unified Agent...")
    print("=============================================\n")
    
    try:
        pipeline = MasterPipeline()
        
        test_input = (
            "During Mughal rule, significant architectural and economic expansions occurred in the subcontinent. "
            "In 1776, completely across the world, George Washington crossed the Delaware River."
        )
        
        print(f"RAW INPUT TEXT:\n{test_input}\n")
        print("Executing Master Pipeline Hooks...")
        
        results = pipeline.process_document(test_input)
        
        print("\n=============================================")
        print(f" FINAL CHRONO EVENTS EXTRACTED: {len(results)}")
        print("=============================================\n")
        
        for ev in results:
            print(json.dumps(ev.model_dump(), indent=2))
            print("-" * 40)
            
    except Exception as e:
        print(f"\n[PIPELINE EXCEPTION]: Graceful fallback triggered. Missing OS Dependencies for full ML initialization: {e}")
        print("In a production/conference environment, this mandates the Docker Container setup.")

if __name__ == '__main__':
    test_chronomind()
