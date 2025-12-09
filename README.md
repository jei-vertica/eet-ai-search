```bash
sudo apt install python3-pip python3-venv
python3 -m venv venv
source venv/bin/active
pip install -r requirements.txt
pip install uvicorn gunicorn
export OPENROUTER_API_KEY=lars
gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
