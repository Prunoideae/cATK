#[allow(unused_imports)]
mod tests {

    use crate::annotate;
    use crate::annotate::GenePred;
    use crate::chimeric_extract;
    use crate::PartialSAM;
    use crate::CIGAR;

    #[test]
    fn test_sam_parsing() {
        let parse_string = "E00516:28:HCYLVALXX:8:1101:14763:1854	99	chr7	152406868	60	18S133M	=	152406874	157	GGAGGGAGAAGAGGTAGTGGTGGTAATGGTTTCTGTTTTGGAGGGAGAAGAGGTAGTGGTGGTAATGGTTTCTTCTTGGGAAGGAGTATTAAGGTTTACAGTGTTTACCATTTTATTTAAAAATATTCTACTACAGAAACTGAAACATTTT	AAFFFJJJFJF-FJFJAJJAFJJJJJJJJJJJJJJJ--7F<AJJJFJ-AAJJF-FF-7F-<FJFJAFAJFJJJJFJ<FJJ-AFFAJ-FJAJJJJ-A<FAJJJJFF-7-7AFFFJJJJJJJ--<A7<AAFAF<-A7F7-7FAAFAFJFJFFJ	NM:i:1	MD:Z:102C30	MC:Z:151M	AS:i:128	XS:i:0	SA:Z:chr7,152406889,+,34M117S,60,0;";
        let sam = PartialSAM::from(parse_string.to_string());
        assert_eq!(sam.read, "E00516:28:HCYLVALXX:8:1101:14763:1854");
        assert_eq!(sam.flag, 99u16);
        assert_eq!(sam.start, 152406868u64);
        assert_eq!(sam.chr, "chr7");
        assert_eq!(sam.sequence, "GGAGGGAGAAGAGGTAGTGGTGGTAATGGTTTCTGTTTTGGAGGGAGAAGAGGTAGTGGTGGTAATGGTTTCTTCTTGGGAAGGAGTATTAAGGTTTACAGTGTTTACCATTTTATTTAAAAATATTCTACTACAGAAACTGAAACATTTT");
        assert_eq!(sam.cigar, "18S133M");
        assert!(sam.features.contains_key("SA"));
        println!(
            "{:?}",
            chimeric_extract::calculate_querys(&CIGAR::parse(&sam.cigar).unwrap())
        );
    }

    #[test]
    fn test_cigar_parsing() {
        let parse_string = "18S133M";
        assert_eq!(
            CIGAR::parse(&parse_string.to_string()).unwrap(),
            vec![('S', 18), ('M', 133)]
        );
    }

    #[test]
    fn test_cigar_relocating() {
        let start = 1;
        let cigar = vec![
            ('S', 18),
            ('M', 53),
            ('I', 2),
            ('M', 18),
            ('D', 1),
            ('M', 30),
        ];
        let (start, end) = chimeric_extract::calculate_regions(start, &cigar);
        assert_eq!(start, 1);
        assert_eq!(end, 103);
    }

    #[test]
    fn test_genepred_parsing() {
        let parse_string = "MIR6859-1	ENST00000619216.1	chr1	-	17368	17436	17368	17368	1	17368,	17436,";
        let genepred = GenePred::from(parse_string.to_string());
        println!("{:#?}", genepred);
        assert_eq!(genepred.name, "MIR6859-1");
        assert_eq!(genepred.exon_starts, vec![17368u64]);
    }

    #[test]
    fn test_judge4() {
        let (ss, ee, se, es) = (true, true, false, false);
        assert_eq!(
            annotate::judge4(ss, ee, se, es),
            annotate::SpliceType::EXON_2
        );

        let (ss, ee, se, es) = (false, false, true, true);
        assert_eq!(
            annotate::judge4(ss, ee, se, es),
            annotate::SpliceType::INTRON_2
        );
    }
}
