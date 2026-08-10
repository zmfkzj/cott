from cott_runtime import CottList, I32, I64, U32
from curriculum.roast_analysis_types import RoastAnalysis, TemperatureSample


def summarize_roast_samples(samples: CottList[TemperatureSample]) -> RoastAnalysis:
    first: TemperatureSample = samples[0]
    peak_temp_deci_c: I32 = first.bean_temp_deci_c
    peak_at_s: U32 = first.elapsed_s
    last_temp_deci_c: I32 = first.bean_temp_deci_c

    for sample in samples:
        last_temp_deci_c = sample.bean_temp_deci_c
        if sample.bean_temp_deci_c > peak_temp_deci_c:
            peak_temp_deci_c = sample.bean_temp_deci_c
            peak_at_s = sample.elapsed_s

    total_rise_deci_c: I64 = last_temp_deci_c - first.bean_temp_deci_c
    return RoastAnalysis(
        peak_temp_deci_c=peak_temp_deci_c,
        peak_at_s=peak_at_s,
        total_rise_deci_c=total_rise_deci_c,
    )
