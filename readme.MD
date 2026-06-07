# starting docker ( llm service backend database ) 
cd to shiv_ai folder
docker-compose up -d #start
docker-compose down #close
start the vision audio and speaker sevice

# Adding new local llm
docker exec -it ollama bash #inside a container
ollama list
ollama pull qwen3:1.7b

# pushing code to my branch
git branch
git status
git add .
git commit -m "...."
git push -u origin shiv_claude_vibhesh
# restore 
git restore . 

# getting code from master branch
git checkout master
git pull origin main
git checkout shiv_claude_vibhesh
git merge master

# Vision service 
# search 
Change mode at start (to INVENTORY)
Change Camera    (uncomment esp32 link)
 
# To run all services repeat this process forr audio vision and speaker 
cd C:\Users\vibhe\OneDrive\Desktop\Shiv_ai\vision_service\
venv\Scripts\activate # activating the virtual envirnment 
python -m app.main
deactivate (close the venv)