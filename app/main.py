from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import items

app = FastAPI()

origins = [
    'http://localhost',
    'https://shopify-backend-developer-intern-challenge-e17dv1pnc-leon-li1.vercel.app'
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(items.router)