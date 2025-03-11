# Overview

This project detects propaganda and persuasion tactics observed in the web page that you visit

It consists of two parts :
- Front-end : a chrome extension 
- Back-end : Flask based API

The flask based API takes in the url of the webpage and extracts the contents , performing a keyword - based analysis  with the help of Gemini Flash 2.0 model

The flask API returns a response that is rendered appropriately in the chrome extension

# Installation

## Extension 

Prerequisites : Chrome browser

1. Clone the repository
2. Go to chrome://extensions
3. Toggle developer mode
4. Choose `Load unpacked` option and select the `extension/` directory inside this repository


## Back-end API

1. Clone the repository
2. run `pip install -r requirements.txt` 
3. run `python main.py`
4. The API can be accessed at `http://localhost:5000`
      



