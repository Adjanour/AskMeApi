import asyncio
import aiohttp
import time
import json
from statistics import mean, stdev

# URL of your API endpoint
API_URL = 'http://127.0.0.1:8000/api/ask'
# The request payload
REQUEST_PAYLOAD = {
    "question": "what is stroke?"
}
# Number of concurrent requests to make
NUM_REQUESTS = 10

# Function to send a single request
async def send_request(session, url, data):
    async with session.post(url, json=data) as response:
        response_time = response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
        return response_time, response.status

# Function to benchmark the API
async def benchmark_api():
    async with aiohttp.ClientSession() as session:
        # Track response times
        response_times = []
        failed_requests = 0

        # Record start time
        start_time = time.time()

        # Make concurrent requests
        tasks = []
        for _ in range(NUM_REQUESTS):
            tasks.append(send_request(session, API_URL, REQUEST_PAYLOAD))

        # Run the tasks concurrently
        for task in asyncio.as_completed(tasks):
            response_time, status = await task
            if status == 200:
                response_times.append(response_time)
            else:
                failed_requests += 1

        # Calculate statistics
        total_time = time.time() - start_time
        avg_response_time = mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        response_time_stdev = stdev(response_times) if len(response_times) > 1 else 0

        # Print out the results
        print(f"Total Requests: {NUM_REQUESTS}")
        print(f"Failed Requests: {failed_requests}")
        print(f"Total Time Taken: {total_time:.2f} seconds")
        print(f"Average Response Time: {avg_response_time:.4f} seconds")
        print(f"Max Response Time: {max_response_time:.4f} seconds")
        print(f"Min Response Time: {min_response_time:.4f} seconds")
        print(f"Response Time Standard Deviation: {response_time_stdev:.4f} seconds")

if __name__ == '__main__':
    # Run the benchmark
    asyncio.run(benchmark_api())
