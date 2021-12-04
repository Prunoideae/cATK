use std::collections::HashMap;
use std::io::prelude::*;

use crate::{util, PartialSAM};
use clap::ArgMatches;

struct BinarySearch {
    inner: HashMap<String, Vec<(u64, u64)>>,
}

impl BinarySearch {
    fn new(inner: HashMap<String, Vec<(u64, u64)>>) -> Self {
        BinarySearch { inner }
    }

    /// Search for a given point is in the stored regions, or not.
    ///
    /// Returns None when the chromosome is unknown.
    fn search(&self, chr: &String, point: u64) -> Option<bool> {
        let vec = self.inner.get(chr)?;
        let (mut start, mut end) = (0 as i64, (vec.len() - 1) as i64);
        while start <= end {
            let mid = (start + end) / 2;
            let mid_item = vec.get(mid as usize).unwrap(); //Infallible
            if mid_item.0 <= point {
                start = mid + 1;
            } else {
                end = mid - 1
            }
        }

        Some({
            let last = vec.get((start - 1) as usize)?;
            last.0 <= point && point <= last.1
        })
    }
}

pub fn overlap_extract(matches: &ArgMatches) {
    let input = util::read_file(matches.value_of("input"));
    let mut output = util::write_file(matches.value_of("output"));

    let mut read_pairs: HashMap<String, Vec<(u64, u64)>> = HashMap::new();
    util::read_file(matches.value_of("fasta"))
        .lines()
        .map(|x| x.unwrap())
        .map(|x| {
            let mut splited = x.split("\t").into_iter();
            (
                splited.next().unwrap().to_string(),
                (
                    splited.next().and_then(|x| x.parse::<u64>().ok()).unwrap(),
                    splited.next().and_then(|x| x.parse::<u64>().ok()).unwrap(),
                ),
            )
        })
        .for_each(|(chr, region)| {
            read_pairs
                .entry(chr)
                .or_insert_with(|| Vec::new())
                .push(region)
        });

    let search = BinarySearch::new(read_pairs);

    eprintln!("Regions loaded.");

    for line in input.lines() {
        let line = line.unwrap();
        if line.starts_with("@") {
            writeln!(output, "{}", line).unwrap();
            continue;
        }

        let partial = PartialSAM::from(line);
        if let Some(true) = search.search(&partial.chr, partial.start) {
            writeln!(output, "{}", &partial.original).ok();
        }
    }
}
