from pydantic import BaseModel


class fileResponse(BaseModel):
    origin_name: str
    disk_name: str
    size: int
    url: str
