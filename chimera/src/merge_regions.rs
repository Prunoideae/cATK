use std::collections::HashMap;

use clap::ArgMatches;

use crate::util;
use std::io::prelude::*;

pub fn merge_regions(matches: &ArgMatches) {
    let mut output = util::write_file(matches.value_of("output"));
    let mut read_pairs: HashMap<String, Vec<(u64, u64)>> = HashMap::new();
    let (min, max) = (
        matches
            .value_of("min")
            .and_then(|x| x.parse::<u64>().ok())
            .unwrap(),
        matches
            .value_of("max")
            .and_then(|x| x.parse::<u64>().ok())
            .unwrap(),
    );

    util::read_file(matches.value_of("input"))
        .lines()
        .map(|x| x.unwrap())
        .map(|x| {
            let mut splited = x.split("\t");
            (
                splited.next().unwrap().to_string(),
                (
                    splited.next().and_then(|x| x.parse::<u64>().ok()).unwrap(),
                    splited.next().and_then(|x| x.parse::<u64>().ok()).unwrap(),
                ),
            )
        })
        .filter(|(_, (start, end))| min < end - start && end - start < max)
        .for_each(|(chr, region)| {
            read_pairs
                .entry(chr)
                .or_insert_with(|| Vec::new())
                .push((region.0, region.1))
        });

    let merged_total: u64 = read_pairs
        .values_mut()
        .map(|x| {
            let mut merged_count = 0;
            x.sort_by_key(|x| x.0);
            let mut merged: Vec<(u64, u64)> = Vec::new();
            {
                let mut pointer = 1;
                let mut merged_loci: (u64, u64) = *x.get(0).unwrap();
                loop {
                    if pointer >= x.len() {
                        merged.push(merged_loci);
                        break;
                    }
                    let current_loci = x.get(pointer).unwrap();
                    if merged_loci.1 > current_loci.0 {
                        merged_loci = (merged_loci.0, current_loci.1);
                        merged_count += 1;
                    } else {
                        merged.push(merged_loci);
                        merged_loci = *current_loci;
                    }
                    pointer += 1;
                }
            }
            *x = merged;
            merged_count
        })
        .sum();

    eprintln!("Merged {} regions.", merged_total);

    read_pairs.iter().for_each(|(k, v)| {
        v.iter().for_each(|x| {
            writeln!(output, "{}\t{}\t{}", k, x.0, x.1).ok();
        })
    });
}
