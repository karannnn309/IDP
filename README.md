# 🧠 Intelligent Document Processing (IDP) System

https://github.com/karannnn309/IDP/issues/1#issue-3127352567

An AI-powered web-based document verification system developed to validate user-submitted documents by extracting information using OCR/NLP techniques and comparing it against form input data. This project is designed to streamline and automate the document validation process for organizations.

---

## 🔍 Features

- 🔐 **User Authentication** – Signup and Login for applicants
- 📝 **Form Submission** – Collect user information (Personal, Academic, Work Experience)
- 📄 **Document Upload** – Accepts PDF documents (e.g., Aadhaar, Certificates, Scorecards)
- 🧠 **AI-powered Extraction** – Extracts structured and unstructured data using google cloud platform(OCR & NLP)
- ✅ **Verification Engine** – Compares extracted data against user inputs
- 📊 **Mismatch Detection & Visualization** – Highlights mismatches with percentage accuracy
- 📍 **Dashboard** – Track document verification status and results


---

## ⚙️ Tech Stack

- **Backend**: Django, Python
- **Frontend**: HTML, CSS, Bootstrap, Django Templates
- **Database**: SQLite 
- **Document Parsing**: Tesseract OCR, LayoutLM (optional), PyMuPDF, PDFMiner
- **Visualization**: Matplotlib / Plotly
- **Authentication**: Django Auth System

---
WEBSITE OUTPUT=https://github.com/karannnn309/IDP/issues/1#issue-3127352567


## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip
- Virtualenv (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/karannnn309/IDP.git
cd IDP

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows use: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run the server
python manage.py runserver
