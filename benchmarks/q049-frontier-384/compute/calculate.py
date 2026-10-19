#!/usr/bin/env python3
"""Earth-Sun circular, isolated, constant point masses; Python stdlib only.
Run: python /workspace/frontier/compute/calculate.py
Generated result files stay beside this script. Capture stdout with tee stdout.txt.
No orbit integration, N-body simulation, network access, or fitted observations.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
G = 6.67430e-11                 # m^3 kg^-1 s^-2, NIST/CODATA 2022
G_STD = 0.00015e-11
C = 299792458.0                # m/s, adopted exact SI defining value
AU = 149597870700.0            # m, exact; IAU 2015 B3 endnote 4 quotes IAU 2012
GM_S = 1.3271244e20            # m^3/s^2, exact nominal conversion factor, IAU B3
GM_E = 3.986004e14             # m^3/s^2, exact nominal conversion factor, IAU B3
YEAR = 365.25 * 86400.0        # s, Julian-year unit convention
m1, m2 = GM_S/G, GM_E/G       # kg, model masses, not independent mass measurements
M = m1+m2
mu = m1*m2/M
a = AU                         # relative separation, not Sun-barycentre radius
omega = math.sqrt(G*M/a**3)
energy = -G*m1*m2/(2*a)
power = (32/5)*G**4*m1**2*m2**2*M/(C**5*a**5)
K = (64/5)*G**3*m1*m2*M/C**5 # da/dt = -K/a^3, K in m^4/s
adot = -K/a**3
formal_t = a**4/(4*K)
peters_t = 5*C**5*a**4/(256*G**3*m1*m2*M)
# For r=a(cos phi,sin phi,0), Qij=mu(ri*rj-delta_ij*a^2/3).
# Qxxx'''=4 mu a^2 omega^3 sin(2phi), Qyy'''=-Qxx''',
# Qxy'''=Qyx'''=-4 mu a^2 omega^3 cos(2phi); all other components vanish.
# ('Qxxx' above denotes Q_xx, third time derivative, not a rank-3 tensor.)
q3_amp = 4*mu*a*a*omega**3
contractions = []
for i in range(4096):
    phase = 2*math.pi*i/4096
    qxx = q3_amp*math.sin(2*phase)
    qxy = -q3_amp*math.cos(2*phase)
    contractions.append(qxx*qxx+(-qxx)**2+2*qxy*qxy)
power_tensor = G/(5*C**5)*math.fsum(contractions)/len(contractions)
# Independent algebraic parameterization in terms of nominal GM values.
power_gm = (32/5)*GM_S**2*GM_E**2*(GM_S+GM_E)/(G*C**5*a**5)
time_gm = 5*C**5*a**4/(256*GM_S*GM_E*(GM_S+GM_E))
# Simpson quadrature of dt = a0^4/K * x^3 dx, x in [0,1].
# This is a one-dimensional integral check, NOT a long-time orbit simulation.
n = 1024
s = math.fsum((1 if i in (0,n) else 4 if i % 2 else 2)*(i/n)**3 for i in range(n+1))
time_integral = a**4/K*s/(3*n)
checks = {
    'quadrupole_tensor_vs_mass_formula': math.isclose(power_tensor,power,rel_tol=2e-14),
    'GM_vs_mass_power': math.isclose(power_gm,power,rel_tol=2e-14),
    'GM_vs_mass_time': math.isclose(time_gm,peters_t,rel_tol=2e-14),
    'time_integral_vs_Peters_circular': math.isclose(time_integral,peters_t,rel_tol=2e-14),
    'energy_balance': math.isclose(G*m1*m2/(2*a*a)*adot,-power,rel_tol=2e-14),
    'local_timescale_is_four_times_formal_time': math.isclose(abs(energy)/power,4*peters_t,rel_tol=2e-14),
}
assert all(checks.values()), checks
print('MODEL: isolated circular constant-mass point-particle binary; leading quadrupole, adiabatic energy balance')
print('INPUTS (nominal GM values are exact conversion factors, not exact physical measurements):')
for key,val,unit in [('G',G,'m^3 kg^-1 s^-2'),('G_standard_uncertainty',G_STD,'m^3 kg^-1 s^-2'),('c',C,'m s^-1'),('a_relative',a,'m'),('GM_Sun_nominal',GM_S,'m^3 s^-2'),('GM_Earth_nominal',GM_E,'m^3 s^-2'),('Julian_year',YEAR,'s')]:
    print(f'{key} = {val:.12e} {unit}')
print('RESULTS (extra printed digits are arithmetic reproducibility, not physical accuracy):')
for key,val,unit in [
    ('m_Sun_model',m1,'kg'),('m_Earth_model',m2,'kg'),('reduced_mass',mu,'kg'),
    ('orbital_angular_frequency',omega,'rad s^-1'),('orbital_period',2*math.pi/omega/YEAR,'Julian yr'),
    ('relative_speed_over_c',omega*a/C,'dimensionless'),('GM_total_over_a_c_squared',G*M/(a*C*C),'dimensionless'),
    ('binding_energy',energy,'J'),('GW_power_mass_formula',power,'W'),('GW_power_tensor_contraction',power_tensor,'W'),
    ('GW_power_GM_formula',power_gm,'W'),('initial_da_dt',adot,'m s^-1'),('initial_da_per_Julian_year',adot*YEAR,'m yr^-1'),
    ('formal_Peters_time',peters_t,'s'),('formal_Peters_time_years',peters_t/YEAR,'Julian yr'),
    ('formal_time_quadrature',time_integral,'s'),('local_energy_over_power',abs(energy)/power,'s'),
    ('local_a_over_abs_adot',a/abs(adot),'s'),('local_timescale_years',a/abs(adot)/YEAR,'Julian yr'),
    ('fractional_energy_loss_per_orbit',power*(2*math.pi/omega)/abs(energy),'dimensionless')]:
    print(f'{key} = {val:.12e} {unit}')
for key,passed in checks.items():
    print(f'CHECK {key}: {"PASS" if passed else "FAIL"}')
print('CHECKS are internal arithmetic/model consistency only, not observational validation or independent verification of GR.')
print('Fixed nominal GM inputs imply P proportional to 1/G and formal t independent of G; do not propagate derived kg masses as independent inputs.')
print('No primary Peters full text was accessed. No real-system fate or detection claim is made.')

sources = [
 {'URL':'https://physics.nist.gov/cgi-bin/cuu/Value?bg','实际访问范围':'本轮成功下载并读取常数页面正文，2022 CODATA G=6.67430(15)e-11 SI；原件 sources/nist_G.html。'},
 {'URL':'https://arxiv.org/pdf/1510.07674','实际访问范围':'本轮成功下载 IAU 2015 B3 决议6页PDF并读取全部提取文本；第3页标称GM，第6页注4引用au定义。原件 sources/iau2015_nominal.pdf；不是Peters论文。'},
 {'URL':'https://www.iau.org/static/resolutions/IAU2015_English.pdf','实际访问范围':'本轮请求返回404，未读到正文；用上述arXiv决议副本替代。'},
 {'URL':'https://www.iau.org/static/resolutions/IAU2012_English.pdf','实际访问范围':'本轮请求返回404，未读到正文；au定义仅从已读IAU 2015决议注4核实。'},
 {'URL':'https://articles.adsabs.harvard.edu/pdf/1964PhRv..136.1224P','实际访问范围':'本轮请求403，Peters 1964（Phys. Rev. 136, B1224）全文未核验；不声称逐式对照原文。'},
 {'URL':'https://en.wikipedia.org/wiki/Gravitational_wave','实际访问范围':'本轮请求超时，未获取正文、不作证据。六次外部访问已用完；详细日志 sources/access_log.json。'}
]
report = {
 'title':'q049子任务：地球—太阳圆轨道四极矩功率与Peters形式时间的独立复算',
 'summary':f'本轮以1 au相对间距、IAU标称日地GM及CODATA G复算：四极矩功率{power:.3g} W，圆轨道Peters形式并合时间{peters_t/YEAR:.3g}年。张量收缩、能量平衡与一维积分内部一致；脚本和实际stdout已保存，未做N体模拟。功率是初始能流，时间是固定点质量模型积分至零间距的外推，不是实测衰变或真实太阳系结局。Peters原文未获取，不能声称全文核验。',
 'findings':[
  {'claim':f'模型初始引力波总功率为{power:.6g} W（约196 W），非零但极小。',
   'basis':'【本轮执行】calculate.py以Qij=μ(ri rj−δij a²/3)，P=G〈Qij三阶时间导数的逐项平方和〉/(5c⁵)，4096相位收缩得到32Gμ²a⁴ω⁶/(5c⁵)，与32G⁴m₁²m₂²(m₁+m₂)/(5c⁵a⁵)一致。ω²=G(m₁+m₂)/a³。G、GM、a的来源正文已读取；原始stdout保留额外算术位数。',
   'limitations':'【模型】孤立、圆轨道、无自旋点质量、固定质量、弱场慢速、领先四极矩及绝热反作用。此值是远区总能量/时间，不是某地点的W/m²，也不是直接观测。两种表达共享同一理论，内部一致不等于独立验证GR。'},
  {'claim':f'形式并合时间为{peters_t:.6g} s，即{peters_t/YEAR:.6g}儒略年；局部衰减时标却为其4倍。',
   'basis':f'【本轮推导及执行】E=−Gm₁m₂/(2a)，dE/dt=−P导出da/dt=−K/a³，K=64G³m₁m₂(m₁+m₂)/(5c⁵)。积分a₀→0得t=a₀⁴/(4K)=5c⁵a₀⁴/[256G³m₁m₂(m₁+m₂)]。Simpson积分核对通过；|E₀|/P₀=a₀/|da/dt₀|=4t。初始da/dt={adot:.6g} m/s，即{adot*YEAR:.6g} m/年。',
   'limitations':'【未核验】称为Peters圆轨道形式，但原文403，未逐式核对作者文本。积分至零是数学终点；真实太阳有限半径、潮汐及末端强场均破坏假设。不能把初始P保持不变积分，也不能把|E|/P误叫总并合时间。'},
  {'claim':'可比较的必须是相同轨道定义、输入约定、近似阶数与同一物理量。',
   'basis':'【已读来源】IAU B3将GM太阳=1.3271244e20、GM地球=3.986004e14 m³/s²定义为精确标称换算因子，不是精确真值；a=149597870700 m。NIST G=6.67430(15)e−11 m³ kg⁻¹ s⁻²，m=GM/G。c=299792458 m/s作为SI定义值采用，1儒略年=31557600 s为单位约定。【推断】固定这些GM时P∝1/G，而t中的G完全抵消；由GM/G导出的kg质量不能作为互相独立输入重复传播误差。',
   'limitations':'本轮未另访问SI定义原文；不提供真实历元星历参数、偏心率误差预算。a是相对轨道半长轴/圆轨道中心间距，不是太阳或地球各自绕质心的半径；非圆轨道需平均功率和耦合的a、e演化，不能直接套用本圆轨道时间。'},
  {'claim':'P>0只说明此耗散近似有轨道能量流出，不能推出真实太阳系会在上述时间并合或其稳定性结局。',
   'basis':f'【本轮执行】初始v/c={omega*a/C:.3g}、GM/(ac²)={G*M/(a*C*C):.3g}，支持当前弱场慢速近似；每轨道GW能量损失占|E|约{power*(2*math.pi/omega)/abs(energy):.3g}。【模型推断】纯牛顿孤立双体守恒且无辐射；加入领先GR耗散后才有极小内旋。多体之间可交换轨道能量与角动量；恒星失质量、半径演化和潮汐会改变模型，慢速各向同性失质量甚至可使轨道膨胀。',
   'limitations':'不把牛顿无耗散与GR有耗散当作同假设的矛盾。无N体模拟、无恒星演化或潮汐参数拟合；未核验太阳演化文献，不给吞没时间、逃逸概率、混沌稳定性或最终命运的定量预测。'}
 ],
 'warnings':[
  {'label':'need-info','reason':'Peters 1964原文获取失败；6次外部检索/下载额度耗尽。','next_action':'后续取得可访问的作者原文并核对功率、圆轨道da/dt及时间公式的定义；当前仅声称自主推导和算术复算。'},
  {'label':'need-grill','reason':'把196 W、|E|/P与1.07e23年混为同一种量，或声称由此预测地球真实结局，会跨越量纲与模型边界。','next_action':'逐项注明瞬时总辐射功率、局部时标、积分终点和外推期间维持的假设；真实系统需另列失质量、潮汐、多体与有限半径效应。'},
  {'label':'need-info','reason':'标称常数不是带历元的实际地日参数；本计算也不是极小衰变的检测。','next_action':'若需与星历或测量比较，先指定历元、GM时间尺度约定、相对半长轴和偏心率，并分离非GW效应与观测不确定度。'}
 ],
 'questions':[
  {'title':'比较对象究竟是当前功率、局部衰减时标，还是理想点质量的积分终点？','why':'三者定义、单位和物理意义不同；局部时标与圆轨道形式时间恰差4倍。'},
  {'title':'真实太阳系中哪些过程会先使固定质量孤立圆轨道前提失效？','why':'本任务只复算GW通道；恒星演化、多体相互作用和潮汐需要各自输入与证据，不能由非零GW功率代替。'}
 ],
 'proposed_changes':[
  {'before':'行星轨道完全不衰变／有引力波就能预测地球最终撞太阳。','after':'牛顿孤立双体轨道守恒；领先GR四极矩模型给出极小内旋，但不单独确定真实太阳系命运。','reason':'避免混合不同假设，把有限近似的数学结果误当现实预言。','evidence':'本轮功率、能量平衡、da/dt复算；真实命运未计算。'},
  {'before':'地日的并合时间就是当前束缚能除以辐射功率。','after':'圆轨道模型的局部|E|/P=a/|da/dt|=4t；形式t须随a变化积分，并标注点质量外推。','reason':'功率随a⁻⁵增大，不能假设全程固定为初值。','evidence':'calculate.py的能量平衡和一维积分检查；stdout.txt实际输出。'},
  {'before':'采用精确地球质量和太阳质量即可给出高精度真实并合时间。','after':'明确使用标称GM及选定G推导模型kg质量；报约196 W、1.07e23年，不暗示真实系统预测精度。','reason':'标称精确性是换算约定，不是天体真值精确性；物理模型限制远大于打印位数。','evidence':'已读IAU 2015 B3第2—3页关于标称换算因子的明确说明及NIST G页面。'}
 ],
 'sources':sources
}
(ROOT/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md = f'''# {report['title']}

{report['summary']}

## 模型与输入

相对圆轨道间距 a₀=1 au；两点质量固定，忽略其他天体、有限半径、潮汐、失质量。
采用领先四极矩辐射、牛顿圆轨道能量与绝热能量平衡。不是纯牛顿无耗散模型，也不做长期N体模拟。

|输入|采用值|单位与证据|
|---|---|---|
|G|6.67430(15) × 10⁻¹¹|m³ kg⁻¹ s⁻²；已读取NIST CODATA 2022页面|
|GM太阳|1.3271244 × 10²⁰|m³ s⁻²；IAU 2015 B3第3页，精确标称换算因子|
|GM地球|3.986004 × 10¹⁴|m³ s⁻²；同上，不含月球质量|
|a₀|149597870700|m；精确au定义，经已读IAU B3注4核实|
|c|299792458|m s⁻¹；采用SI定义值，本轮未另访问SI原文|
|1年|31557600|s；儒略年单位约定|
|模型太阳质量|{m1:.12e}|kg；GM太阳/G，不是独立质量观测|
|模型地球质量|{m2:.12e}|kg；GM地球/G，不是独立质量观测|

## 公式、量纲及结果

- 总质量 M=m₁+m₂，约化质量 μ=m₁m₂/M，ω²=GM/a³。
- Qᵢⱼ=μ(rᵢrⱼ−δᵢⱼa²/3)。P=G〈Σᵢⱼ(Qᵢⱼ的三阶时间导数)²〉/(5c⁵)。
- 圆轨道张量收缩为32μ²a⁴ω⁶；P=32G⁴m₁²m₂²M/(5c⁵a⁵)={power:.9g} W。量纲 kg m² s⁻³；这是初始总能流，不是能量或局地通量。
- E=−Gm₁m₂/(2a)={energy:.9g} J；dE/dt=−P。
- da/dt=−64G³m₁m₂M/(5c⁵a³)={adot:.9g} m/s={adot*YEAR:.9g} m/儒略年。
- t₍formal₎=5c⁵a₀⁴/(256G³m₁m₂M)={peters_t:.9g} s={peters_t/YEAR:.9g} 儒略年，积分终点为点质量间距零。
- 初始局部时标 |E₀|/P₀=a₀/|da/dt₀|={a/abs(adot)/YEAR:.9g} 年=4t₍formal₎。
- 当前v/c={omega*a/C:.6g}、GM/(ac²)={G*M/(a*C*C):.6g}；每轨道GW能量损失占比{power*(2*math.pi/omega)/abs(energy):.6g}。

这是对标准圆轨道Peters形式的独立推导及执行，不是声称逐页验证Peters原文。
P∝a⁻⁵，内旋加快；不能把当前P当常量推算总时间。t的秒量纲来自积分，不可直接与W比较大小。
固定标称GM时，P=(32/5)(GM₁)²(GM₂)²(GM₁+GM₂)/(G c⁵a⁵)，t=5c⁵a⁴/[256(GM₁)(GM₂)(GM₁+GM₂)]。
因此G不确定度对P有影响而在该参数约定的t中抵消；不能把导出的kg质量再当独立测量传播误差。

## 实际执行与可复现性

```bash
cd /workspace/frontier/compute
python calculate.py | tee stdout.txt
```

仅Python标准库。4096个相位的解析三阶导数收缩与质量公式比较；1024分段Simpson求积检查∫₀¹x³dx；再检查GM表达式、能量平衡和4倍时标关系。没有长时间轨道或N体积分。这些测试共享理论，只验证实现的一致性，不验证GR或真实地球轨道衰减。实际输出在 `stdout.txt`；脚本 `calculate.py`；来源原件和访问日志在 `sources/`。输出的更多位数仅为复现算术。

## 主要发现与边界

'''
for i,f in enumerate(report['findings'],1):
    md += f"### {i}. {f['claim']}\n\n{f['basis']}\n\n**限制：**{f['limitations']}\n\n"
md += '''## 可比与不可比条件

|可直接比较的条件|不可直接比较的情形|
|---|---|
|相同a₀（两体相对距离）、GM约定、G及单位|各自绕质心半径与相对距离混用；年、秒混用|
|同为圆轨道、领先四极矩的总平均功率|W与W/m²、功率与时间、总引力波功率与太阳电磁光度混同|
|同为固定质量、孤立点质量、积分a₀→0的形式时间|真实偏心多体、有限半径碰撞/吞没、恒星演化终点的时间|
|同为初始局部a/|da/dt|或|E|/P|把局部时标当积分总时间；后者在本模型中小4倍|
|纯牛顿对纯牛顿，或包含相同辐射项的模型相互对照|牛顿无辐射与GR有辐射当作同一模型的矛盾|

真实太阳有有限半径，且质量与半径会演化；潮汐、失质量与多体交换改变轨道。慢速各向同性失质量可导致外扩，但这里不量化该效应。弱场近似也不能延伸到零间距；形式积分大部分时间发生在大a处，不等于真实系统会维持假设至该时间。本轮没有太阳演化文献核验、吞没年代预测或多体长期稳定性结论。

## 待核实与建议

'''
for w in report['warnings']:
    md += f"- **{w['label']}**：{w['reason']} 下一步：{w['next_action']}\n"
for q in report['questions']:
    md += f"- **问题：{q['title']}** {q['why']}\n"
for change in report['proposed_changes']:
    md += f"- 将“{change['before']}”改为“{change['after']}”。理由：{change['reason']} 证据：{change['evidence']}\n"
md += '\n## 来源与本轮实际访问范围\n\n'
for s in sources:
    md += f"- {s['URL']} — {s['实际访问范围']}\n"
md += '\n**证据分层：**数值和检查是本轮执行；标称常数说明是已读决议的发布方陈述；能量平衡、适用边界及比较关系是本模型推导；Peters全文、真实系统演化时间及轨道衰变检测均未核验。未把下载失败当作全文通过。\n'
(ROOT/'result.md').write_text(md,encoding='utf-8')
# Validate the requested report shape and string-only scalar fields.
assert len(report['summary']) <= 300
assert len(report['findings']) <= 4 and len(report['warnings']) <= 4
assert len(report['questions']) <= 3 and len(report['proposed_changes']) <= 3
assert set(report) == {'title','summary','findings','warnings','questions','proposed_changes','sources'}
def check_strings(obj):
    if isinstance(obj,dict):
        for value in obj.values(): check_strings(value)
    elif isinstance(obj,list):
        for value in obj: check_strings(value)
    else: assert isinstance(obj,str), type(obj)
check_strings(report)
print('REPORT_SCHEMA: PASS (required keys, array limits, string scalar fields, summary <=300 Chinese characters)')
print('WROTE result.json and result.md')
