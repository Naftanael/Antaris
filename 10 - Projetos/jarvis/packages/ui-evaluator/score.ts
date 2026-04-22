import type { RubricScores } from "./rubric.js";

export function averageScore(scores: RubricScores): number {
  const values = Object.values(scores);
  return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2));
}
