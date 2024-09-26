"""

need a way to parse aws API docs and gen API code

consolidate all SDK/Github API
CDK for API gateway
git action -> trigger a job -> CDK/SDK(attach API gateway)




"""

from _common import _decorator as _decorator_

import asyncio


@_decorator_.sync_to_async
def sync_function(x, y):
    import time
    time.sleep(2)  # Simulate a blocking operation
    return x + y


# To call the decorated function, you need to be inside an async function or an event loop
async def main():
    result = await sync_function(10, 20)
    print(result)

# Run the async function
asyncio.run(main())