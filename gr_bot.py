import gradio as gr
import asyncio
import re

from RAG import rag_retrieval_qa
from lambda_stream.producer import publish_chat_event
from lambda_batch.producer import run_produce_async

answer_format = """Answer:
{}
              
URL:
{}

EVIDENCE:
{}
"""
temp_history = []


def get_answer(query, history, http, depth):
    output = ""
    print(history)
    print("HTTP: ", http)
    try:
        urls = re.findall(r'\bhttps?://[^\s<>"]+|www\.[^\s<>"]+\b', http)
        asyncio.run(run_produce_async(urls, int(depth)))
        output = "Crawled from {}\n".format("\n".join(urls))
    except:
        pass
    
    if len(query) != 0:
        answer, retrieved_chunks, retrieved_url = rag_retrieval_qa(query, history)
        publish_chat_event(query, answer)
        
        output += answer_format.format(answer, retrieved_url, retrieved_chunks)
        temp_history = history
    else:
        output += "Please ask something!"
    return  output

with gr.Blocks() as demo:
    http = gr.Textbox(label="url to crawl")
    depth = gr.Textbox("1", label="depth")

    gr.ChatInterface(
        get_answer, additional_inputs=[http, depth], type="messages"
    )

demo.launch()