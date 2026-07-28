# M2 prep: CV loopback self-calibration.
# Requires a mono patch cable from CV<n> out to CV<n> in on the front panel.
# Sweeps the DAC output over its range, reads it back on the ADC, and fits
# read = scale * set + offset so we can correct both directions later.

import time

import amyboard


def sweep(out_ch, in_ch, lo=-10.0, hi=10.0, step=1.0, n_avg=5):
    results = []
    v = lo
    while v <= hi + 1e-9:
        amyboard.cv_out(v, channel=out_ch)
        time.sleep(0.08)  # settle
        reads = []
        for _ in range(n_avg):
            reads.append(amyboard.cv_in(channel=in_ch))
            time.sleep(0.01)
        avg = sum(reads) / len(reads)
        spread = max(reads) - min(reads)
        results.append((v, avg, spread))
        v += step
    amyboard.cv_out(0.0, channel=out_ch)  # park at 0V
    return results


def fit_and_report(results, label):
    n = len(results)
    sx = sum(r[0] for r in results)
    sy = sum(r[1] for r in results)
    sxx = sum(r[0] * r[0] for r in results)
    sxy = sum(r[0] * r[1] for r in results)
    scale = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    offset = (sy - scale * sx) / n
    worst = 0.0
    print('== %s ==' % label)
    print('set_V;read_V;spread_V')
    for v, a, s in results:
        print('%+.2f;%+.5f;%.5f' % (v, a, s))
        err = abs(a - (scale * v + offset))
        worst = max(worst, err)
    print('fit: read = %.5f * set %+.5f' % (scale, offset))
    print('worst linearity error: %.4f V (= %.1f cents bij 1V/oct)'
          % (worst, worst * 1200))
    return scale, offset


cal_cv1 = fit_and_report(sweep(0, 0), 'CV1 out -> CV1 in')
