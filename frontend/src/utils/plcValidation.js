/**
 * Robust validation and normalization utility for PLC identifiers.
 * Prevents creation of invalid cards (null, undefined, empty, NaN, or corrupted strings).
 */

export const isValidPlcId = (id) => {
  if (id === null || id === undefined) return false;
  if (typeof id === 'number') {
    return !isNaN(id) && isFinite(id) && id > 0;
  }
  const s = String(id).trim();
  if (!s) return false;
  
  const upper = s.toUpperCase();
  if (
    upper === 'NAN' ||
    upper === 'UNDEFINED' ||
    upper === 'NULL' ||
    upper === 'NONE' ||
    upper === 'PLC_NAN' ||
    upper === 'PLC NAN' ||
    upper === 'PLC_NULL' ||
    upper === 'PLC_UNDEFINED' ||
    upper.includes('NAN')
  ) {
    return false;
  }

  // Matches PLC_01..PLC_99, PLC1..PLC99, PLC 01..PLC 99
  const match = s.match(/^PLC[_\s-]?0*([1-9]\d*)$/i);
  if (match) {
    const num = parseInt(match[1], 10);
    return !isNaN(num) && num > 0;
  }

  // Matches numeric digits only '1'..'99'
  if (/^\d+$/.test(s)) {
    const num = parseInt(s, 10);
    return !isNaN(num) && num > 0;
  }

  return false;
};

export const formatPlcDisplay = (pId) => {
  if (!isValidPlcId(pId)) return 'PLC_01';
  const s = String(pId).trim();
  const match = s.match(/^PLC[_\s-]?0*([1-9]\d*)$/i);
  if (match) {
    const num = parseInt(match[1], 10);
    return `PLC_${String(num).padStart(2, '0')}`;
  }
  if (/^\d+$/.test(s)) {
    const num = parseInt(s, 10);
    return `PLC_${String(num).padStart(2, '0')}`;
  }
  return 'PLC_01';
};

export const getPlcNumber = (pId) => {
  if (!isValidPlcId(pId)) return 1;
  const s = String(pId).trim();
  const match = s.match(/^PLC[_\s-]?0*([1-9]\d*)$/i);
  if (match) {
    const num = parseInt(match[1], 10);
    return !isNaN(num) && num > 0 ? num : 1;
  }
  if (/^\d+$/.test(s)) {
    const num = parseInt(s, 10);
    return !isNaN(num) && num > 0 ? num : 1;
  }
  return 1;
};

export const isPlcMatch = (a, b) => {
  if (!isValidPlcId(a) || !isValidPlcId(b)) return false;
  return formatPlcDisplay(a) === formatPlcDisplay(b);
};
