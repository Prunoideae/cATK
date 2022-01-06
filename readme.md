# cATK (circRNA Analysis ToolKit)

This is meant to be a circRNA upstream analysis pipeline, which includes these functions:

1. Back-splicing reads identification
2. Locating circRNA on reference genomes
3. circRNA sequence assembly from reads
4. Sequence filtering and quantification agains transcriptome

Even it should have these functions, actually it provides only one single pipeline, so to be honest maybe should call it something else than a `toolkit`.

## 1. BSJ (Back-splicing Junction) identification

The key feature of a circRNA is its BSJ site. By identifying BSJs, we can easily filter out circRNAs from other reads, so what is a BSJ, and how we will pick it out from raw reads?

### 1.1 What is BSJ

The BSJ is a special splicing junction occurred only in circRNAs, it's because the circulation will always cause an inversion of the junction regions, so the order of the chimeric regions will be reversed when mapped to the genome.

### 1.2 The pipeline

[bwa-mem](https://github.com/lh3/bwa) is used here as aligner, which aligns the raw reads onto the reference genome. By using bwa-mem, all chimeric reads will be reported instantly unlike bowtie(1/2), which requires Tophat to initiate a redundant fragmentized search, greatly increasing both pipeline time and resource consumption.

[bwa-mem2](https://github.com/bwa-mem2/bwa-mem2) is the next version of bwa, which is superior in performance, maybe can switch to this for future improvement. If 3rd gen sequencing is needed, [minimap2](https://github.com/lh3/minimap2) should can help. Other aligners can be supported, but at least need an adapter for converting data to acceptable formats.

[chimera](https://github.com/Prunoideae/cATK/tree/master/chimera) is then used for picking out chimeric reads, especially the ones of interest, in the streamed SAM/BAM output.

## 2. circRNA Assembly from reads

## 3. Sequence filtering and quantification
