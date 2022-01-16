import os
from uuid import uuid4
from typing import Optional
from prisma import Client
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

client = Client()
router = APIRouter(prefix='/api/item', tags=['items'])

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

@router.on_event('startup')
async def startup_event():
    await client.connect()

@router.on_event('shutdown')
async def shutdown_event():
    await client.disconnect()

@router.post('/')
async def create(item: CreateInput):
    try:
        assert item.sku != '', 'SKU cannot be empty'
        assert item.sku not in ('list', 'export'), f'SKU cannot be the reserved word "{item.sku}"'
        assert item.name != '', 'Name cannot be empty'
        assert item.description != '', 'Description cannot be empty'
        assert item.count > 0, 'There must be at least one of this item'
    except AssertionError as e:
      return PlainTextResponse(f'ERROR: {str(e)}', status_code=400)

    existing_item = await client.item.find_unique(where={ 'sku': item.sku })
    if existing_item:
        return PlainTextResponse(f'ERROR: Item with SKU {item.sku} already exists', status_code=400)

    return await client.item.create(data={
        'sku': item.sku,
        'name': item.name,
        'description': item.description,
        'color': item.color or None,
        'size': item.size or None,
        'count': item.count
    })

@router.put('/{sku}')
async def edit(sku: str, item: UpdateInput):
    try:
        assert item.name != '', 'Name cannot be empty'
        assert item.description != '', 'Description cannot be empty'
        assert item.count > 0, 'There must be at least one of this item'
    except AssertionError as e:
      return PlainTextResponse(f'ERROR: {str(e)}', status_code=400)

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

@router.delete('/{sku}')
async def delete(sku: str):
    return await client.item.delete(where={ 'sku': sku })

@router.get('/list')
async def getall():
    return await client.item.find_many()

@router.get('/export')
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

@router.get('/{sku}')
async def getone(sku: str):
    return await client.item.find_unique(where={ 'sku': sku })