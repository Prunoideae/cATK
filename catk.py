from wdp.cli.cli import commands
import cmds  # pylint:disable-unused-imports
import asyncio


if __name__ == "__main__":
    (asyncio
     .get_event_loop()
     .run_until_complete(
         commands("catk", "circRNA analysis toolkit.")
         .run()
     ))
