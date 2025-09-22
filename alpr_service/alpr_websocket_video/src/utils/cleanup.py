import asyncio

from .logging import logger

async def shutdown_tasks(timeout=10):
  tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
  for task in tasks:
    task.cancel()
  
  try:
    await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
  except asyncio.TimeoutError:
    logger.info(f"Timeout occurred while waiting for tasks to complete after {timeout} seconds.")
  except Exception as e:
    logger.error(f"Error during shutdown: {e}")
  finally:
    logger.info("All tasks have been cancelled or completed.")
  await asyncio.gather(*tasks, return_exceptions=True)