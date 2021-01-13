from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

from spacy.lang.en import English
#import en_core_web_sm

import gner # class for recognising chronological entities.

app = FastAPI()
templates = Jinja2Templates(directory="./templates")


class Data(BaseModel):
    text: str


@app.get("/about")
def about(request: Request):

    context = {
        'request': request,
    }

    return templates.TemplateResponse("about.html", context)


@app.get("/chrono")
async def chrono(request: Request, text: str):
    print(text)
    pipe, tokens = get_chronos(text)

    # print(tokens)
    # return {"pipe": pipe, "details": tokens}
    context = {
        'request': request,
        'pipe': pipe,
        'result': tokens,
    }

    return templates.TemplateResponse("index.html", context)


@app.get("/api/")
async def api(text: str):
    pipe, tokens = get_chronos(text)
    return {'pipe': pipe, 'chronos': tokens}


@app.get("/")
def main(request: Request):

    q = ''

    context = {
        'request': request,
    }

    return templates.TemplateResponse("index.html", context)

def get_chronos(text):
    # nlp = en_core_web_sm.load(disable=['ner'])
    nlp = English()
    chronos = gner.ChronologyComponent(nlp)  # initialise component
    nlp.add_pipe(chronos) # add it to the pipeline
    doc = nlp(text.title())

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

    print(tokens)
    return pipe, tokens
