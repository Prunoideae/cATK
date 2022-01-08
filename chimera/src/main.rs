use clap::{clap_app, crate_authors, crate_version};

use anyhow::Result;
use std::collections::HashMap;

use crate::{
    chimeric_extract::chimeric_extract, merge_regions::merge_regions,
    overlap_extract::overlap_extract,
};

mod annotate;
mod chimeric_extract;
mod merge_regions;
mod overlap_extract;
mod test;
mod util;

#[derive(Clone)]
pub struct PartialSAM {
    read: String,
    flag: u16,
    start: u64,
    chr: String,
    sequence: String,
    original: String,
    cigar: String, //Do not parse it right on the reading
    features: HashMap<String, Vec<String>>,
}

impl From<String> for PartialSAM {
    fn from(s: String) -> Self {
        let mut spt = s.split("\t").into_iter();
        let read = spt.next().unwrap().to_string();
        let flag = spt.next().unwrap().parse::<u16>().unwrap();
        let chr = spt.next().unwrap().to_string();
        let start = spt.next().unwrap().parse::<u64>().unwrap();
        let mut spt = spt.skip(1);
        let cigar = spt.next().unwrap().to_string();
        let mut spt = spt.skip(3);
        let sequence = spt.next().unwrap().to_string();
        let features: HashMap<String, Vec<String>> = spt
            .skip(1)
            .map(|feature_str| {
                let mut feature_collections = feature_str.split(":");
                let header = feature_collections.next().unwrap().to_string();
                let features: Vec<_> = feature_collections.map(|x| x.to_string()).collect();
                (header, features)
            })
            .collect();
        PartialSAM {
            read,
            flag,
            start,
            chr,
            cigar,
            sequence,
            original: s,
            features,
        }
    }
}

struct CIGAR;
impl CIGAR {
    pub fn parse(cigar: &str) -> Result<Vec<(char, u8)>> {
        let mut result = Vec::new();
        for ch in cigar.split_inclusive(|x: char| x.is_alphabetic()) {
            result.push((ch.chars().last().unwrap(), ch[..ch.len() - 1].parse()?))
        }
        Ok(result)
    }
}

fn main() {
    let matches = clap_app!(
        chimera=>
        (about: "The core utility for cATK to perform.")
        (version: crate_version!())
        (author: crate_authors!())
        (@subcommand chimera =>
            (about: "Pick out chimeric reads from SAM stream")
            (version: crate_version!())
            (@arg input: -i --input [String] "input path, leave out to stdin")
            (@arg pairs: -p --pairs +required [String] "output the read pair span")
            (@arg output: -o --output +required [String] "output the chimeric reads for mapping")
        )
        (@subcommand merge =>
            (about: "Merge overlapped regions in pairs file")
            (version:crate_version!())
            (@arg input: -i --input [String] "input path, leave out to stdin")
            (@arg output: -o --output "output path, leave out to stdout")
            (@arg extend: -e --extend +required [u64] "extended region length")
            (@arg min: --min [u64] "the minimum region length")
            (@arg max: --max [u64] "the maximum region length")
        )
        (@subcommand overlap =>
            (about: "Pick out overlapped reads from SAM stream")
            (version: crate_version!())
            (@arg input: -i --input [String] "input path, leave out to stdin")
            (@arg output: -o --output [String] "output path, leave out to stdout")
            (@arg fasta: -a --fa +required [String] "chimeric reads path")
        )
        (@subcommand annotate =>
            (about: "Annotate the circular RNAs by given annotation")
            (version: crate_version!())
            (@arg juncs: -j --junctions_file [String] +required "junction file from align module")
            (@arg reference: -r --reference_file [String] +required "gene annotation file")
            (@arg output: -o --output [String] +required "write annotated circular RNA to")
        )
    )
    .get_matches_safe()
    .unwrap_or_else(|x| x.exit());

    if matches.is_present("chimera") {
        let matches = matches.subcommand_matches("chimera").unwrap();
        chimeric_extract(matches);
    } else if matches.is_present("overlap") {
        let matches = matches.subcommand_matches("overlap").unwrap();
        overlap_extract(matches);
    } else if matches.is_present("merge") {
        let matches = matches.subcommand_matches("merge").unwrap();
        merge_regions(matches);
    } else if matches.is_present("annotate") {
        let matches = matches.subcommand_matches("annotate").unwrap();
    }
}
