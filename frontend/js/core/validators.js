// 基础校验
export const v = {
  positive(n) { return typeof n === "number" && n > 0; },
  nonEmpty(s) { return typeof s === "string" && s.trim().length > 0; },
};
