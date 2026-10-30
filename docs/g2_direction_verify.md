# 原则二方向性修复验证（不对称度前因 → 向下解绑后果）

种子团: 1502，asym 前因 = e_std > 中位数 0.6960

## 前因 = down_std（拆出的窄岗不对称度更低）
  h=1: P(down_std|asym高)=0.2736(n=742), P(down_std|asym低)=0.1750(n=760), 提升比=1.56, p=4.56e-06
  h=2: P(down_std|asym高)=0.2022(n=742), P(down_std|asym低)=0.1447(n=760), 提升比=1.40, p=0.00327
  h=3: P(down_std|asym高)=0.1685(n=742), P(down_std|asym低)=0.1303(n=760), 提升比=1.29, p=0.0377

## 前因 = down_e（拆出的窄岗平均E更低，例程下沉）
  h=1: P(down_e|asym高)=0.0687(n=742), P(down_e|asym低)=0.2737(n=760), 提升比=0.25, p=7.56e-26
  h=2: P(down_e|asym高)=0.0418(n=742), P(down_e|asym低)=0.2250(n=760), 提升比=0.19, p=2.34e-25
  h=3: P(down_e|asym高)=0.0377(n=742), P(down_e|asym低)=0.1961(n=760), 提升比=0.19, p=1.83e-21

## 前因 = split（原判据，对照）
  h=1: P(split|asym高)=0.2857(n=742), P(split|asym低)=0.3697(n=760), 提升比=0.77, p=0.000526
  h=2: P(split|asym高)=0.2102(n=742), P(split|asym低)=0.2855(n=760), 提升比=0.74, p=0.000735
  h=3: P(split|asym高)=0.1725(n=742), P(split|asym低)=0.2566(n=760), 提升比=0.67, p=7.34e-05

## 交叉：LLM holds × asym_high → split
  h=1 holds=1 asym_high=1: n=159, split率=0.1698, down_std率=0.1572
  h=1 holds=1 asym_high=0: n=250, split率=0.2400, down_std率=0.1040
  h=1 holds=0 asym_high=1: n=583, split率=0.3173, down_std率=0.3053
  h=1 holds=0 asym_high=0: n=510, split率=0.4333, down_std率=0.2098

  h=2 holds=1 asym_high=1: n=159, split率=0.1069, down_std率=0.1069
  h=2 holds=1 asym_high=0: n=250, split率=0.1920, down_std率=0.0960
  h=2 holds=0 asym_high=1: n=583, split率=0.2384, down_std率=0.2281
  h=2 holds=0 asym_high=0: n=510, split率=0.3314, down_std率=0.1686

  h=3 holds=1 asym_high=1: n=159, split率=0.0755, down_std率=0.0755
  h=3 holds=1 asym_high=0: n=250, split率=0.1520, down_std率=0.0720
  h=3 holds=0 asym_high=1: n=583, split率=0.1990, down_std率=0.1938
  h=3 holds=0 asym_high=0: n=510, split率=0.3078, down_std率=0.1588

## 卡方（asym_high × down_std）
  h=1: chi2=21.01, p=4.56e-06  (2x2: 203,539,133,627)
  h=2: chi2=8.65, p=0.00327  (2x2: 150,592,110,650)
  h=3: chi2=4.32, p=0.0377  (2x2: 125,617,99,661)

## 组合前因：holds=1 ∧ hier_n>=3 ∧ asym_high → down_std
  h=1: P=0.7333(n=15) vs 0.2186(n=1487), 提升比=3.36, p=1.93e-06
  h=2: P=0.4667(n=15) vs 0.1701(n=1487), 提升比=2.74, p=0.00253
  h=3: P=0.4000(n=15) vs 0.1466(n=1487), 提升比=2.73, p=0.00612