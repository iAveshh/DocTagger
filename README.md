# DocTagger

## Overview

DocTagger is a Python-based application designed for extracting and tagging data from PDF documents. The application utilizes `PyMuPDF` (fitz) for PDF processing, `tkinter` for the graphical user interface, and `ttkbootstrap` for modern UI components and `SpaCy` for Automated labeling. It allows users to upload PDFs, extract text and metadata, and apply custom tags to the extracted data.

## Features

- **PDF Upload**: Select and upload PDF files through a user-friendly interface.
- **Data Extraction**: Extract text and metadata from PDF documents.
- **Tagging**: Apply custom tags to the extracted data.
- **Data Validation**: Validate the extracted and tagged data.
- **Reset Functionality**: Clear all previous data and start afresh with a new PDF upload.

## Installation

### Prerequisites

- Python 3.x
- pip (Python package installer)

### Install Dependencies

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pdf-tagger.git
   cd pdf-tagger
