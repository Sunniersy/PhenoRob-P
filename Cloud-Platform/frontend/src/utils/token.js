/**
 * 解析 JWT payload 中的 exp 字段（Unix 秒）
 * @param {string} token
 * @returns {number|null}
 */
export function parseJwtExp(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch {
    return null;
  }
}

/**
 * 判断 token 是否已过期（提前 30 秒视为过期，避免与服务端时钟偏差）
 * @param {string} token
 * @returns {boolean}
 */
export function isTokenExpired(token) {
  const exp = parseJwtExp(token);
  if (exp === null) return false;
  return Date.now() >= (exp - 30) * 1000;
}
