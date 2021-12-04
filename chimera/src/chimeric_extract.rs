use std::{io::stdout, iter};

use clap::ArgMatches;

use crate::{util, PartialSAM, CIGAR};
use std::io::prelude::*;

/// Calculate the span on ref genome of the query seq by CIGAR
pub fn calculate_regions(start: u64, cigar: &Vec<(char, u8)>) -> (u64, u64) {
    let mut offset: u64 = 0;
    for comp in cigar {
        match comp.0 {
            'M' | 'D' | 'N' | '=' | 'X' => offset += comp.1 as u64,
            _ => {}
        }
    }
    (start, start + offset)
}

pub fn calculate_querys(cigar: &Vec<(char, u8)>) -> (u64, u64) {
    let mut start = 0;
    let mut offset = 0;
    for (idx, comp) in cigar.iter().enumerate() {
        match comp.0 {
            'M' | 'I' => offset += comp.1 as u64,
            'S' => {
                if idx == 0 {
                    start += comp.1 as u64
                }
            }
            _ => {}
        }
    }
    (start, start + offset)
}

#[derive(Debug, Clone, Copy)]
struct Pos4 {
    ref_start: u64,
    ref_end: u64,
    query_start: u64,
    query_end: u64,
}

pub fn chimeric_extract(matches: &ArgMatches) {
    let input = util::read_file(matches.value_of("input"));
    let mut pairs = util::write_file(matches.value_of("pairs"));
    let mut output = util::write_file(matches.value_of("output"));
    let out = stdout();
    let mut stdout = out.lock();

    for line in input.lines() {
        let line = line.unwrap();
        writeln!(stdout, "{}", line).unwrap();
        if line.starts_with('@') {
            writeln!(output, "{}", line).unwrap();
            continue;
        }

        let sam = PartialSAM::from(line);
        if sam.flag & 0x800 != 0 || sam.flag & 0x4 != 0 {
            continue;
        }
        if !sam.features.contains_key("SA") {
            continue;
        }

        let primary_cigar = CIGAR::parse(&sam.cigar).unwrap();
        let (primary_ref_start, primary_ref_end) = calculate_regions(sam.start, &primary_cigar);
        let (primary_que_start, primary_que_end) = calculate_querys(&primary_cigar);

        let mut poses = sam
            .features
            .get("SA")
            .unwrap()
            .get(1)
            .unwrap()
            .split(';')
            .filter(|x| !x.is_empty())
            .filter_map(|x| {
                let mut sas = x.split(',');
                if sas.next().unwrap() != sam.chr {
                    return None;
                }
                let ref_pos = sas.next().unwrap().parse::<u64>().unwrap();
                if (sas.next().unwrap() == "+") != (sam.flag & 0x10 == 0) {
                    return None;
                };
                Some((ref_pos, sas.next().unwrap()))
            })
            .map(|(ref_pos, cigar)| {
                let cigar = CIGAR::parse(cigar).unwrap();
                let (ref_start, ref_end) = calculate_regions(ref_pos, &cigar);
                let (que_start, que_end) = calculate_querys(&cigar);
                Pos4 {
                    ref_start,
                    ref_end,
                    query_start: que_start,
                    query_end: que_end,
                }
            })
            .chain(iter::once(Pos4 {
                ref_start: primary_ref_start,
                ref_end: primary_ref_end,
                query_start: primary_que_start,
                query_end: primary_que_end,
            }))
            .collect::<Vec<_>>();
        poses.sort_unstable_by_key(|x| x.query_start);

        let mut split_event: Vec<(u64, u64)> = Vec::new();
        for idx in 1..poses.len() {
            let last = poses.get(idx - 1).unwrap();
            let this = poses.get(idx).unwrap();
            if this.ref_start < last.ref_end && this.query_start <= last.query_end {
                split_event.push((
                    this.ref_start,
                    last.ref_end - (last.query_end - this.query_start),
                ));
            }
        }

        //TODO: Process more
        if split_event.len() == 1 {
            let (start, end) = split_event.get(0).unwrap();
            writeln!(pairs, "{}\t{}\t{}\t{}", sam.chr, start, end, sam.read).unwrap();
            writeln!(output, "{}", &sam.original).unwrap();
        }
    }
}
