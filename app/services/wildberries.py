import httpx
import logging

logger = logging.getLogger(__name__)

async def fetch_product_data(artikul: str):
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            logger.info(f"Response from Wildberries: {data}")

            product_data = data.get("data", {}).get("products", [])
            if not product_data:
                return None

            product = product_data[0]
            return {
                "name": product.get("name"),
                "artikul": artikul,
                "price": product.get("salePriceU", 0) / 100,  # Цена в рублях
                "rating": product.get("rating", 0),
                "quantity": sum(size.get("qty", 0) for size in product.get("sizes", [])),
            }
    except Exception as e:
        logger.error(f"Error fetching product data: {e}")
        return None