import uvicorn
import sys
import os

if __name__ == "__main__":
    print("====================================================")
    print("      Bank Complaint Intelligence System Launcher    ")
    print("====================================================")
    print("Port: 8000")
    print("Host: http://localhost:8000")
    print("Endpoints:")
    print("  - Submit Portal   : http://localhost:8000/submit")
    print("  - Dashboard       : http://localhost:8000/dashboard")
    print("====================================================")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
