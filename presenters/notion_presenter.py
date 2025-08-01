from notion_client import Client
from config import NOTION_API_KEY, NOTION_DATABASE_ID
import math

notion = Client(auth=NOTION_API_KEY)

def chunk_items(items, chunk_size):
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]

def create_notion_page(title, summarized_data, chunk_size=10):
    chunks = list(chunk_items(summarized_data, chunk_size))
    
    for index, chunk in enumerate(chunks):
        page_title = title if len(chunks) == 1 else f"{title} - Part {index + 1}"

        children = []
        for item in chunk:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "text": [{"type": "text", "text": {"content": item['title']}}]
                }
            })
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "text": [{"type": "text", "text": {"content": item['summary']}}]
                }
            })
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "text": [{"type": "text", "text": {"content": f"Link: {item['link']}"}}]
                }
            })

        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": page_title}}]
                }
            },
            children=children
        )
