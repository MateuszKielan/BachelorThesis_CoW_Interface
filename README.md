**CoW Interface**

This repository is dedicated to the developement of the Intelligent conversion tool from tabular to linked data. 

**Project Description**

The tool integrates Csv on the Web (CoW) as well as a vocabulary recommender for ranking vocabularies and instances. It is offers user the ability to select instances based on table context.

Original CoW tool repository: https://github.com/CLARIAH/COW

**Instalation**

Step 1: Create a Virtual Environment
Windows:

nginx
Copy
Edit
python -m venv cowEnv
cowEnv\Scripts\activate
macOS/Linux:

bash
Copy
Edit
python3 -m venv cowEnv
source cowEnv/bin/activate
Step 2: Clone the Repository
bash
Copy
Edit
git clone https://github.com/MateuszKielan/BachelorThesis_CoW_Interface.git
Step 3: Navigate to the Project Folder
bash
Copy
Edit
cd BachelorThesis_CoW_Interface
Step 4: Install the Tool with pip
nginx
Copy
Edit
pip install -e .
▶Step 5: Run the Tool via CLI
nginx
Copy
Edit
scow
If the scow command doesn’t work, you can launch the interface manually:

bash
Copy
Edit
python Interface/main.py

