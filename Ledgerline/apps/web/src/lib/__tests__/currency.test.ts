import { describe, expect, it } from 'vitest';
import { formatCurrency, getCurrencySymbol, supportedCurrencies } from '../currency';

describe('formatCurrency', () => {
  it('formats USD with dollar symbol', () => {
    expect(formatCurrency(1234.5)).toBe('$1234.50');
    expect(formatCurrency(1234.5, 'USD')).toBe('$1234.50');
  });

  it('formats CNY with yen symbol', () => {
    expect(formatCurrency(88, 'CNY')).toBe('¥88.00');
  });
});

describe('getCurrencySymbol', () => {
  it('returns symbol for supported currencies', () => {
    expect(getCurrencySymbol('USD')).toBe('$');
    expect(getCurrencySymbol('CNY')).toBe('¥');
  });

  it('falls back to dollar for unknown currency', () => {
    expect(getCurrencySymbol('EUR' as never)).toBe('$');
  });
});

describe('supportedCurrencies', () => {
  it('includes USD and CNY', () => {
    expect(supportedCurrencies).toEqual(['USD', 'CNY']);
  });
});
