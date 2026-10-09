// Error function approximation for Normal CDF
function erf(x: number): number {
  // Abramowitz and Stegun formula 7.1.26
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;

  const sign = x < 0 ? -1 : 1;
  const absX = Math.abs(x);
  const t = 1.0 / (1.0 + p * absX);
  const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-absX * absX);
  return sign * y;
}

export function normalCdf(x: number, mean: number, std: number): number {
  if (std <= 0) return x >= mean ? 1 : 0;
  return 0.5 * (1 + erf((x - mean) / (std * Math.SQRT2)));
}

export function normalPdf(x: number, mean: number, std: number): number {
  if (std <= 0) return 0;
  const exponent = -0.5 * Math.pow((x - mean) / std, 2);
  return (1 / (std * Math.sqrt(2 * Math.PI))) * Math.exp(exponent);
}

export function mean(arr: number[]): number {
  if (arr.length === 0) return 0;
  return arr.reduce((acc, v) => acc + v, 0) / arr.length;
}

export function median(arr: number[]): number {
  if (arr.length === 0) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

export function standardDeviation(arr: number[], m?: number): number {
  if (arr.length <= 1) return 0;
  const avg = m ?? mean(arr);
  const variance = arr.reduce((acc, v) => acc + Math.pow(v - avg, 2), 0) / (arr.length - 1);
  return Math.sqrt(variance);
}

export function percentile(arr: number[], p: number): number {
  if (arr.length === 0) return 0;
  if (arr.length === 1) return arr[0];
  const sorted = [...arr].sort((a, b) => a - b);
  const index = (p / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index - lower;
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

export function medianAbsoluteDeviation(arr: number[]): number {
  if (arr.length === 0) return 0;
  const med = median(arr);
  const absDiffs = arr.map(v => Math.abs(v - med));
  return median(absDiffs);
}

export function skewness(arr: number[]): number {
  const n = arr.length;
  if (n < 3) return 0;
  const m = mean(arr);
  const s = standardDeviation(arr, m);
  if (s === 0) return 0;
  const sum3 = arr.reduce((acc, v) => acc + Math.pow(v - m, 3), 0);
  return (n / ((n - 1) * (n - 2))) * (sum3 / Math.pow(s, 3));
}

export function kurtosis(arr: number[]): number {
  const n = arr.length;
  if (n < 4) return 0;
  const m = mean(arr);
  const s = standardDeviation(arr, m);
  if (s === 0) return 0;
  const sum4 = arr.reduce((acc, v) => acc + Math.pow(v - m, 4), 0);
  const term1 = (n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3));
  const term2 = (3 * Math.pow(n - 1, 2)) / ((n - 2) * (n - 3));
  return term1 * (sum4 / Math.pow(s, 4)) - term2;
}

export function giniIndex(arr: number[]): number {
  const absVals = arr.map(v => Math.abs(v)).filter(v => v > 0);
  const n = absVals.length;
  if (n <= 1) return 0;
  absVals.sort((a, b) => a - b);
  const totalSum = absVals.reduce((acc, v) => acc + v, 0);
  if (totalSum === 0) return 0;
  let cumSum = 0;
  for (let i = 0; i < n; i++) {
    cumSum += (i + 1) * absVals[i];
  }
  return (2 * cumSum) / (n * totalSum) - (n + 1) / n;
}

export function shannonEntropy(categories: string[]): number {
  if (categories.length === 0) return 0;
  const counts: Record<string, number> = {};
  for (const c of categories) {
    counts[c] = (counts[c] || 0) + 1;
  }
  const total = categories.length;
  let entropy = 0;
  for (const key in counts) {
    const p = counts[key] / total;
    if (p > 0) {
      entropy -= p * Math.log2(p);
    }
  }
  return entropy;
}

export function linearRegression(x: number[], y: number[]) {
  const n = x.length;
  if (n < 2) return { slope: 0, intercept: y[0] || 0 };
  const mx = mean(x);
  const my = mean(y);
  let num = 0;
  let den = 0;
  for (let i = 0; i < n; i++) {
    num += (x[i] - mx) * (y[i] - my);
    den += (x[i] - mx) * (x[i] - mx);
  }
  const slope = den === 0 ? 0 : num / den;
  const intercept = my - slope * mx;
  return { slope, intercept };
}

export interface AdvancedRegressionResult {
  slope: number;
  intercept: number;
  r: number;
  rSquared: number;
  stdError: number;
  fStatistic: number;
  equation: string;
  residuals: number[];
  durbinWatson: number;
  trendDescription: string;
  isStatisticallySignificant: boolean;
}

export function advancedLinearRegression(x: number[], y: number[]): AdvancedRegressionResult {
  const n = x.length;
  if (n < 2) {
    return {
      slope: 0,
      intercept: y[0] || 0,
      r: 0,
      rSquared: 0,
      stdError: 0,
      fStatistic: 0,
      equation: `Y = ${((y[0] || 0)).toFixed(2)}`,
      residuals: [0],
      durbinWatson: 2,
      trendDescription: 'Dados insuficientes para regressão linear',
      isStatisticallySignificant: false
    };
  }

  const { slope, intercept } = linearRegression(x, y);
  const my = mean(y);

  let ssTot = 0;
  let ssRes = 0;
  const residuals: number[] = [];

  for (let i = 0; i < n; i++) {
    const yHat = intercept + slope * x[i];
    const res = y[i] - yHat;
    residuals.push(res);
    ssRes += res * res;
    ssTot += Math.pow(y[i] - my, 2);
  }

  const rSquared = ssTot > 0 ? Math.max(0, Math.min(1, 1 - ssRes / ssTot)) : 0;
  const r = (slope >= 0 ? 1 : -1) * Math.sqrt(rSquared);

  const df = n - 2;
  const stdError = df > 0 ? Math.sqrt(ssRes / df) : 0;
  const fStatistic = df > 0 && 1 - rSquared > 0 ? (rSquared / 1) / ((1 - rSquared) / df) : 0;

  // Durbin-Watson statistic
  let dwNum = 0;
  let dwDen = ssRes;
  for (let i = 1; i < n; i++) {
    dwNum += Math.pow(residuals[i] - residuals[i - 1], 2);
  }
  const durbinWatson = dwDen > 0 ? dwNum / dwDen : 2;

  let trendDescription = '';
  if (Math.abs(slope) < 0.05 * (my || 1)) {
    trendDescription = 'Tendência Estável / Horizontal (Variação residual baixa)';
  } else if (slope > 0) {
    trendDescription = `Tendência de Alta (+R$ ${slope.toFixed(2)}/período)`;
  } else {
    trendDescription = `Tendência de Queda (-R$ ${Math.abs(slope).toFixed(2)}/período)`;
  }

  const sign = intercept >= 0 ? '+' : '-';
  const equation = `Y = ${slope.toFixed(2)}·X ${sign} ${Math.abs(intercept).toFixed(2)}`;

  return {
    slope,
    intercept,
    r,
    rSquared,
    stdError,
    fStatistic,
    equation,
    residuals,
    durbinWatson,
    trendDescription,
    isStatisticallySignificant: rSquared >= 0.35 && n >= 4
  };
}
