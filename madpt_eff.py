import os, os.path as osp, glob, re

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


class Record:

    @classmethod
    def from_log(cls, log_file):
        mz = int(re.search(r'mz(\d+)', log_file).group(1))

        with open(log_file, 'r') as f:
            txt = f.read()

            n_init = int(re.search(r'maxEvents=(\d+)', txt).group(1))
            match = re.search(r'Filter efficiency \(event\-level\)= \((\d+)\) / \((\d+)\)', txt)
            n_after_matching = int(match.group(2))
            n_after_filter = int(match.group(1))

            match = re.search(
                r'After matching: total cross section = ([\d\.e\+\-]+) \+\- ([\d\.e\+\-]+) pb',
                txt
                )
            xs = float(match.group(1))
            xs_err = float(match.group(2))

        record = cls(mz, n_init, n_after_matching, n_after_filter)
        record.xs = xs
        record.xs_err = xs_err
        return record


    def __init__(self, mz, n_init=0, n_after_matching=0, n_after_filter=0):
        self.mz = mz
        self.n_init = n_init
        self.n_after_matching = n_after_matching
        self.n_after_filter = n_after_filter
        self.xs = 0.
        self.xs_err = 0.

    def __repr__(self):
        return (
            f'<mz={self.mz}'
            f' n_init={self.n_init}'
            f' n_after_matching={self.n_after_matching}'
            f' n_after_filter={self.n_after_filter}'
            '>'
            )

    def copy(self):
        return Record(self.mz, self.n_init, self.n_after_matching, self.n_after_filter)

    def __add__(self, other):
        assert self.mz == other.mz
        out = self.copy()
        out.n_init += other.n_init
        out.n_after_matching += other.n_after_matching
        out.n_after_filter += other.n_after_filter
        return out


def calc_errs(x, cov):
    """Calculate err up and down per x value.
    See https://stackoverflow.com/a/28528966
    """
    degree = cov.shape[0]
    x_powers = np.vstack([x**i for i in range(degree-1, -1, -1)]).T
    err = np.sqrt(np.diag(
        np.dot(x_powers, np.dot(cov, x_powers.T))
        ))
    return err


def main():
    log_files = glob.glob('logs/*/*.txt')

    all_records = []
    for f in log_files:
        try:
            all_records.append(Record.from_log(f))
        except AttributeError:
            print(f'Skipping {f}')

    mzs = np.array(list(sorted(set([r.mz for r in all_records]))))

    # Get the error on the xs as reported by MadGraph
    # Take a straight average
    errs = []
    for mz in mzs:
        record = Record(mz)
        e = 0
        n = 0
        for r in all_records:
            if r.mz == mz:
                e += r.xs_err
                n += 1
        errs.append(e/n)
    errs = np.array(errs)

    x_raw = [r.mz for r in all_records]
    y_raw = [r.xs for r in all_records]

    fit, cov = np.polyfit(x_raw, y_raw, 2, cov=True)
    f = np.poly1d(fit)

    mz_fine = np.linspace(mzs[0], mzs[-1], 100)
    xs_fine = f(mz_fine)

    set_matplotlib_fontsizes()
    fig = plt.figure(figsize=(8,8))
    ax = fig.gca()
    ax.scatter(x_raw, y_raw)
    ax.plot(mz_fine, xs_fine, c='orange', label=f'${fit[0]:.2e}\cdot x^{{2}}+{fit[1]:.2e}\cdot x+{fit[2]:.2e}$')

    # Fit error: very tiny, ignore
    # err = calc_errs(mz_fine, cov)
    # ax.fill_between(mz_fine, xs_fine-err, xs_fine+err, alpha=.3)

    # Draw the error on the xs as reported by MadGraph
    ax.fill_between(mzs, f(mzs)-errs, f(mzs)+errs, alpha=.3)

    ax.set_ylabel(r'$\sigma$ after matching (pb)')
    ax.set_xlabel(r'$m_{Z\prime}$ (GeV)')
    ax.legend()

    plt.savefig('madpt_xs_fit.png', bbox_inches='tight')
    os.system('imgcat madpt_xs_fit.png')



if __name__ == '__main__':
    main()