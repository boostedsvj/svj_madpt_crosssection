import os, os.path as osp, glob, re, argparse
import matplotlib.pyplot as plt
import numpy as np


def set_matplotlib_fontsizes(small=18, medium=22, large=26):
    import matplotlib.pyplot as plt
    plt.rc('font', size=small)          # controls default text sizes
    plt.rc('axes', titlesize=small)     # fontsize of the axes title
    plt.rc('axes', labelsize=medium)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=small)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=small)    # fontsize of the tick labels
    plt.rc('legend', fontsize=small)    # legend fontsize
    plt.rc('figure', titlesize=large)   # fontsize of the figure title
set_matplotlib_fontsizes()

class Record:
    def __init__(self, model_name, filter_eff, after_filter_xs, after_filter_xs_err, n_after_matching):
        self.model_name = model_name
        self.filter_eff = filter_eff
        self.after_filter_xs = after_filter_xs
        self.after_filter_xs_err = after_filter_xs_err
        self.n_after_matching = n_after_matching

    @property
    def after_matching_xs(self):
        return self.after_filter_xs / self.filter_eff

    @property
    def after_matching_xs_err(self):
        return self.after_filter_xs_err / self.filter_eff

    @property
    def madpt(self):
        return int(re.match(r'madpt(\d+)', self.model_name).group(1))

    @property
    def mz(self):
        return int(re.search(r'mz(\d+)', self.model_name).group(1))

    @property
    def rinv(self):
        return float(re.search(r'rinv([\d\.]+)', self.model_name).group(1))

    def __repr__(self):
        return (
            f'{self.model_name:35}'
            f' xs (after filter): {self.after_filter_xs:9.3f}'
            f' +- {self.after_filter_xs_err:<7.3f}'
            f' filter eff: {self.filter_eff:<7.3f}'
            f' xs (after mtchg): {self.after_matching_xs:9.3f}'
            f' +- {self.after_matching_xs_err:<7.3f}'
            f' (n={self.n_after_matching})'
            )

def read_genxsec_output(txt_file):
    with open(txt_file) as f:
        txt = f.readlines()

    current_model = None
    current_filter_eff = None
    current_after_filter_xs = None
    current_after_filter_xs_err = None
    current_n_after_matching = None

    records = []

    for line in txt:
        line = line.strip()
        if not line: continue

        if (match := re.search(r'Closed file ([\w/\.\:]+)', line)):
            if current_model:
                # Write whatever is there now
                records.append(Record(
                    current_model,
                    current_filter_eff,
                    current_after_filter_xs,
                    current_after_filter_xs_err,
                    current_n_after_matching
                    ))
                current_model = None
                current_filter_eff = None
                current_after_filter_xs = None
                current_after_filter_xs_err = None
                current_n_after_matching = None

            root_file = match.group(1)
            current_model = re.search(r'/(madpt[\w\.]+)/', root_file).group(1)

        elif (match := re.search(
            r'Filter efficiency \(event-level\)= \((\d+)\) / \((\d+)\)',
            line
            )):
            current_filter_eff = float(match.group(1)) / float(match.group(2))
            current_n_after_matching = float(match.group(2))

        elif (match := re.search(
            r'After filter: final cross section = ([\d\.e+\-]+) \+- ([\d\.e+\-]+) pb',
            line
            )):
            current_after_filter_xs = float(match.group(1))
            current_after_filter_xs_err = float(match.group(2))

    return records


def test_read_xs_output():
    parser = argparse.ArgumentParser()
    parser.add_argument('txtfile')
    args = parser.parse_args()
    records = read_genxsec_output(args.txtfile)
    for r in records:
        print(r)


def plot_and_fit_xs():
    parser = argparse.ArgumentParser()
    parser.add_argument('txtfile')
    args = parser.parse_args()
    all_records = read_genxsec_output(args.txtfile)

    for madpt in [300]:
        records = [r for r in all_records if r.madpt==madpt and r.rinv==0.1]
        records.sort(key=lambda r: r.mz)
        mzs = np.array([r.mz for r in records])
        xss = np.array([r.after_matching_xs for r in records])
        exss = np.array([r.after_matching_xs_err for r in records])

        # Apply g_q scaling
        xss *= 0.25**2
        exss *= 0.25**2

        # Fit
        fit, cov = np.polyfit(mzs, xss, 1, cov=True)
        f = np.poly1d(fit)
        mzs_fine = np.linspace(mzs[0], mzs[-1], 100)
        xss_fine = f(mzs_fine)

        fig = plt.figure(figsize=(8,8))
        ax = fig.gca()
        
        ax.errorbar(
            mzs, xss, exss, None,
            'o',
            c='red', label='xs (GXSA, $g_{q}$-scaled)', markersize=8
            )
        ax.plot(mzs_fine, xss_fine, label='fit')

        ax.set_ylabel(r'$\sigma$ after matching (pb)')
        ax.set_xlabel(r'$m_{Z\prime}$ (GeV)')
        ax.legend()

        outfile = f'xs_madpt{madpt}.png'
        plt.savefig(outfile, bbox_inches='tight')
        os.system(f'imgcat {outfile}')

        fit_outfile = f'fit_madpt{madpt}.txt'
        print(f'Dumping fit result to {fit_outfile}')
        with open(fit_outfile, 'w') as f:
            f.write(repr(list(fit)))

plot_and_fit_xs()
# test_read_xs_output()