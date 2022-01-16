import os
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from prisma import Client
from pydantic import BaseModel
from uuid import uuid4

client = Client()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class CreateInput(BaseModel):
    sku: str
    name: str
    description: str
    color: Optional[str]
    size: Optional[str]
    count: int

class UpdateInput(BaseModel):
    name: str
    description: str
    color: Optional[str]
    size: Optional[str]
    count: int

'''
CRUD inventory tracking web application
- Create inventory items
- Edit Them
- Delete Them
- View a list of them
'''

@app.on_event('startup')
async def startup_event():
    await client.connect()

@app.on_event('shutdown')
async def shutdown_event():
    await client.disconnect()

BASE_URL = '/api/item'

@app.post(BASE_URL)
async def create(item: CreateInput):
    try:
        assert item.sku != '', 'SKU cannot be empty'
        assert item.sku not in ('list', 'export'), f'SKU cannot be the reserved word "{item.sku}"'
        assert item.name != '', 'Name cannot be empty'
        assert item.description != '', 'Description cannot be empty'
        assert item.count > 0, 'There must be at least one of this item'
    except AssertionError as e:
      raise HTTPException(status_code=400, detail=str(e))

    existing_item = await client.item.find_unique(where={ 'sku': item.sku })
    if existing_item:
        raise HTTPException(status_code=400, detail=f'Item with SKU {item.sku} already exists')

    return await client.item.create(data={
        'sku': item.sku,
        'name': item.name,
        'description': item.description,
        'color': item.color or None,
        'size': item.size or None,
        'count': item.count
    })

@app.put(BASE_URL+'/{sku}')
async def edit(sku: str, item: UpdateInput):
    try:
        assert item.name != '', 'Name cannot be empty'
        assert item.description != '', 'Description cannot be empty'
        assert item.count > 0, 'There must be at least one of this item'
    except AssertionError as e:
      raise HTTPException(status_code=400, detail=str(e))

    return await client.item.update(
        where={ 'sku': sku }, 
        data={
            'name': item.name,
            'description': item.description,
            'color': item.color or None,
            'size': item.size or None,
            'count': item.count
        }
    )

@app.delete(BASE_URL+'/{sku}')
async def delete(sku: str):
    return await client.item.delete(where={ 'sku': sku })

@app.get(BASE_URL+'/list')
async def getall():
    return await client.item.find_many()

@app.get(BASE_URL+'/export')
async def export(background_tasks: BackgroundTasks):
    items = await client.item.find_many()
    csvContent = ['sku,name,description,size,color,count']
    for item in items:
        csvContent.append(f'"{item.sku}","{item.name}","{item.description}","{item.size}","{item.color}","{item.count}"')
    filename = f'inventory-{uuid4()}.csv'
    with open(filename, 'w') as f:
        f.write('\n'.join(csvContent))
    background_tasks.add_task(lambda f: os.remove(f), filename) # delete the file afterwards
    return FileResponse(filename, media_type='text/csv')

@app.get(BASE_URL+'/{sku}')
async def getone(sku: str):
    return await client.item.find_unique(where={ 'sku': sku })
