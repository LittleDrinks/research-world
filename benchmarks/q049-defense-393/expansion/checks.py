import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
D=Path('/work');G=6.67430e-11;c=299792458.;Ms=1.98847e30

def mass():
 t=np.array([-.19118234,-.04541778,-.01540456]);f=np.array([35.,60.,90.]);x=f**(-8/3);k=float(x@(-t)/(x@x));mc=c**3/G*(5/(256*k)*np.pi**(-8/3))**(3/5)/Ms
 return {'t_s':t.tolist(),'f_Hz':f.tolist(),'tc_s':0,'slope':k,'chirp_mass_detector_Msun':mc,'eta':.25,'total_mass_detector_Msun':mc*.25**(-3/5),'redshift_assumed':.09,'total_mass_source_at_assumed_z_Msun':mc*.25**(-3/5)/1.09,'remnant_mass':'not inferred by this approximation'}

def timing():
 f=np.array([20.,100.,250.,1000.]);angle=360*f*10e-6
 return {'timing_error_s':1e-5,'frequency_Hz':f.tolist(),'phase_error_deg':angle.tolist(),'phase_budget_deg':10,'fraction_at_100Hz_percent':float(angle[1]/10*100)}

def glitch():
 return {'input_rates_per_hour':{'Livingston':{'Tomte':6.44,'Fast Scattering':9.05},'Hanford':{'Tomte':.23,'Fast Scattering':.22}},'difference_per_hour':(6.44-.23)+(9.05-.22),'measure':'rates after the source selection and observing-time definition'}

def backgrounds():
 exposure=np.array([1e3,1e4,203000.]);upper=-np.log(.05)/exposure
 return {'background_years':exposure.tolist(),'louder_events':0,'poisson_95_rate_upper_per_year':upper.tolist(),'candidate_window_days':16,'poisson_95_fap_upper':(-np.expm1(-upper*16/365.25)).tolist(),'assumption':'independent Poisson background; no trials-factor correction'}

def tide():
 r=np.array([10.,11.,12.,13.,14.]);mass_kg=1.4*Ms;k2=.1;compactness=G*mass_kg/(r*1000*c*c);lam=2/3*k2*compactness**(-5)
 return {'mass_Msun':1.4,'Love_number_k2':k2,'radius_km':r.tolist(),'Lambda_dimensionless':lam.tolist(),'scope':'single-star Lambda; not the binary weighted tidal deformability'}

def plot(data):
 fig,axes=plt.subplots(1,3,figsize=(12,3.5),layout='constrained')
 a=data['mass'];axes[0].plot(a['f_Hz'],a['t_s'],'o-');axes[0].set(xlabel='Frequency [Hz]',ylabel='Time before merger [s]',title='Specified chirp points')
 a=data['timing'];axes[1].plot(a['frequency_Hz'],a['phase_error_deg'],'o-');axes[1].set(xlabel='Frequency [Hz]',ylabel='Phase error [degree]',title='10 microsecond timing offset')
 a=data['tidal_scaling'];axes[2].plot(a['radius_km'],a['Lambda_dimensionless'],'o-');axes[2].set(xlabel='Radius [km]',ylabel='Dimensionless Lambda',title='Fixed mass and Love number')
 fig.savefig(D/'physical-controls.png',dpi=160)

if __name__=='__main__':
 data={'mass':mass(),'timing':timing(),'glitches':glitch(),'background':backgrounds(),'tidal_scaling':tide()};plot(data);(D/'physical-results.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
