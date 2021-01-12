from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

from spacy.lang.en import English
#import en_core_web_sm

import gner # class for recognising chronological entities.

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


class Data(BaseModel):
    text: str


@app.get("/chrono/{text}")
def find_chronos(text: str):
    # nlp = en_core_web_sm.load(disable=['ner'])
    nlp = English()
    chronos = gner.ChronologyComponent(nlp)  # initialise component
    nlp.add_pipe(chronos) # add it to the pipeline
    doc = nlp(text.title())
    print(doc.text.title())

    pipe = nlp.pipe_names  # pipeline contains component name
    tokens = []
    for token in doc:
        if token._.is_chrono:
            tokens.append({
                'interval': token.text,
                'start_date': token._.start,
                'start_uncert': token._.start_uncert,
                'end_date': token._.end,
                'end_uncert': token._.end_uncert,
                'rank': token._.rank,
                'part_of': token._.part_of,
                'source': token._.source,
                })  # chronology data

    # print(tokens)
    return {"pipe": pipe, "details": tokens}


@app.get("/", response_class=HTMLResponse)
def read_item(request: Request):
    with open('templates/index.html') as f:
        print(f.readlines())
    return templates.TemplateResponse("index.html", {"request": request})
