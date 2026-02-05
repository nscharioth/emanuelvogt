# How to Share the Digital Archive

To let another person run this archive on their local machine, follow these steps:

## 1. Files to Copy
You need to transfer the following folders and files:
- `app/` (The web application)
- `data/` (Crucially `archive.db` which contains all the metadata)
- `archive/` (The 28GB folder containing the actual PDFs)
- `requirements.txt`
- `run_viewer.sh`

## 2. Setup on the Other Machine

### Step A: Prerequisites
Ensure **Python 3.9+** is installed on the machine.

### Step B: Create a Virtual Environment
Open the terminal (or Command Prompt on Windows) in the project folder and run:

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**On Windows:**
```batch
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step C: Launch

**On macOS / Linux:**
```bash
./run_viewer.sh
```

**On Windows:**
Double-click `run_viewer.bat` or run:
```batch
run_viewer.bat
```
The archive will then be available at `http://localhost:8000`.

---

## 💡 Important Considerations

### Large File Transfer
Since the `archive/` folder is ~28GB, the best way to share it is via:
- A physical **external SSD/Thumb drive**.
- A private cloud link (Dropbox/Google Drive) if they have the space.

### Paths
The application is designed to be **portable**. As long as the `archive` folder and the `app` folder stay in the same parent directory, the viewer will find the PDFs regardless of where they are on the computer.

### Git (Optional)
If the other person uses GitHub, you can push the code (everything *except* the 28GB `archive` and the `archive.db`) to a repository. They can then clone the code and you only have to transfer the `archive/` and `data/archive.db` files manually.
