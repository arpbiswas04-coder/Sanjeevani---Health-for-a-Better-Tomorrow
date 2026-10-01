import asyncio
import httpx
from datetime import datetime,timezone
from pydantic import BaseModel,Field,ConfigDict
from app.core.config import settings


class CurrentWeather(BaseModel):
    model_config=ConfigDict(extra='ignore')
    time:datetime
    temperature_2m:float=Field(ge=-100,le=100)
    precipitation:float=Field(ge=0,le=10000)
    weather_code:int=Field(ge=0,le=99)


class WeatherResponse(BaseModel):
    current:CurrentWeather


async def fetch_weather(latitude,longitude,client=None):
    if settings.WEATHER_PROVIDER!='open-meteo':
        raise RuntimeError('WEATHER_PROVIDER_NOT_CONFIGURED')
    own=client is None
    client=client or httpx.AsyncClient(timeout=5,follow_redirects=False)
    try:
        for attempt in range(3):
            try:
                async with client.stream('GET','https://api.open-meteo.com/v1/forecast',params={
                    'latitude':latitude,'longitude':longitude,'current':'temperature_2m,precipitation,weather_code','timezone':'UTC'}) as response:
                    response.raise_for_status()
                    body=bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body)>1_000_000:
                            raise ValueError('Weather payload too large')
                result=WeatherResponse.model_validate_json(body).current
                # Requested timezone is UTC; this provider returns naive UTC strings.
                if result.time.tzinfo is None:
                    result.time=result.time.replace(tzinfo=timezone.utc)
                return {'source':'open-meteo','current':result.model_dump(mode='json')}
            except (httpx.TimeoutException,httpx.NetworkError,httpx.HTTPStatusError) as exc:
                if isinstance(exc,httpx.HTTPStatusError) and exc.response.status_code<500 and exc.response.status_code!=429:
                    raise
                if attempt==2:
                    raise
                await asyncio.sleep(0.1*2**attempt)
    finally:
        if own:
            await client.aclose()
