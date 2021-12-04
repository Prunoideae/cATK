from dataclasses import dataclass
from utils import async_system
from os import path

CONFIG_BASE = path.join(path.dirname(__file__), "config_template")


@dataclass
class SOAPdenovo():
    max_read_len: int
    insert_size: int
    reverse_seq: bool
    asm_flags: int
    fastq1: str
    fastq2: str = None

    def generate_config(self, config_path: str):
        self.config_path = config_path
        if self.fastq2 == "":
            config = CONFIG_BASE + "_SE"
        else:
            config = CONFIG_BASE + "_PE"
        open(config_path, 'w').write(open(config).read().format(**self.__dict__))

    async def run(self, binary: str, output: str, addi: str = "", config_path: str = None):
        if config_path is None:
            try:
                config_path = self.config_path
            except:
                raise AttributeError("SOAPdenovo wrapper is not initialized")

        await async_system(f"\"{binary}\" all -s \"{config_path}\" -o \"{output}\" {addi}")
        return f"{output}.scafSeq"
