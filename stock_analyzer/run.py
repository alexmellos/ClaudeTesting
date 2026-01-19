#!/usr/bin/env python3
"""Run the stock analyzer application."""
import subprocess
import sys
import os

def main():
    # Change to the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("=" * 50)
    print("  S&P 500 Stock Analyzer")
    print("=" * 50)
    print("\nChoose how to run the application:")
    print("1. Web Dashboard (Streamlit) - Recommended")
    print("2. API Server (FastAPI)")
    print("3. Both (Dashboard + API)")
    print()

    choice = input("Enter your choice (1/2/3) [default: 1]: ").strip() or "1"

    if choice == "1":
        print("\nStarting Streamlit dashboard...")
        print("Open http://localhost:8501 in your browser\n")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])

    elif choice == "2":
        print("\nStarting FastAPI server...")
        print("API available at http://localhost:8000")
        print("API docs at http://localhost:8000/docs\n")
        subprocess.run([sys.executable, "-m", "uvicorn", "api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

    elif choice == "3":
        import multiprocessing

        def run_api():
            subprocess.run([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"])

        def run_dashboard():
            subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])

        print("\nStarting both services...")
        print("API: http://localhost:8000 (docs at /docs)")
        print("Dashboard: http://localhost:8501\n")

        api_process = multiprocessing.Process(target=run_api)
        dashboard_process = multiprocessing.Process(target=run_dashboard)

        api_process.start()
        dashboard_process.start()

        try:
            api_process.join()
            dashboard_process.join()
        except KeyboardInterrupt:
            api_process.terminate()
            dashboard_process.terminate()

    else:
        print("Invalid choice. Please run again.")

if __name__ == "__main__":
    main()
