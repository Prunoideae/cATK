from argparse import ArgumentTypeError
from shutil import which
from wdp.cli.model import Arg, ArgGroup
from wdp.collector.concrete.common import SimpleField
from wdp.collector.concrete.int import Int
from wdp.collector.concrete.str import DirLike, FileLike, Str
from wdp.util.decorator import oneshot, singleton
import os
from os import name, path
from wdp.util.error import throw_if_false


def throw_if_no_binary(bin: str):
    if which(bin) is None:
        raise ArgumentTypeError(f"binary is not valid at \"{bin}\"")


@singleton()
class UniversalArgs(ArgGroup):
    name = "universal arguments"

    threads = Arg(required=False,
                  help="the threads used in command.",
                  meta="INT",
                  short="t",
                  long="threads",
                  default=os.cpu_count()
                  ).field(Int().ranged(lower=0).unwrapped())
    keep_temp = Arg(default=False,
                    help="keep the temporary files",
                    long="keep-temp"
                    ).field(SimpleField(bool))
    work_dir = Arg(
        required=True,
        help="the working directory",
        short="w",
        long="work-dir",
        meta="DIR"
    ).field(DirLike(exists=False))

    @oneshot
    def manifest(self):
        self.work_dir.make()


@singleton()
class AlignArgs(ArgGroup):
    name = "aligning arguments"

    seed_length = Arg(required=False,
                      help="the minimum length for a mapping to be valid",
                      meta="INT",
                      long="seed-length",
                      default=19).field(Int().ranged(lower=0).unwrapped())

    bwa_binary = Arg(required=False,
                     help="the bwa binary path",
                     meta="STR",
                     long="bwa-binary",
                     default="bwa"
                     ).field(Str()
                             .with_validator(throw_if_no_binary)
                             .unwrapped())

    # Stole from UniversalArgs
    work_dir = DirLike(exists=False)
    keep_temp: bool = SimpleField(bool)
    align_dir: str

    @oneshot
    def manifest(self):
        self.align_dir = DirLike(exists=False).accept(path.join(self.work_dir.inner, "align"))
        self.align_dir.make()
        self.align_dir = self.align_dir.unwrap()


@singleton()
class AlignInputArgs(ArgGroup):
    name = "aligning input file arguments"

    fq1 = Arg(required=True,
              help="the fastq file input",
              meta="FILE",
              long="fq1",
              short='1').field(FileLike(exists=True).unwrapped())

    fq2 = Arg(required=False,
              help="the fastq file input 2 for PE-end data",
              meta="FILE",
              long="fq2",
              short="2",
              default="").field(FileLike(exists=False).unwrapped())

    db = Arg(required=True,
             help="the path to the query fasta, or the prefix to the bwa index",
             meta="FILE",
             long="db",
             short="d").field(FileLike(exists=False).unwrapped())

    prefix: bool = Arg(
        required=True,
        help="if the db is the prefix to the bwa index",
        long="prefix",
        short="p",
        default=False).field(SimpleField(bool))


@singleton()
class ParseArgs(ArgGroup):
    name = "parsing arguments"

    chimera_binary = path.join(path.dirname(__file__), 'tools', "chimera-bin")
    uniq_binary = path.join(path.dirname(__file__), 'tools', "uniq.py")

    samtools_binary = Arg(required=False,
                          help="the samtools binary path",
                          meta="STR",
                          long="samtools-binary",
                          default="samtools").field(
                              Str()
        .with_validator(throw_if_no_binary)
        .unwrapped()
    )

    extend_length = Arg(default=0,
                        help="the extended region for the pairs",
                        meta="INT",
                        long="extend-length").field(Int().ranged(0,).unwrapped())

    filter_length = Arg(default="10,10000",
                        help="the minimum length of a circRNA",
                        meta="INT,INT",
                        long="filter-length").field(
                            Str()
                            .with_validator(
                                lambda x: throw_if_false(len([int(y) for y in x.split(",")]) == 2,
                                                         ArgumentTypeError(f"Cannot parse {x} into MIN,MAX pairs")))
                            .unwrapped()
    )

    # Stole from UniversalArgs
    work_dir = DirLike(exists=False)
    keep_temp: bool = SimpleField(bool)
    parse_dir: DirLike

    @oneshot
    def manifest(self):
        self.parse_dir = DirLike(exists=False).accept(path.join(self.work_dir.inner, "parse"))
        self.parse_dir.make()


@singleton()
class AssembleArgs(ArgGroup):
    name = "assemble arguments"

    soapdenovo_binary = Arg(default="SOAPdenovo-Trans-31mer",
                            help="the SOAPdenovo-Trans binary path",
                            long="soapdenovo-binary",
                            meta="STR").field(Str().with_validator(throw_if_no_binary).unwrapped())
    uniq_binary = Arg(default=path.join(path.dirname(__file__), "tools", "uniq.py"),
                      help="the uniq.py binary path",
                      long="uniq-binary",
                      meta="STR").field(FileLike(exists=True).unwrapped())

    # Stole from UniversalArgs
    work_dir = DirLike(exists=False)
    keep_temp: bool = SimpleField(bool)

    # Generated
    assemble_dir: str
    soap_dir: str

    @oneshot
    def manifest(self):
        self.assemble_dir = DirLike(exists=False).accept(path.join(self.work_dir.unwrap(), "assemble"))
        self.assemble_dir.make()
        self.assemble_dir = self.assemble_dir.unwrap()
        self.soap_dir = DirLike(exists=False).accept(path.join(self.assemble_dir, "soap"))
        self.soap_dir.make()
        self.soap_dir = self.soap_dir.unwrap()


@singleton()
class AssembleInputArgs(ArgGroup):
    name = "assemble input file arguments"

    chimeric_reads = Arg(required=True,
                         help="the chimeric junctions of circRNAs in SAM",
                         meta="FILE",
                         long="chimeric-reads",
                         short="c").field(FileLike(exists=True).unwrapped())

    read_length = Arg(default=150,
                      help="the max read length of the chimeric reads, excessive ones will be truncated",
                      meta="INT",
                      long="read-length").field(Int().ranged(0,).unwrapped())

    insert_size = Arg(default=150,
                      help="the insert size of the reads",
                      meta="INT",
                      long="insert-size").field(Int().ranged(0,).unwrapped())

    reversed: bool = Arg(default=False,
                         help="if the reads should be reversed, set the reverse_seq flag to 1",
                         long="reversed").field(SimpleField(bool))

    asm_flags = Arg(default=3,
                    help="the asm_flags in SOAPdenovo config",
                    meta="INT",
                    long="asm-flags").field(Int().unwrapped())

    fastq1 = Arg(required=True,
                 help="reads set 1 in fastq format",
                 meta="FILE",
                 long="fastq1",
                 short="1").field(FileLike(exists=True).unwrapped())

    fastq2 = Arg(default="",
                 help="reads set 2 in fastq format, will switch to PE after specified",
                 short="2",
                 long="fastq2").field(FileLike(exists=False).unwrapped())


@singleton()
class AnnotateArgs(ArgGroup):
    chimera_binary = path.join(path.dirname(__file__), 'tools', "chimera-bin")
    merge_binary = path.join(path.dirname(__file__), 'tools', "merge.py")

    edge: bool = Arg(
        help="if the start/end of gene will be considered as splice site",
        long="edge",
        short="e",
        default=False).field(SimpleField(bool))

    single: bool = Arg(
        help="output single hits for salvation",
        long="single",
        short="s",
        default=False).field(SimpleField(bool))

    extend_length = Arg(default=10,
                        help="the extended region for the hits",
                        meta="INT",
                        long="extend-length").field(Int().ranged(0,).unwrapped())


@singleton()
class AnnotateInputArgs(ArgGroup):
    juncs = Arg(required=True,
                help="the junction file input",
                meta="FILE",
                long="juncs",
                short='j').field(FileLike(exists=True).unwrapped())

    reference = Arg(required=True,
                    help="the reference file input, in GenePred format",
                    meta="FILE",
                    long="reference",
                    short='j').field(FileLike(exists=True).unwrapped())

    # Stole from UniversalArgs
    work_dir = DirLike(exists=False)
    keep_temp: bool = SimpleField(bool)
    annotate_dir: str

    @oneshot
    def manifest(self):
        self.annotate_dir = DirLike(exists=False).accept(path.join(self.work_dir.inner, "annotate"))
        self.annotate_dir.make()
        self.annotate_dir = self.annotate_dir.unwrap()


@singleton()
class QuantificateArgs(ArgGroup):
    name = "quantificate arguments"

    # Stole from UniversalArgs
    work_dir = DirLike(exists=False)
    keep_temp: bool = SimpleField(bool)
