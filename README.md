# **CoW Interface**

This repository is dedicated to the developement of the Intelligent conversion tool from tabular to linked data. 

## **Project Description**

The tool integrates Csv on the Web (CoW) as well as a vocabulary recommender for ranking vocabularies and instances. It is offers user the ability to select instances based on table context.

Original CoW tool repository: https://github.com/CLARIAH/COW

## **Instalation**

### 1. Create and run Virtual Environment

**Windows:**
```bash
python -m venv cowEnv
cowEnv\Scripts\activate
```

**macOS/Linux**
```bash
python3 -m venv cowEnv
source cowEnv/bin/activate
```

### 2. Clone the Repository
```bash
git clone https://github.com/MateuszKielan/BachelorThesis_CoW_Interface.git
```

### 3. Navigate to the Project Folder
```bash
cd BachelorThesis_CoW_Interface
```

### 3. Install the tool with pip
```bash
pip install .
```

### 4. Run the Tool 
```bash
scow
```

If the scow command does not work, you can alternatively run:
```bash
python Interface/main.py
```
