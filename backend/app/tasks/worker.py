from __future__ import annotations

import logging
import asyncio

from app.tasks.activity_status import run_activity_status_loop
from app.tasks.compensation import run_compensation_loop
from app.tasks.lottery_consumer import consume_draw_results

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    await asyncio.gather(
        run_activity_status_loop(),
        consume_draw_results(),
        run_compensation_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())