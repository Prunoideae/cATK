import asyncio
from subprocess import STDOUT


async def async_system(command: str, debug=True) -> int:
    '''
    Execute the command in a subshell, but async.
    '''
    if debug:
        print(command)

    proc = await asyncio.create_subprocess_shell(command)
    await proc.wait()
    return proc.returncode
