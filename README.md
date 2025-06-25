# **CoW Interface**

This repository is dedicated to the developement of the Intelligent conversion tool from tabular to linked data. 

## **Project Description**

The tool integrates Csv on the Web (CoW) as well as a vocabulary recommender for ranking vocabularies and instances. It is offers user the ability to select instances based on table context.

Original CoW tool repository: https://github.com/CLARIAH/COW

## **Instalation**

Below is the installation guide for the tool. It works on any operating system and should take around 2 minutes to install. As the last step there is a link with a sample dataset used for evaluation. Please download it as well.

### 1. Create Environment

**Windows:**
```bash
python -m venv cowEnv
```

**macOS/Linux**
```bash
python -m venv cowEnv
```
### 2. Activate the environment

**Windows**
```bash
cowEnv\Scripts\activate
```

**macOS/Linux**
```bash
source cowEnv/bin/activate
```

### 2. Navigate to the environment
```bash
cd cowEnv
```
### 3. Clone the Repository
```bash
git clone https://github.com/MateuszKielan/BachelorThesis_CoW_Interface.git
```

### 4. Navigate to the Project Folder
```bash
cd BachelorThesis_CoW_Interface
```

### 5. Install the tool with pip

**Windows**
```bash
pip install .
```

**macOS/Linux**
```bash
../bin/pip install .
```

### 6. Run the Tool 

**Windows**
```bash
scow
```

**macOS/Linux**
```bash
../bin/python ../bin/scow
```

If the scow command does not work, you can alternatively run:
```bash
python Interface/main.py
```

### 7. Download a sample dataset
You can access the link below and download a dataset "example.csv":
https://drive.google.com/drive/folders/16y2IHep4GmYxn7ptYYzi-Iz_aPY3HJmg


