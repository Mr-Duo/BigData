# RAG Chatbot from URLs using Lambda Architecture
This is a Project in Big Data course of SoICT - HUST

## Our team
| Name              | Student ID | Mail                           |
|-------------------|------------|--------------------------------|
| Cao Minh Tue      | 20210908   | tue.cm210908@sis.hust.edu.vn   | 
| Nghiem Minh Hieu  | 20210333   | hieu.nm210333@sis.hust.edu.vn  |
| Nguyen Dang Duong | 20215336   | duong.nd215336@sis.hust.edu.vn |  

## Requirements
Python >= 3.11
Docker >= 27.2.0

## Usage
To use this project, follow these steps:

- Clone this repository.
    ```
    git clone https://github.com/Mr-Duo/BigData
    ```
- Setup virtual evironment and download dependencies.
    ```
    python -m venv .venv
    .venv\Scripts\activate
    pip install requirements.txt
    ```    
- Deploy docker containers.
    ```
    docker compose up -d
    ```
- Start script
    ```
    start.bat
    ```  
    The commmand above will start the chatbot.    
    
- Visualizer:
    - Chatbot: localhost:7860
    - HDFS namenode: localhost:9870
    - Cassandra-web: localhost:3000