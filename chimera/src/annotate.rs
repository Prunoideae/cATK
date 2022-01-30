use clap::ArgMatches;

use crate::util;
use std::io::prelude::*;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    Positive,
    Negative,
}

#[allow(non_camel_case_types)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpliceType {
    CIRNA_1,
    CIRNA_2,
    EXON,
    MONO,
    MISS,
}

impl SpliceType {
    pub fn to_str(&self) -> &str {
        match self {
            SpliceType::CIRNA_1 => "CIRNA_1",
            SpliceType::CIRNA_2 => "CIRNA_2",
            SpliceType::EXON => "EXON",
            SpliceType::MONO => "MONO",
            SpliceType::MISS => "MISS",
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

pub fn annotate(matches: &ArgMatches) {
    let junctions = util::read_file(matches.value_of("juncs"));
    let output = util::write_file(matches.value_of("output"));

    let extend = matches
        .value_of("extend")
        .unwrap_or("30")
        .parse::<u64>()
        .unwrap();
    let allow_single = matches.is_present("single");

    let preds: Vec<_> = util::read_file(matches.value_of("reference"))
        .lines()
        .map(|x| GenePred::from(x.unwrap()))
        .collect();
}

pub fn salvage_single(matches: &ArgMatches) {}
