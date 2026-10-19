"""Recompute circular-binary GW scales and diagnose two-body integration drift."""
import csv
import itertools
import json
import math
from pathlib import Path
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
YEAR = 365.25 * 86400


def radiation():
    G, c, m1, m2, a = 6.67430e-11, 299792458., 1.98847e30, 5.9722e24, 149597870700.
    power = 32 / 5 * G**4 * m1**2 * m2**2 * (m1+m2) / (c**5 * a**5)
    beta = 64 / 5 * G**3 * m1 * m2 * (m1+m2) / c**5
    merge = a**4 / (4 * beta)
    energy = -G * m1 * m2 / (2*a)
    return {'inputs':{'G_SI':G,'c_m_s':c,'solar_mass_kg':m1,'earth_mass_kg':m2,'a_m':a,'eccentricity':0},
            'power_W':power,'merge_years':merge/YEAR,'local_energy_years':abs(energy)/power/YEAR,
            'local_to_merge_ratio':abs(energy)/power/merge,'da_m_per_second':-beta/a**3}


def acceleration(x, y):
    scale = (x*x+y*y)**-1.5
    return -x*scale, -y*scale


def advance(state, dt, method):
    x, y, vx, vy = state
    ax, ay = acceleration(x, y)
    if method == 'Euler':
        return x+dt*vx, y+dt*vy, vx+dt*ax, vy+dt*ay
    vx, vy = vx+.5*dt*ax, vy+.5*dt*ay
    x, y = x+dt*vx, y+dt*vy
    ax, ay = acceleration(x, y)
    return x, y, vx+.5*dt*ax, vy+.5*dt*ay


def orbit(method, steps, periods=30):
    state, dt, rows = (1.,0.,0.,1.), 2*math.pi/steps, []
    started = time.perf_counter()
    for i in range(periods*steps+1):
        x,y,vx,vy = state
        energy = .5*(vx*vx+vy*vy)-1/math.hypot(x,y)
        if i % max(1,steps//20) == 0:
            rows.append({'orbits':i/steps,'relative_energy_error':(energy+.5)/.5})
        state = advance(state,dt,method)
    summary = {'method':method,'steps_per_orbit':steps,'orbits':periods,
               'max_relative_energy_error':max(abs(r['relative_energy_error']) for r in rows),
               'final_relative_energy_error':rows[-1]['relative_energy_error'],'seconds':time.perf_counter()-started}
    return summary,rows


def budget():
    tasks = [{'id':'resolution','name':'加倍时间分辨率','cost':1}, {'id':'duration','name':'延长积分时间','cost':2},
             {'id':'ensemble','name':'初值扰动集合','cost':3}]
    feasible = [list(pair) for pair in itertools.combinations(tasks,2) if sum(t['cost'] for t in pair)<=3]
    return {'budget_units':3,'minimum_tasks':2,'candidates':tasks,'feasible_pairs':feasible,
            'selected':[t['id'] for t in feasible[0]],'cost_basis':'规划计算配额；不是实付费用'}


def write_plot(runs):
    fig,ax=plt.subplots(figsize=(8.5,4.4),layout='constrained')
    for summary,rows in runs:
        if summary['steps_per_orbit']==200:
            ax.plot([r['orbits'] for r in rows],[abs(r['relative_energy_error'])+1e-16 for r in rows],label=summary['method'])
    ax.set(yscale='log',xlabel='Orbital periods',ylabel='Absolute relative energy error',title='Same model, different numerical methods')
    ax.grid(alpha=.2);ax.legend();fig.savefig(OUT/'energy-drift.png',dpi=160);plt.close(fig)


def main():
    runs = [orbit(method,steps) for method in ['Euler','Leapfrog'] for steps in [100,200,400]]
    value = {'radiation':radiation(),'integration':[summary for summary,_ in runs],'budget':budget(),
             'model':{'integration':'GM=1, r0=1, v0=1, circular orbit, no physical dissipation','periods':30}}
    (OUT/'results.json').write_text(json.dumps(value,indent=2)+'\n')
    with (OUT/'integration.csv').open('w') as target:
        writer=csv.DictWriter(target,fieldnames=list(value['integration'][0]));writer.writeheader();writer.writerows(value['integration'])
    write_plot(runs)
    print(json.dumps(value,indent=2))


if __name__=='__main__':main()
