# cATK (circRNA Analysis ToolKit) (WIP)

This is meant to be a circRNA upstream analysis pipeline, which includes these functions:

1. Back-splicing reads identification
2. Locating circRNA on reference genomes
3. circRNA sequence assembly from reads
4. Sequence filtering and quantification agains transcriptome

DISCLAIMER: Currently the pipeline is pretty much functional, but since it's migrating to HISAT2 from bwa, and which may introduce some new features involving more than just circular RNA detection, it's still WIP, and can have breaking change at any time.

Even it should have these functions, actually it provides only one single pipeline, so to be honest maybe should call it something else than a `toolkit`.

## 1. BSJ (Back-splicing Junction) identification

The key feature of a circRNA is its BSJ site. By identifying BSJs, we can easily filter out circRNAs from other reads, so what is a BSJ, and how we will pick it out from raw reads?

### 1.1 What is BSJ

The BSJ is a special splicing junction occurred only in circRNAs, it's because the circulation will always cause an inversion of the junction regions, so the order of the chimeric regions will be reversed when mapped to the genome.

### 1.2 The pipeline

[hisat2](http://daehwankimlab.github.io/hisat2/manual/) is used here as aligner, which aligns the raw reads onto the reference genome. By using hisat2, all chimeric reads will be reported instantly unlike bowtie(1/2), which requires Tophat to initiate a redundant fragmentized search, greatly increasing both pipeline time and resource consumption.

[chimera](https://github.com/Prunoideae/cATK/tree/master/chimera) is then used for picking out chimeric reads, especially the ones of interest, in the streamed SAM/BAM output.

## 2. circRNA Assembly from reads

## 3. Sequence filtering and quantification
