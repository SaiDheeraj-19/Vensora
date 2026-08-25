import asyncio
import time
import httpx
import statistics
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000/api/v1/health"
CONCURRENCY = 50
TOTAL_REQUESTS = 500

async def fetch(client):
    start = time.time()
    try:
        response = await client.get(API_URL)
        response.raise_for_status()
        latency = time.time() - start
        return latency, response.status_code
    except Exception as e:
        return None, 500

async def run_benchmark():
    logger.info(f"Starting Load Test: {TOTAL_REQUESTS} requests, {CONCURRENCY} concurrent workers")
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Create a semaphore to limit concurrency
        sem = asyncio.Semaphore(CONCURRENCY)
        
        async def bounded_fetch():
            async with sem:
                return await fetch(client)
                
        tasks = [bounded_fetch() for _ in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)
        
    end_time = time.time()
    
    latencies = [r[0] for r in results if r[0] is not None]
    errors = sum(1 for r in results if r[1] != 200)
    
    if not latencies:
        logger.error("All requests failed!")
        return
        
    total_time = end_time - start_time
    rps = TOTAL_REQUESTS / total_time
    
    logger.info("=== Benchmarking Results (API Concurrency) ===")
    logger.info(f"Total Time:     {total_time:.2f}s")
    logger.info(f"Throughput:     {rps:.2f} req/s")
    logger.info(f"Error Rate:     {(errors/TOTAL_REQUESTS)*100:.1f}%")
    logger.info(f"P50 Latency:    {statistics.median(latencies)*1000:.1f}ms")
    logger.info(f"P95 Latency:    {statistics.quantiles(latencies, n=100)[94]*1000:.1f}ms")
    logger.info(f"P99 Latency:    {statistics.quantiles(latencies, n=100)[98]*1000:.1f}ms")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
