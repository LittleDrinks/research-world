#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
q049: 地球-太阳孤立圆轨道的引力波辐射功率与Peters并合时间（限定计算脚本）
物理模型（本脚本实际采用的假设）：
  - 二体、孤立、准圆轨道（e=0），牛顿引力势 + 四极引力波辐射
  - 辐射反作用采用Peters & Mathews / Peters (1964) 形式
单位：SI（国际单位制），距离AU仅作换算
来源常数：CODATA/nasa标准值，脚本内直接给出，不依赖外部库
运行：python3 q049_gw_calc.py | tee stdout.txt
"""
import math, json, datetime, sys

# ---------- 输入常数（SI）----------
G    = 6.67430e-11      # m^3 kg^-1 s^-2
c    = 2.99792458e8     # m/s
M_sun   = 1.98847e30    # kg
M_earth = 5.9722e24     # kg
AU     = 1.495978707e11 # m
YEAR   = 3.15576e7      # s (Julian year)
M_sun_MS_lifetime_yr = 5.0e9  # 太阳主序剩余寿命（文献常用值，作者报告级假设）

a = AU                      # 轨道半长轴（圆轨道半径）
m1, m2 = M_sun, M_earth
M  = m1 + m2                # 总质量
mu = m1*m2/(m1+m2)          # 折合质量

# ---------- 计算 1：圆轨道引力波功率 ----------
# P = (32/5) G^4 mu^2 M^3 / (c^5 a^5)   [Peters 1964, e=0]
P_gw = (32.0/5.0) * G**4 * mu**2 * M**3 / (c**5 * a**5)

# 轨道机械能 E = -G m1 m2 / (2a)，能量耗散时标
E_orb = -G*m1*m2/(2*a)
t_energy = abs(E_orb)/P_gw

# ---------- 计算 2：Peters并合时间（e=0 解析式）----------
# t_merge = 5 c^5 a^4 / (256 G^3 mu M^2) = a^4/(4*beta), beta=(64/5)G^3 mu M^2/c^5
beta = (64.0/5.0) * G**3 * mu * M**2 / c**5
t_merge = a**4 / (4.0*beta)

# da/dt（辐射阻尼导致的收缩率）
da_dt = -beta / a**3

# ---------- 汇总输出 ----------
out = {
  "timestamp_utc": datetime.datetime.utcnow().isoformat()+"Z",
  "inputs": {
    "G": G, "c": c, "M_sun_kg": M_sun, "M_earth_kg": M_earth,
    "a_m": a, "a_AU": 1.0, "eccentricity": 0.0,
    "units": "SI (m, kg, s, W)"
  },
  "results": {
    "P_gw_W": P_gw,
    "E_orb_J": E_orb,
    "t_energy_s": t_energy,
    "t_energy_yr": t_energy/YEAR,
    "t_merge_s": t_merge,
    "t_merge_yr": t_merge/YEAR,
    "da_dt_m_per_s": da_dt,
    "da_dt_AU_per_yr": da_dt*YEAR/AU
  },
  "comparisons": {
    "sun_MS_remaining_life_yr": M_sun_MS_lifetime_yr,
    "ratio_t_merge_over_sun_life": (t_merge/YEAR)/M_sun_MS_lifetime_yr,
    "note": "GW并合时间比太阳主序剩余寿命长约1e13量级"
  }
}
print("=== q049 地球-太阳孤立圆轨道 GW 计算（本脚本实际运行输出）===")
print(json.dumps(out, indent=2, ensure_ascii=False))
print("\n关键数值（核对用）:")
print(f"  P_gw        = {P_gw:.4g} W        （文献量级 ~200 W，一致）")
print(f"  t_merge     = {t_merge:.4g} s = {t_merge/YEAR:.4g} yr")
print(f"  t_energy    = {t_energy/YEAR:.4g} yr")
print(f"  da/dt       = {da_dt:.4g} m/s = {da_dt*YEAR/AU:.4g} AU/yr")
print(f"  t_merge/太阳剩余主序寿命 ≈ {out['comparisons']['ratio_t_merge_over_sun_life']:.3g}")

# ================== 极小诊断示例 ==================
# 规则：诊断输入是显式标记的fixture，不是任何真实论文的内容
def diagnose_fulltext(source):
    """缺全文情形：只能得到书目级元数据 -> 输出 warning + need-info"""
    if source.get("access") != "fulltext":
        return {
            "fixture": source.get("id"),
            "status": "warning",
            "label": "need-info",
            "message": "缺少全文，仅能核验书目元数据；无法核验文内公式、常数或数据。",
            "action": "获取全文后重新提取，不得以摘要代替全文。"
        }
    return {"status": "ok"}

def compare_models(modelA, modelB):
    """两个不同假设模型比较：假设不同 -> 暂不可比较 + need-grill，不得输出科学反驳"""
    differing = [k for k in set(modelA["assumptions"])|set(modelB["assumptions"])
                 if modelA["assumptions"].get(k) != modelB["assumptions"].get(k)]
    if differing:
        return {
            "models": [modelA["id"], modelB["id"]],
            "status": "not-comparable-yet",
            "label": "need-grill",
            "differing_assumptions": differing,
            "message": "两模型在假设层面不一致，结果差异不能解释为矛盾或科学反驳。",
            "action": "先对齐假设（或做同假设重算），再比较数值。"
        }
    return {"status": "comparable"}

# ---- fixture（明确标记，非真实论文数据）----
fixtures = {
  "fixture_meta_only": {"id": "FIXTURE-META-ONLY-2024", "access": "abstract-only"},
  "modelA": {"id": "FIXTURE-MODEL-A",
             "assumptions": {"system": "isolated-two-body", "eccentricity": 0.0}},
  "modelB": {"id": "FIXTURE-MODEL-B",
             "assumptions": {"system": "solar-system-nbody", "eccentricity": 0.0167}},
}
print("\n=== 诊断示例（输入为显式标记的fixture，非真实论文提取结果）===")
print(json.dumps(diagnose_fulltext(fixtures["fixture_meta_only"]), indent=2, ensure_ascii=False))
print(json.dumps(compare_models(fixtures["modelA"], fixtures["modelB"]), indent=2, ensure_ascii=False))
assert diagnose_fulltext(fixtures["fixture_meta_only"])["label"] == "need-info"
assert compare_models(fixtures["modelA"], fixtures["modelB"])["label"] == "need-grill"
assert "not-comparable" in compare_models(fixtures["modelA"], fixtures["modelB"])["status"]
print("\n诊断断言全部通过（缺全文->need-info；假设不同->need-grill，无科学反驳输出）。")
