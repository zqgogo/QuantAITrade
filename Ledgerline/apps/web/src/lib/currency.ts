export type Currency = 'USD' | 'CNY';

export const currencySymbols: Record<Currency, string> = {
  USD: '$',
  CNY: '¥',
};

export const currencyNames: Record<Currency, string> = {
  USD: 'US Dollar',
  CNY: 'Chinese Yuan',
};

export const supportedCurrencies: Currency[] = ['USD', 'CNY'];

export function formatCurrency(amount: number, currency: Currency = 'USD'): string {
  const symbol = currencySymbols[currency];
  if (currency === 'CNY') {
    return `${symbol}${amount.toFixed(2)}`;
  }
  return `${symbol}${amount.toFixed(2)}`;
}

export function getCurrencySymbol(currency: Currency): string {
  return currencySymbols[currency] || '$';
}