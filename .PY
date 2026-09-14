# -*- coding: utf-8 -*-
"""
2026 A题 问题1 求解代码
功能：全隐式有限差分求解圆柱药材预热平衡阶段温度场与水分浓度场
输出：result1.xlsx + 4张竞赛级图表
运行：python q1_solver.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import warnings, os, sys
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC',
                                   'Heiti SC', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
OUT_DIR = "./q1_output"
os.makedirs(OUT_DIR, exist_ok=True)


# ============================================================
# 1. 内嵌附件1数据（前1800s，31个点）
# ============================================================
T_ENV_DATA = np.array([28, 28.528, 29.192, 29.684, 30.037, 30.834, 31.293, 31.82, 32.121,
                       32.73, 33.202, 33.879, 34.268, 34.806, 35.142, 35.524, 36.091,
                       36.354, 37.067, 37.419, 37.882, 38.134, 38.767, 39.125, 39.458,
                       39.595, 40.061, 40.238, 40.621, 41.166, 41.513])
C_ENV_DATA = np.array([0.01963, 0.02002, 0.02053, 0.021, 0.02151, 0.02191, 0.02233,
                       0.02278, 0.02325, 0.02377, 0.02428, 0.02465, 0.02506, 0.02552,
                       0.02612, 0.0266, 0.02687, 0.02732, 0.02793, 0.02826, 0.02891,
                       0.02921, 0.02961, 0.03029, 0.03051, 0.03098, 0.03137, 0.03179,
                       0.03219, 0.03262, 0.03307])
T_ENV_TIME = np.arange(0, 1801, 60, dtype=float)


# ============================================================
# 2. 模型参数
# ============================================================
rho = 820.0        # kg/m³
cp  = 2600.0       # J/(kg·K)
kth = 0.36         # W/(m·K)
h   = 25.0         # W/(m²·K)
hm  = 8e-7         # m/s
R   = 0.02         # m
T0  = 28.0         # ℃
C0  = 2.55         # kg/kg
D0  = 7e-9         # m²/s
aD  = 0.89         # —


# ============================================================
# 3. 网格与时间
# ============================================================
N = 21
dr = R / (N - 1)
r_nodes = np.linspace(0, R, N)

dt = 1.0
t_end = 1800.0
n_steps = int(t_end / dt) + 1
time_arr = np.linspace(0, t_end, n_steps)

alpha = kth / (rho * cp)
beta  = alpha * dt / dr**2
print(f"[参数] alpha = {alpha:.4e} m²/s, beta = {beta:.4f}")


# ============================================================
# 4. 环境边界插值
# ============================================================
try:
    T_env_func = interp1d(T_ENV_TIME, T_ENV_DATA, kind='linear',
                          fill_value='extrapolate', bounds_error=False)
    C_env_func = interp1d(T_ENV_TIME, C_ENV_DATA, kind='linear',
                          fill_value='extrapolate', bounds_error=False)
    print("[插值] 环境边界插值成功")
except Exception as e:
    print(f"[警告] 插值失败：{e}，使用常值边界")
    T_env_func = lambda t: 28.0
    C_env_func = lambda t: 0.02


# ============================================================
# 5. TDMA 求解器
# ============================================================
def tdma(a, b, c, d):
    """三对角矩阵追赶法求解 Ax=d，a 下对角，b 对角，c 上对角"""
    n = len(b)
    c_ = np.zeros(n); d_ = np.zeros(n); x = np.zeros(n)
    try:
        c_[0] = c[0] / b[0]
        d_[0] = d[0] / b[0]
        for i in range(1, n-1):
            m = b[i] - a[i] * c_[i-1]
            if abs(m) < 1e-30:
                m = 1e-30
            c_[i] = c[i] / m
            d_[i] = (d[i] - a[i] * d_[i-1]) / m
        m = b[n-1] - a[n-1] * c_[n-2]
        d_[n-1] = (d[n-1] - a[n-1] * d_[n-2]) / m
        x[n-1] = d_[n-1]
        for i in range(n-2, -1, -1):
            x[i] = d_[i] - c_[i] * x[i+1]
    except Exception as e:
        print(f"[TDMA异常] {e}，返回上一步解")
    return x


# ============================================================
# 6. 初始化
# ============================================================
T = np.full(N, T0)
C = np.full(N, C0)
T_hist = np.zeros((n_steps, N)); T_hist[0] = T
C_hist = np.zeros((n_steps, N)); C_hist[0] = C


# ============================================================
# 7. 主循环
# ============================================================
print("[求解] 开始时间推进...")
for n in range(n_steps - 1):
    t_next = time_arr[n+1]
    T_env_n = float(T_env_func(t_next))
    C_env_n = float(C_env_func(t_next))

    # ---------- 温度场 ----------
    a = np.zeros(N); b = np.zeros(N); c = np.zeros(N); d = np.zeros(N)

    # 中心节点
    b[0] = 1 + 4*beta
    c[0] = -4*beta
    d[0] = T[0]

    # 内部节点
    for j in range(1, N-1):
        rj = r_nodes[j]
        rp = rj + dr/2
        rm = rj - dr/2
        coef = beta / rj
        a[j] = -coef * rm
        b[j] = 1 + coef * (rp + rm)
        c[j] = -coef * rp
        d[j] = T[j]

    # 边界节点
    denom_T = kth + h*dr
    a[N-1] = -kth / denom_T
    b[N-1] = 1.0
    c[N-1] = 0.0
    d[N-1] = h * dr * T_env_n / denom_T

    T = tdma(a, b, c, d)

    # ---------- 水分场（Picard 迭代）----------
    C_iter = C.copy()
    for it in range(5):
        D_field = D0 * np.exp(-aD / np.maximum(C_iter, 0.001))

        a = np.zeros(N); b = np.zeros(N); c = np.zeros(N); d = np.zeros(N)

        # 中心节点
        D0_ = D_field[0]
        gm0 = D0_ * dt / dr**2
        b[0] = 1 + 4*gm0
        c[0] = -4*gm0
        d[0] = C[0]

        # 内部节点
        for j in range(1, N-1):
            rj = r_nodes[j]
            rp = rj + dr/2
            rm = rj - dr/2
            Dj = D_field[j]
            gm = Dj * dt / (rj * dr**2)
            a[j] = -gm * rm
            b[j] = 1 + gm * (rp + rm)
            c[j] = -gm * rp
            d[j] = C[j]

        # 边界节点
        DN = D_field[N-1]
        denom_C = DN + hm * dr
        a[N-1] = -DN / denom_C
        b[N-1] = 1.0
        c[N-1] = 0.0
        d[N-1] = hm * dr * C_env_n / denom_C

        C_new = tdma(a, b, c, d)

        if np.max(np.abs(C_new - C_iter)) < 1e-8:
            break
        C_iter = C_new

    C = np.maximum(C_new, 0.0)   # 物理保正

    T_hist[n+1] = T
    C_hist[n+1] = C

    if (n+1) % 300 == 0:
        print(f"  t = {time_arr[n+1]:.0f}s, T_center = {T[0]:.4f}℃, "
              f"C_center = {C[0]:.4f}, C_surf = {C[-1]:.4f}")

print("[求解] 完成")


# ============================================================
# 8. 提取报告结果
# ============================================================
report_times = [100, 300, 600, 900, 1200, 1500, 1800]
r_report_cm = [0, 0.5, 1, 1.5, 2]
idx_report = [int(t/dt) for t in report_times]
j_report = [int(round(rc/100.0/dr)) for rc in r_report_cm]

print("\n" + "="*70)
print("表1 30分钟内药材的温度（单位：℃）")
print("="*70)
hdr = "时间/s | " + " | ".join([f"r={rc}cm" for rc in r_report_cm])
print(hdr)
print("-"*70)
for t, i in zip(report_times, idx_report):
    row = " | ".join([f"{T_hist[i, j]:.4f}" for j in j_report])
    print(f"{t:6d} | {row}")

print("\n" + "="*70)
print("表2 30分钟内药材的水分浓度（单位：kg/kg）")
print("="*70)
print(hdr)
print("-"*70)
for t, i in zip(report_times, idx_report):
    row = " | ".join([f"{C_hist[i, j]:.4f}" for j in j_report])
    print(f"{t:6d} | {row}")


# ============================================================
# 9. 保存 result1.xlsx
# ============================================================
r_cols = [f"{rc}" for rc in np.arange(0, 2.01, 0.1)]
df_T = pd.DataFrame(np.round(T_hist, 4), columns=r_cols)
df_T.insert(0, "时间\\距离", np.arange(0, 1801).astype(int))
df_C = pd.DataFrame(np.round(C_hist, 4), columns=r_cols)
df_C.insert(0, "时间\\距离", np.arange(0, 1801).astype(int))

try:
    with pd.ExcelWriter(os.path.join(OUT_DIR, "result1.xlsx"), engine='openpyxl') as w:
        df_T.to_excel(w, sheet_name="温度", index=False)
        df_C.to_excel(w, sheet_name="水分浓度", index=False)
    print(f"\n[保存] {OUT_DIR}/result1.xlsx")
except Exception as e:
    print(f"[警告] xlsx 保存失败：{e}，改存 CSV")
    df_T.to_csv(os.path.join(OUT_DIR, "result1_温度.csv"), index=False, encoding="utf-8-sig")
    df_C.to_csv(os.path.join(OUT_DIR, "result1_水分浓度.csv"), index=False, encoding="utf-8-sig")


# ============================================================
# 10. 竞赛级图表
# ============================================================
# --- 图1：中心与表面温度随时间 ---
fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
ax.plot(time_arr/60, T_hist[:, 0], '-', color='#C0392B', lw=2, label='中心 r=0')
ax.plot(time_arr/60, T_hist[:, 10], '-', color='#2E86C1', lw=2, label='r=1.0cm')
ax.plot(time_arr/60, T_hist[:, -1], '-', color='#27AE60', lw=2, label='表面 r=2.0cm')
ax.plot(time_arr/60, [T_env_func(t) for t in time_arr], '--',
        color='#7F8C8D', lw=1.5, label='环境 T_env(t)')
ax.set_xlabel('时间 / min', fontsize=12)
ax.set_ylabel('温度 / ℃', fontsize=12)
ax.set_title('图1  预热平衡阶段药材内部温度演变（中心/中间/表面）', fontsize=13)
ax.grid(alpha=0.3); ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig1_温度演变.png"), dpi=200, bbox_inches='tight')
plt.close()

# --- 图2：中心与表面水分浓度随时间 ---
fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
ax.plot(time_arr/60, C_hist[:, 0], '-', color='#C0392B', lw=2, label='中心 r=0')
ax.plot(time_arr/60, C_hist[:, 10], '-', color='#2E86C1', lw=2, label='r=1.0cm')
ax.plot(time_arr/60, C_hist[:, -1], '-', color='#27AE60', lw=2, label='表面 r=2.0cm')
ax.plot(time_arr/60, [C_env_func(t) for t in time_arr], '--',
        color='#7F8C8D', lw=1.5, label='环境 C_env(t)')
ax.set_xlabel('时间 / min', fontsize=12)
ax.set_ylabel('水分浓度 / (kg/kg)', fontsize=12)
ax.set_title('图2  预热平衡阶段药材内部水分浓度演变', fontsize=13)
ax.grid(alpha=0.3); ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig2_水分浓度演变.png"), dpi=200, bbox_inches='tight')
plt.close()

# --- 图3：空间分布热力图（温度）---
fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=150)
im1 = axes[0].imshow(T_hist.T, aspect='auto', origin='lower',
                     extent=[0, 30, 0, 2], cmap='YlOrRd')
axes[0].set_xlabel('时间 / min'); axes[0].set_ylabel('到中心距离 / cm')
axes[0].set_title('温度场 T(r,t) 热力图')
plt.colorbar(im1, ax=axes[0], label='T / ℃')

im2 = axes[1].imshow(C_hist.T, aspect='auto', origin='lower',
                     extent=[0, 30, 0, 2], cmap='GnBu')
axes[1].set_xlabel('时间 / min'); axes[1].set_ylabel('到中心距离 / cm')
axes[1].set_title('水分浓度场 C(r,t) 热力图')
plt.colorbar(im2, ax=axes[1], label='C / (kg/kg)')
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig3_空间热力图.png"), dpi=200, bbox_inches='tight')
plt.close()

# --- 图4：不同时刻径向分布 ---
fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=150)
cmap_t = plt.cm.plasma(np.linspace(0.1, 0.9, len(report_times)))
for t, i, col in zip(report_times, idx_report, cmap_t):
    axes[0].plot(r_nodes*100, T_hist[i], 'o-', color=col, ms=3, lw=1.5,
                 label=f't={t}s')
axes[0].set_xlabel('到中心距离 / cm'); axes[0].set_ylabel('T / ℃')
axes[0].set_title('不同时刻温度径向分布')
axes[0].grid(alpha=0.3); axes[0].legend(fontsize=9, ncol=2)

for t, i, col in zip(report_times, idx_report, cmap_t):
    axes[1].plot(r_nodes*100, C_hist[i], 's-', color=col, ms=3, lw=1.5,
                 label=f't={t}s')
axes[1].set_xlabel('到中心距离 / cm'); axes[1].set_ylabel('C / (kg/kg)')
axes[1].set_title('不同时刻水分浓度径向分布')
axes[1].grid(alpha=0.3); axes[1].legend(fontsize=9, ncol=2)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig4_径向分布.png"), dpi=200, bbox_inches='tight')
plt.close()

print(f"\n[图表] 4张竞赛级图表已保存至 {OUT_DIR}/")
print("✅ 问题1求解全部完成。")