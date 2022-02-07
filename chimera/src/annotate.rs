use clap::ArgMatches;

use crate::util;
use std::{collections::HashMap, io::prelude::*, ops::RangeInclusive};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    Positive,
    Negative,
}

impl Direction {
    fn as_str(&self) -> &str {
        match self {
            Direction::Positive => "+",
            Direction::Negative => "-",
        }
    }
}

#[allow(non_camel_case_types)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpliceType {
    INTRON_1,
    INTRON_2,
    EXON_2,
    EXON_1,
    MISS,
}

impl SpliceType {
    pub fn to_str(&self) -> &str {
        match self {
            SpliceType::INTRON_1 => "INTRON_1",
            SpliceType::INTRON_2 => "INTRON_2",
            SpliceType::EXON_2 => "EXON_2",
            SpliceType::EXON_1 => "EXON_1",
            SpliceType::MISS => "MISS",
        }
    }

    pub fn from_str(s: &str) -> Result<Self, ()> {
        match s {
            "INTRON_1" => Ok(SpliceType::INTRON_1),
            "INTRON_2" => Ok(SpliceType::INTRON_2),
            "EXON_2" => Ok(SpliceType::EXON_2),
            "EXON_1" => Ok(SpliceType::EXON_1),
            "MISS" => Ok(SpliceType::MISS),
            _ => Err(()),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct Junction {
    chr: String,
    start: u64,
    end: u64,
    depth: u32,
}

impl From<String> for Junction {
    fn from(s: String) -> Self {
        let mut spt = s.split('\t');

        Self {
            chr: spt.next().unwrap().to_string(),
            start: spt.next().unwrap().parse().unwrap(),
            end: spt.next().unwrap().parse().unwrap(),
            depth: spt.next().unwrap().parse().unwrap(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenePred {
    pub name: String,
    pub id: String,
    pub chr: String,
    pub strand: Direction,
    pub transcript_start: u64,
    pub transcript_end: u64,
    pub sequence_start: u64,
    pub sequence_end: u64,

    pub exon_count: u32,
    pub exon_starts: Vec<u64>,
    pub exon_ends: Vec<u64>,
}

impl From<String> for GenePred {
    fn from(line: String) -> Self {
        let mut spt = line.split('\t');
        GenePred {
            name: spt.next().unwrap().to_string(),
            id: spt.next().unwrap().to_string(),
            chr: spt.next().unwrap().to_string(),
            strand: match spt.next().unwrap() {
                "+" => Direction::Positive,
                "-" => Direction::Negative,
                _ => unreachable!(),
            },
            transcript_start: spt.next().unwrap().parse().unwrap(),
            transcript_end: spt.next().unwrap().parse().unwrap(),
            sequence_start: spt.next().unwrap().parse().unwrap(),
            sequence_end: spt.next().unwrap().parse().unwrap(),
            exon_count: spt.next().unwrap().parse().unwrap(),
            exon_starts: spt
                .next()
                .unwrap()
                .split(',')
                .filter_map(|x| x.parse().ok())
                .collect(),
            exon_ends: spt
                .next()
                .unwrap()
                .split(',')
                .filter_map(|x| x.parse().ok())
                .collect(),
        }
    }
}

pub fn judge4(start_start: bool, end_end: bool, start_end: bool, end_start: bool) -> SpliceType {
    match (start_start, end_end, start_end, end_start) {
        //Ends meet with starts (or vise versa), usually not happening but just guard it
        (true, _, _, true) | (_, true, true, _) => SpliceType::MISS,
        //Mapped to start and end of an EXON_2, should be circular EXON_2
        (true, true, _, _) => SpliceType::EXON_2,
        //Mapped to start and end of an INTRON_2 (so end/start of EXON_2), should be circRNA
        (_, _, true, true) => SpliceType::INTRON_2,
        //Mapped to one side
        (_, _, true, _) | (_, _, _, true) => SpliceType::EXON_1,
        (true, _, _, _) | (_, true, _, _) => SpliceType::INTRON_1,
        //Hit miss
        _ => SpliceType::MISS,
    }
}

#[derive(Debug, Clone)]
struct ExonSite<'a> {
    is_start: bool,
    original_index: u64,
    genepred: &'a GenePred,
}

impl<'a> ExonSite<'a> {
    fn new(is_start: bool, original_index: u64, genepred: &'a GenePred) -> Self {
        Self {
            is_start,
            original_index,
            genepred,
        }
    }
}

pub fn annotate(matches: &ArgMatches) {
    let mut output = util::write_file(matches.value_of("output"));

    let extend = matches
        .value_of("extend")
        .unwrap_or("30")
        .parse::<u64>()
        .unwrap();
    let allow_single = matches.is_present("single");

    let genepreds: Vec<_> = util::read_file(matches.value_of("reference"))
        .lines()
        .map(|x| GenePred::from(x.unwrap()))
        .collect();

    let junctions: Vec<_> = util::read_file(matches.value_of("juncs"))
        .lines()
        .map(|x| Junction::from(x.unwrap()))
        .collect();

    let edge = matches.is_present("edge");

    // HashMap<chr_name, HashMap<site_offset, EXON_2Site(is_start, site_original, GenePred)>>
    let mut chr_preds: HashMap<String, HashMap<u64, ExonSite>> = HashMap::new();

    for pred in &genepreds {
        let chr_pred = chr_preds.entry(pred.chr.clone()).or_insert(HashMap::new());

        let mut exon_starts = pred.exon_starts.clone();
        let mut exon_ends = pred.exon_ends.clone();
        if !edge {
            exon_ends.pop();
            exon_starts.remove(0);
        }

        for index in exon_starts.iter() {
            for index_offset in index - extend..=index + extend {
                chr_pred.insert(index_offset, ExonSite::new(true, *index, pred));
            }
        }

        for index in exon_ends.iter() {
            for index_offset in index - extend..=index + extend {
                chr_pred.insert(index_offset, ExonSite::new(false, *index, pred));
            }
        }
    }

    for junction in junctions {
        let (mut start_start, mut end_end, mut start_end, mut end_start) =
            (false, false, false, false);

        if let Some(chr_pred) = chr_preds.get(&junction.chr) {
            let start_site = if let Some(site) = chr_pred.get(&junction.start) {
                if site.is_start {
                    start_start = true;
                } else {
                    start_end = true;
                }
                Some(site)
            } else {
                None
            };

            let end_site = if let Some(site) = chr_pred.get(&junction.end) {
                if site.is_start {
                    end_start = true;
                } else {
                    end_end = true;
                }

                Some(site)
            } else {
                None
            };

            match judge4(start_start, end_end, start_end, end_start) {
                double @ (SpliceType::INTRON_2 | SpliceType::EXON_2) => {
                    let (start_site, end_site) = (start_site.unwrap(), end_site.unwrap());
                    let (start_site, end_site) =
                        if start_site.original_index < end_site.original_index {
                            (start_site, end_site)
                        } else {
                            (end_site, start_site)
                        };

                    if start_site.genepred.name == end_site.genepred.name {
                        let (start_pos, end_pos) =
                            (start_site.original_index, end_site.original_index);
                        let seq_span = start_pos..=end_pos;
                        let genepred = start_site.genepred;
                        let mut seq_start_span: Vec<_> = genepred
                            .exon_starts
                            .iter()
                            .filter(|x| seq_span.contains(*x))
                            .collect();
                        let mut seq_end_span: Vec<_> = genepred
                            .exon_ends
                            .iter()
                            .filter(|x| seq_span.contains(*x))
                            .collect();
                        seq_start_span.sort_unstable();
                        seq_end_span.sort_unstable();

                        let span_str = format!(
                            "{}\t{}",
                            seq_start_span
                                .iter()
                                .map(|x| x.to_string())
                                .collect::<Vec<_>>()
                                .join(","),
                            seq_end_span
                                .iter()
                                .map(|x| x.to_string())
                                .collect::<Vec<_>>()
                                .join(",")
                        );

                        writeln!(
                            output,
                            "{}\t{}\t{}\t{}\t{}\t{}\t{}",
                            start_site.genepred.chr,
                            start_pos,
                            end_pos,
                            double.to_str(),
                            genepred.strand.as_str(),
                            span_str,
                            junction.depth
                        )
                        .unwrap();
                    }
                }
                single @ (SpliceType::EXON_1 | SpliceType::INTRON_1) => {
                    if allow_single {
                        let site = if let Some(site) = start_site {
                            site
                        } else if let Some(site) = end_site {
                            site
                        } else {
                            unreachable!()
                        };

                        let chr = &site.genepred.chr;
                        let strand = site.genepred.strand.as_str();
                        let gene_range =
                            site.genepred.transcript_start..=site.genepred.transcript_end;

                        #[inline(always)]
                        fn overlaps(r1: RangeInclusive<u64>, r2: &RangeInclusive<u64>) -> bool {
                            let max_start = r1.start().max(r2.start());
                            let min_end = r1.end().min(r2.end());
                            return max_start < min_end;
                        }

                        if !overlaps(
                            junction.start - extend..=junction.start + extend,
                            &gene_range,
                        ) || !overlaps(
                            junction.end - extend..=junction.end + extend,
                            &gene_range,
                        ) {
                            continue;
                        }

                        writeln!(
                            output,
                            "{}\t{}\t{}\t{}\t{}\t{}\t{}",
                            chr,
                            if let Some(site) = start_site {
                                site.original_index as _
                            } else {
                                -(junction.start as i64)
                            },
                            if let Some(site) = end_site {
                                site.original_index as _
                            } else {
                                -(junction.end as i64)
                            },
                            single.to_str(),
                            strand,
                            "\t",
                            junction.depth
                        )
                        .unwrap();
                    }
                }
                SpliceType::MISS => (),
            }
        }
    }
}
