"""Дескрипторы для L1_2-окна: VEC, Al+Ti, Al/Ti, delta."""
import numpy as np
import pandas as pd

BASE_6 = ['Ni', 'Co', 'Fe', 'Cr', 'Al', 'Ti']
VEC_TABLE = {'Ni': 10, 'Co': 9, 'Fe': 8, 'Cr': 6, 'Al': 3, 'Ti': 4}
RADIUS_TABLE = {'Ni': 124.6, 'Co': 125.2, 'Fe': 124.1,
                'Cr': 124.9, 'Al': 143.2, 'Ti': 146.2}  # пм


def calculate_descriptors(df: pd.DataFrame, elements=BASE_6) -> pd.DataFrame:
    missing = [e for e in elements if e not in VEC_TABLE or e not in RADIUS_TABLE]
    assert not missing, f"Нет данных в таблицах для: {missing}"

    x = df[elements].to_numpy(dtype=float)
    c = x / x.sum(axis=1, keepdims=True)

    vec = c @ np.array([VEC_TABLE[e] for e in elements], dtype=float)
    r = np.array([RADIUS_TABLE[e] for e in elements], dtype=float)
    r_mean = c @ r
    delta = 100.0 * np.sqrt((c * (1.0 - r / r_mean[:, None]) ** 2).sum(axis=1))

    out = pd.DataFrame(index=df.index)
    out['Al_plus_Ti'] = df['Al'] + df['Ti']
    out['Al_to_Ti_ratio'] = df['Al'] / df['Ti'].replace(0, np.nan)
    out['VEC'] = vec
    out['delta_atomic_radius'] = delta
    return out