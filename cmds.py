from groups import AlignArgs, AlignInputArgs, AssembleArgs, AssembleInputArgs, ParseArgs, QuantificateArgs, UniversalArgs
from utils import async_system
from wdp.cli.cli import command
from wdp.runner.model import Runnable, Conditional

from os import path, makedirs


@command("all")
class All(Runnable):
    '''
    run the complete pipeline
    '''

    universal = UniversalArgs
    align = AlignArgs
    parse = ParseArgs
    assemble = AssembleArgs
    quantificate = QuantificateArgs

    async def run(self):
        return await super().run()


@command("align")
class Align(Runnable):
    '''
    map the reads to the reference genome with bwa and chimera
    '''

    input = AlignInputArgs
    universal = UniversalArgs
    align = AlignArgs
    parse = ParseArgs

    async def run(self):
        self.universal.manifest()
        self.align.manifest()

        min_len, max_len = map(int, self.parse.filter_length.split(","))

        if not self.input.prefix:
            # build the bwa index
            prefix = path.join(self.align.align_dir, "db")
            await async_system(f"\"{self.align.bwa_binary}\" index -p {prefix} {self.input.db}")
            self.input.db = prefix

        mapped_fq1 = path.join(self.align.align_dir, "mapped.1.fq")
        mapped_fq2 = path.join(self.align.align_dir, "mapped.2.fq") if self.input.fq2 else None

        _fq2 = f' \"{self.input.fq2}\"' if self.input.fq2 else ''

        out_bam = path.join(self.align.align_dir, "mapped.bam")
        chimeric_sam = path.join(self.align.align_dir, "chimeric.sam")
        out_pairs = path.join(self.align.align_dir, "mapped.pairs")
        out_sorted_pairs = path.join(self.align.align_dir, "mapped.uniq.pairs")
        out_merged_pairs = path.join(self.align.align_dir, "mapped.merged.pairs")

        # bwa mem | samtools view -q 30 | chimera-bin | samtools view -bS
        # No penalty on pair mismatch and 5/3 end clipping
        # Recover some of the suppressed alignment
        # This is for junction reads' features.
        await async_system(f"\"{self.align.bwa_binary}\""
                           f" mem -L0 -t {self.universal.threads} -k {self.align.seed_length} "
                           f"\"{self.input.db}\" \"{self.input.fq1}\""
                           f"{_fq2}"
                           f'| \"{self.parse.samtools_binary}\" view -Sh -q 30 - '
                           f'| \"{self.parse.chimera_binary}\" chimera -p \"{out_pairs}\" -o \"{chimeric_sam}\"'
                           f'| \"{self.parse.samtools_binary}\" view -bS '
                           f"-@ {self.universal.threads} - "
                           f'> \"{out_bam}\"')

        # sort | uniq | tee | chimera merge
        await async_system(f"sort \"{out_pairs}\" "
                           f"| python3 \"{self.parse.uniq_binary}\""
                           f"| tee \"{out_sorted_pairs}\""
                           f"| \"{self.parse.chimera_binary}\" merge"
                           f" -e {self.parse.extend_length} --min {min_len} --max {max_len} "
                           f"> \"{out_merged_pairs}\"")

        # samtools view | chimera overlap | samtools fastq
        _fqoutput = f"-1 \"{mapped_fq1}\" -2 \"{mapped_fq2}\"" if self.input.fq2 else f"> \"{mapped_fq1}\""
        await async_system(f"\"{self.parse.samtools_binary}\" view -Sh \"{out_bam}\""
                           f"| \"{self.parse.chimera_binary}\" overlap -a \"{out_merged_pairs}\""
                           f"| \"{self.parse.samtools_binary}\" fastq - "
                           f"{_fqoutput}")

        return out_sorted_pairs, mapped_fq1, mapped_fq2


@command("annotate")
class Annotate(Runnable):
    '''
    annotate the alignments by a reference genes list,
    this produces mapped junction reads and unmapped junction reads,
    which will have completely different usage in workflows
    '''
    async def run(self):
        return await super().run()


@command("parse")
class Parse(Runnable):
    '''
    parse the alignment with chimera
    '''

    universal = UniversalArgs
    parse = ParseArgs

    async def run(self):
        pass


@command("assemble")
class Assemble(Runnable):
    '''
    assemble the circRNA transcriptome by the result of align,
    outputs the circRNA sequences, mostly just a wrapped up SOAPdenovo-Trans
    but will filter out unmapped sequences too
    '''
    input = AssembleInputArgs
    universal = UniversalArgs
    assemble = AssembleArgs
    align = AlignArgs
    parse = ParseArgs

    async def run(self):

        self.assemble.manifest()

        # Construct the SOAP config and run it
        from soap_wrapper.SOAP import SOAPdenovo
        input = self.input
        soap = SOAPdenovo(
            max_read_len=input.read_length,
            insert_size=input.insert_size,
            reverse_seq=1 if input.reversed else 0,
            asm_flags=input.asm_flags,
            fastq1=input.fastq1,
            fastq2=None if not path.isfile(input.fastq2) else input.fastq2
        )
        soap.generate_config(path.join(self.assemble.soap_dir, "soap.config"))
        raw_scafseq = await soap.run(binary=self.assemble.soapdenovo_binary,
                                     output=path.join(self.assemble.soap_dir, "out"))

        # Align the chimeric reads to the scaffolds
        chimeric_fastq = path.join(self.assemble.assemble_dir, "chimeric.fq")
        await async_system(f"\"{self.parse.samtools_binary}\" fastq \"{self.input.chimeric_reads}\" > \"{chimeric_fastq}\"")
        scafseq_hits = path.join(self.assemble.assemble_dir, "uniq.txt")
        await async_system(f"\"{self.align.bwa_binary}\" index \"{raw_scafseq}\"")
        await async_system(f"\"{self.align.bwa_binary}\""
                           f" mem -t {self.universal.threads} -k {self.align.seed_length} "
                           f"\"{raw_scafseq}\" \"{chimeric_fastq}\""
                           f'| \"{self.parse.samtools_binary}\" view -S -q 30 -'
                           " | awk -F\"\\t\" '{if ($3) print $3}'"
                           f"| \"{self.assemble.uniq_binary}\" > \"{scafseq_hits}\"")

        # Write output according to the mapped sequences
        mapped = list(map(str.rstrip, open(scafseq_hits)))


@command("quantificate")
class Quantificate(Runnable, Conditional):
    '''
    estimate the sequencing depth of each circRNA sequence,
    outputs the depth graph
    '''

    universal = UniversalArgs
    quantificate = QuantificateArgs

    async def run(self):
        pass
